# Code Review Report: M2 Hardening & CommandBatchDTO

## 1. 🔍 Summary
`CommandBatchDTO`를 `simulation.dtos.api`로 이전하여 시뮬레이션의 모든 상태 변경(P2P 송금, 시스템 Mint/Burn, God/System 커맨드)을 단일 진입점으로 통합했습니다. 또한, DTO 레벨에서 엄격한 정수(Integer) 검증을 도입하여 Float Incursion을 방지하고 `MonetaryLedger.execute_batch`를 통해 안전하게 배치 작업을 수행하도록 구현되었습니다.

## 2. 🚨 Critical Issues
*발견된 심각한 보안 위반, 하드코딩, 또는 Zero-Sum 위반 사항이 없습니다.*

## 3. ⚠️ Logic & Spec Gaps
* **Dependency Purity (Duck Typing vs Injection)**: 
  `MonetaryLedger._resolve_agent` 메서드 내부에서 Agent를 찾기 위해 `self.settlement_system`이나 `self.time_provider`의 내부 속성(`agent_registry`, `agents`, `get_agent`)을 `hasattr`로 추측하여(Duck Typing) 접근하고 있습니다. 
  이는 런타임에는 동작할 수 있으나 객체 지향의 명시적 의존성 주입(Explicit Injection) 원칙과 프로토콜 순수성을 해칩니다. `time_provider`는 시간을 제공하는 목적이므로, Agent를 찾는 책임을 부여하는 것은 역할 분리에 어긋납니다.

## 4. 💡 Suggestions
* **Strict Type Checking for Integers**: 
  `FinancialTransferDTO`와 `SystemLedgerMutationDTO`의 `__post_init__`에서 `isinstance(self.amount_pennies, int)`를 사용해 정수 여부를 검사하고 있습니다. 파이썬에서 `bool`은 `int`의 하위 클래스이므로 `isinstance(True, int)`는 `True`를 반환합니다. `amount_pennies`에 불리언 값이 들어올 가능성을 원천 차단하려면 `type(self.amount_pennies) is int`를 사용하는 것이 더 엄격한 방어책입니다.
* **Explicit `IAgentRegistry` Injection**:
  `MonetaryLedger`가 생성될 때 명시적으로 `IAgentRegistry`를 주입(Inject)받도록 리팩토링하는 것을 권장합니다. 이를 통해 `_resolve_agent`의 불안정한 `hasattr` Fallback 체인을 제거할 수 있습니다.

## 5. 🧠 Implementation Insight Evaluation

* **Original Insight**:
> ### 1. Unified Command Pipeline via `CommandBatchDTO`
> The `CommandBatchDTO` has been successfully refactored to serve as the unified container for all simulation inputs and side-effects for a given tick.
> -   **Old Architecture**: Fragmented inputs (`god_commands` vs `system_commands`) and weakly-typed side-effects (`effects_queue: List[Dict]`).
> -   **New Architecture**: `CommandBatchDTO` encapsulates:
>     -   `transfers`: Typed `FinancialTransferDTO` list.
>     -   `mutations`: Typed `SystemLedgerMutationDTO` list.
>     -   `god_commands`: List of external overrides.
>     -   `system_commands`: List of policy adjustments.
> -   **Benefit**: This enforces a single entry point for state mutation, making the simulation deterministic and replayable.
> 
> ### 2. Strict Integer Enforcement (Float Incursion Defense)
> To resolve `TD-FIN-FLOAT-INCURSION`, the new DTOs (`FinancialTransferDTO`, `SystemLedgerMutationDTO`) utilize `__post_init__` validation to raise `TypeError` immediately if a float is passed.
> 
> ### 3. Protocol Segregation & Monetary Authority
> A critical insight during implementation was the separation between `ISettlementSystem` (Standard P2P transfers) and `IMonetaryAuthority` (Mint/Burn capabilities).

* **Reviewer Evaluation**: 
  작성된 인사이트는 시스템의 진화 방향을 정확히 짚어냈습니다. 특히 `ISettlementSystem`과 `IMonetaryAuthority`의 프로토콜 분리(Protocol Segregation) 인지 및 `isinstance`를 통한 안전한 다운캐스팅 접근은 훌륭한 교훈입니다. `CommandBatchDTO`를 통한 상태 변경의 단일화(Deterministic Execution) 역시 아키텍처 관점에서 매우 중요한 마일스톤입니다. 단, Agent 조회를 위한 Fallback 로직이 임시방편(Technical Debt)이라는 점을 인사이트에 추가로 남기면 더 완벽했을 것입니다.

## 6. 📚 Manual Update Proposal (Draft)

* **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
* **Draft Content**:
```markdown
### [RESOLVED] TD-FIN-FLOAT-INCURSION: Float Type Incursion in Ledger
- **Symptom**: Floating-point values bypassing ledger boundaries, causing "dust" and non-determinism during financial operations.
- **Resolution**: Deprecated loosely-typed `effects_queue` and implemented `CommandBatchDTO` with `FinancialTransferDTO` and `SystemLedgerMutationDTO`. Enforced strict integer (`int`) type checks within the `__post_init__` of DTOs.
- **Related PR**: IMPL-M2-HARDENING

### [NEW] TD-SYS-IMPLICIT-REGISTRY-LOOKUP: Duck-Typed Agent Resolution in Ledger
- **Symptom**: `MonetaryLedger._resolve_agent` utilizes `hasattr` chains to find `agent_registry` from `settlement_system` or `time_provider`.
- **Impact**: Weak dependency coupling. Overloads `time_provider` with unintended domain responsibilities.
- **Action Required**: Explicitly inject `IAgentRegistry` into `MonetaryLedger` and remove the fallback chain logic.
```

## 7. ✅ Verdict
**APPROVE**