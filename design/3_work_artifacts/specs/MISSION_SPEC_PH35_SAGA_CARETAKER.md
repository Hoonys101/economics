# Phase 35: Saga Caretaker Specification

## 1. `api.py` (Draft)
```python
# modules/finance/saga/api.py
from __future__ import annotations
from typing import List, Protocol, runtime_checkable, Dict, Any
from dataclasses import dataclass
from uuid import UUID

from modules.system.api import AgentID, IAgentRegistry
from modules.finance.api import SagaStateDTO

@dataclass(frozen=True)
class OrphanedSagaDTO:
    """DTO representing a saga identified for purging due to dead participants."""
    saga_id: UUID
    dead_participant_ids: List[AgentID]
    state: str
    last_updated_tick: int

@runtime_checkable
class ISagaRepository(Protocol):
    """Provides read-only access to saga states. Separates data fetching from execution."""
    def get_all_active_sagas(self) -> List[SagaStateDTO]:
        """Returns a list of all currently active (non-terminal) sagas."""
        ...

@runtime_checkable
class ISagaOrchestrator(Protocol):
    """Executes state transitions and commands for sagas. Owns the mutation rights."""
    def compensate_and_fail_saga(self, saga_id: UUID, reason: str) -> None:
        """
        Forces a saga into a COMPENSATING or FAILED state, triggering 
        necessary rollback logic (e.g., releasing property contracts, returning escrow).
        """
        ...

@runtime_checkable
class ISagaCaretaker(Protocol):
    """
    Analyzes active sagas and identifies those with stale/dead agents.
    Commands the orchestrator to purge them, ensuring no direct state mutation.
    """
    def sweep_orphaned_sagas(self, current_tick: int) -> List[OrphanedSagaDTO]:
        """
        Scans all active sagas, identifies orphans via IAgentRegistry,
        and triggers orchestrator compensation. Returns a list of swept sagas for logging.
        """
        ...
```

---

## 2. `saga_caretaker_spec.md` (Draft)

### 2.1. System Architecture (High-Level)
The `SagaCaretaker` resolves **TD-ARCH-ORPHAN-SAGA** by acting as a garbage collector for the Saga Orchestration system. It observes active transactions via `ISagaRepository`, queries `IAgentRegistry` to verify participant vitality, and commands `ISagaOrchestrator` to execute safe compensations (e.g., releasing `IRealEstateRegistry` locks). It strictly avoids direct mutations to `WorldState` or `SimulationState` (resolving **TD-ARCH-GOD-DTO** risks).

### 2.2. Logic Steps (Pseudo-code)

**`SagaCaretaker.sweep_orphaned_sagas` Logic:**
```text
INPUT: current_tick (int)
OUTPUT: List[OrphanedSagaDTO]

1. Initialize `purged_sagas = []`
2. Fetch `active_sagas` = ISagaRepository.get_all_active_sagas()
3. FOREACH `saga` IN `active_sagas`:
    a. IF `saga.state` is already 'FAILED' or 'COMPLETED', CONTINUE.
    b. Extract `participant_ids` from `saga.payload` (e.g., buyer_id, seller_id).
    c. `dead_agents = []`
    d. FOREACH `agent_id` IN `participant_ids`:
        i. IF NOT IAgentRegistry.is_agent_active(agent_id):
            APPEND `agent_id` TO `dead_agents`
    e. IF `dead_agents` IS NOT EMPTY:
        i. TRY:
            - ISagaOrchestrator.compensate_and_fail_saga(
                  saga_id=saga.saga_id, 
                  reason=f"Participant(s) Dead: {dead_agents}"
              )
            - Create `OrphanedSagaDTO` and APPEND to `purged_sagas`
        ii. CATCH `ZeroSumViolationError` or generic Exception:
            - Log ERROR "Failed to compensate orphaned saga {saga.saga_id} safely."
            - Continue to the next saga (Do not crash the loop).
4. RETURN `purged_sagas`
```

### 2.3. Exception Handling
- **Missing Payload Keys**: If `saga.payload` does not contain identifiable `participant_ids` keys, log a warning and skip the saga.
- **Rollback Failures**: If `compensate_and_fail_saga` raises an exception (e.g., failing to unlock a property), the Caretaker must catch it, log an error to `diagnostic_output`, and proceed. Killing the entire tick loop for one stubborn saga is forbidden.

### 2.4. 🚨 [Conceptual Debt] (정합성 부채)
- **Saga Payload Schema Homogeneity**: Currently, `SagaStateDTO.payload` is a `dict[str, Any]`. The Caretaker assumes it can reliably extract participant IDs. If different sagas (Housing vs. Bond) use different keys (`buyer_id`, `seller_id` vs `issuer_id`, `investor_id`), the Caretaker needs a resilient extraction strategy or `SagaStateDTO` needs explicit `participant_ids: List[AgentID]` metadata.
- *(Antigravity Review Required)*: Recommend updating `SagaStateDTO` definition across the codebase to mandate a uniform `participant_ids` field for O(1) caretaker lookup.

### 2.5. 검증 계획 (Testing & Verification Strategy)
- **New Test Cases**:
  1. **Happy Path**: Setup an active saga with 2 participants. Mark 1 as inactive in `IAgentRegistry`. Run sweep. Verify `compensate_and_fail_saga` is called exactly once.
  2. **Edge Case (Idempotency)**: Ensure already FAILED/COMPENSATING sagas are bypassed by the caretaker to prevent recursive rollback attempts.
  3. **Error Isolation**: Mock `compensate_and_fail_saga` to throw an exception. Verify the caretaker sweeps the next saga in the list without crashing.
- **Existing Test Impact**: Legacy tests mocking `saga_orchestrator` directly on `SimulationState` might fail if they expect the orchestrator to auto-purge. We must explicitly implement `ISagaOrchestrator` on the mocks without inventing missing attributes (`MagicMock(spec=ISagaOrchestrator)`).
- **Integration Check**: A Housing Transaction saga interrupted by sudden firm bankruptcy (seller death) must result in the `RealEstateUnit` lock (`set_under_contract`) being released.

### 2.6. Mocking 가이드
- **필수**: `tests/conftest.py`의 `golden_households`, `golden_firms` 픽스처를 우선 사용할 것.
- **사용법**: `def test_caretaker_sweep(golden_firms, mock_saga_orchestrator, mock_agent_registry):`
- **금지**: 새로운 `MagicMock()`으로 에이전트 인스턴스를 수동 생성하지 말 것. `IAgentRegistry` mock이 `is_agent_active`를 반환하도록만 설정.

### 2.7. 🚨 Risk & Impact Audit (기술적 위험 분석)
- **DTO/DAO Interface Impact**: The introduction of `ISagaRepository` requires an adapter if the current `saga_orchestrator` tightly couples state storage and execution. We must ensure the repository uses `SagaStateDTO`.
- **순환 참조 위험**: `SagaCaretaker` must NOT import `DeathSystem` or `SimulationState`. It relies entirely on `IAgentRegistry` (dependency injected) to know who is dead.
- **테스트 영향도**: `TD-TEST-MOCK-LEAK` is a risk here. Ensure that `active_sagas` lists returned in tests are properly garbage collected and do not hold circular references to the orchestrator.
- **선행 작업 권고**: (TD-ARCH-GOD-DTO) Extracting `saga_orchestrator` from `SimulationState` should be finalized, injecting it via a `IFinanceTickContext` or `ISagaContext` rather than `sim.saga_orchestrator`.

---

## 3. Mandatory Reporting Instruction
> **작업자 지시사항**: 이 명세를 기반으로 코드를 구현하거나 분석할 때 발견된 추가적인 아키텍처 결함, 정합성 오류, 혹은 통찰은 반드시 `communications/insights/MISSION-PH35-SPEC-SAGA.md` 파일에 독립적으로 기록하십시오. 공유 매뉴얼 파일(`manual.md`)에 덧붙이는 행위는 절대 금지됩니다. (보고서 누락 시 미션 Hard-Fail 처리됨)

---

```markdown
# communications/insights/MISSION-PH35-SPEC-SAGA.md

## 1. [Architectural Insights]
- **Saga Payload Fragmentation**: During the caretaker spec design, it was identified that `SagaStateDTO.payload` is an unstructured dictionary (`dict[str, Any]`). This presents a structural risk for the Caretaker, which needs to homogeneously extract participant IDs across different saga domains (Housing, Bonds, FX). *Decision*: A structural mandate is proposed to either enforce a `participant_ids` field on `SagaStateDTO` or implement a standard extraction protocol in the repository.
- **Decoupling State from Execution**: The Orchestrator historically acted as both the repository and the executor. By enforcing `ISagaRepository` and `ISagaOrchestrator` segregation, we protect the Caretaker from unintentionally triggering side-effects while querying states.

## 2. [Regression Analysis]
- *(Draft - To be filled during actual implementation phase)*
- Expected Regression: Legacy tests that check `SimulationState.saga_orchestrator.active_sagas` might fail due to the new Repository interface layer. These will be fixed by implementing `MagicMock(spec=ISagaRepository)` inside the test fixtures.

## 3. [Test Evidence]
- *(Draft - To be populated with literal `pytest` output showing 100% pass rate once implementation is complete)*
```