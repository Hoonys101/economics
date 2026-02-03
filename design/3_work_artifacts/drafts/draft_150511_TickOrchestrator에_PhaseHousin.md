# Spec: `Phase_HousingSaga` Integration

## 1. 개요 (Overview)

본 문서는 `TickOrchestrator`의 실행 흐름에 `Phase_HousingSaga`라는 새로운 단계를 통합하는 기술 명세를 정의합니다. 이 단계의 목적은 주택 거래와 같이 여러 틱에 걸쳐 진행되는 복잡한 트랜잭션(Saga)의 상태를 전담하여 처리하는 것입니다. 이를 통해 기존 `Phase3_Transaction`에 혼재되어 있던 책임을 분리하고, 코드의 모듈성과 가독성을 향상시킵니다.

## 2. 기술적 위험 분석 및 해결 (Risk & Impact Audit Resolution)

`Pre-flight Audit Report`에서 지적된 두 가지 주요 위험(`Hidden Dependencies`, `State Dependency`)을 해결하기 위해 다음과 같이 설계합니다.

1.  **책임 재배치 (Responsibility Relocation)**: 기존 `Phase3_Transaction` 내에서 호출되던 `settlement_system.process_sagas(state)` 로직을 **완전히 새로운 `Phase_HousingSaga`로 이동**합니다. 이를 통해 Saga 처리 로직이 중복 실행되거나 충돌할 위험을 원천적으로 제거합니다.

2.  **단계 배치 및 로직 분리 (Phase Placement & Logic Segregation)**:
    *   사용자 요구사항에 따라 `Phase_HousingSaga`는 `Phase_Bankruptcy` 직후에 배치됩니다.
    *   `Pre-flight Audit Report`에서 지적했듯이, 이 시점은 시장 매칭(`Phase2_Matching`) 및 자금 결제(`Phase3_Transaction`)가 완료되기 전입니다. 따라서, 이 단계에서 실행되는 Saga 로직은 **자금 결제 여부에 의존해서는 안 됩니다.**
    *   `Phase_HousingSaga`의 책임은 **Saga의 사전 조건(pre-condition)을 검사하고 상태를 전이**하는 것으로 한정됩니다. 주요 로직은 거래 참여자(구매자, 판매자)의 생존 여부(`liveness`)를 확인하고, 참여자가 파산 등으로 비활성화되었을 경우 Saga를 `CANCELLED` 상태로 즉시 전환하는 것입니다.
    *   실제 자금 이체와 소유권 이전 같은 결제 관련 상태 전이는 기존과 같이 `TransactionProcessor`가 처리해야 하며, `Phase_HousingSaga`는 이를 유발하는 트랜잭션을 생성하지 않습니다.

## 3. 상세 설계 (Detailed Design)

### 3.1. `simulation/orchestration/tick_orchestrator.py`

`TickOrchestrator`의 페이즈 목록에 `Phase_HousingSaga`를 추가합니다.

```python
# simulation/orchestration/tick_orchestrator.py

# ... imports
from simulation.orchestration.phases import (
    Phase0_PreSequence, Phase_Production, Phase1_Decision, Phase_Bankruptcy,
    Phase_HousingSaga, # <--- 1. IMPORT NEW PHASE
    Phase_SystemicLiquidation, Phase2_Matching, Phase3_Transaction,
    Phase_Consumption, Phase5_PostSequence
)
# ...

class TickOrchestrator:
    def __init__(self, world_state: WorldState, action_processor: ActionProcessor):
        # ...
        self.phases: List[IPhaseStrategy] = [
            Phase0_PreSequence(world_state),
            Phase_Production(world_state),
            Phase1_Decision(world_state),
            Phase_Bankruptcy(world_state),           # Phase 4: Lifecycle & Bankruptcy
            Phase_HousingSaga(world_state),          # <--- 2. INSERT NEW PHASE HERE
            Phase_SystemicLiquidation(world_state),  # Phase 4.5: Systemic Liquidation
            Phase2_Matching(world_state),            # Phase 5: Matching
            Phase3_Transaction(world_state),
            Phase_Consumption(world_state),
            Phase5_PostSequence(world_state)
        ]
    # ... rest of the class
```

### 3.2. `simulation/orchestration/phases.py`

`Phase_HousingSaga` 클래스를 신규 정의하고, `Phase3_Transaction`에서 기존 Saga 처리 코드를 제거합니다.

#### 3.2.1. New `Phase_HousingSaga`

```python
# simulation/orchestration/phases.py

# ... (다른 페이즈 클래스들) ...

class Phase_HousingSaga(IPhaseStrategy):
    """
    Phase 4.1: Advance Housing Sagas (Pre-Settlement Checks)
    
    This phase processes long-running transactions (sagas), specifically for housing.
    Its primary responsibility at this point in the tick is to perform pre-condition checks
    that do not depend on market matching or financial settlement, such as agent liveness.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        """
        Checks for agent liveness and cancels sagas if participants are no longer active.
        """
        if state.settlement_system and hasattr(state.settlement_system, 'process_sagas'):
            # The core logic is delegated to the settlement system.
            # This call now handles all saga state transitions.
            state.settlement_system.process_sagas(state)
        
        return state

# ... (다른 페이즈 클래스들) ...
```

#### 3.2.2. Modified `Phase3_Transaction`

기존 `Phase3_Transaction`에서 `settlement_system.process_sagas(state)` 호출을 **제거**합니다.

```python
# simulation/orchestration/phases.py

class Phase3_Transaction(IPhaseStrategy):
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # ... (기존 로직)

        # WO-024: Monetary Transactions are now processed incrementally ...

        # REMOVED: Housing Saga Processing (Atomic V3)
        # if state.settlement_system and hasattr(state.settlement_system, 'process_sagas'):
        #     state.settlement_system.process_sagas(state) # <--- THIS LINE IS REMOVED

        # WO-116: Corporate Tax Intent Generation
        # ... (이후 로직)
```

### 3.3. `simulation/systems/settlement_system.py` (API 명세)

`SettlementSystem`의 `process_sagas` 메서드는 이제 에이전트 생존 여부 확인 로직을 포함해야 합니다.

```python
# Pseudo-code for simulation.systems.settlement_system.py

from simulation.dtos.api import SimulationState

class SettlementSystem:
    # ...

    def process_sagas(self, state: SimulationState) -> None:
        """
        Processes all active sagas, handling state transitions based on pre-conditions.
        This method is now the single point of truth for saga lifecycle management.
        """
        if not hasattr(self, 'active_sagas') or not self.active_sagas:
            return

        completed_saga_ids = []
        
        # Iterate over a copy as we might modify the list
        for saga_id, saga in list(self.active_sagas.items()):

            # 1. Agent Liveness Check (Pre-Settlement Logic)
            buyer = state.agents.get(saga.buyer_id)
            seller = state.agents.get(saga.seller_id)

            is_buyer_inactive = not buyer or not getattr(buyer, 'is_active', False)
            is_seller_inactive = not seller or not getattr(seller, 'is_active', False)

            if is_buyer_inactive or is_seller_inactive:
                saga.transition_to_cancelled("Participant inactive")
                state.logger.warning(f"SAGA_CANCELLED | Saga {saga_id} cancelled due to inactive participant.")
                # Trigger compensation logic if necessary (e.g., return escrow)
                # self._generate_cancellation_transactions(saga, state)
                completed_saga_ids.append(saga_id)
                continue

            # 2. Other state transition logic (e.g., based on time, previous steps)
            # saga.advance_state(state) ...
            
            # ... (기존 로직) ...

            if saga.is_complete():
                completed_saga_ids.append(saga_id)

        # Cleanup completed sagas
        for saga_id in completed_saga_ids:
            del self.active_sagas[saga_id]

    # ...
```

## 4. 검증 계획 (Verification Plan)

-   **Unit Test 1 (`test_phase_housing_saga.py`)**: `Phase_HousingSaga`의 `execute` 메서드가 `state.settlement_system.process_sagas`를 정확히 호출하는지 `MagicMock`으로 검증합니다.
-   **Unit Test 2 (`test_settlement_system.py`)**:
    -   `process_sagas` 메서드에 대한 테스트 케이스를 보강합니다.
    -   **Case A (Buyer Inactive)**: 구매자가 `state.agents`에 없거나 `is_active`가 `False`일 때, Saga가 `CANCELLED` 상태로 전이되는지 확인합니다.
    -   **Case B (Seller Inactive)**: 판매자가 비활성 상태일 때, Saga가 `CANCELLED` 상태로 전이되는지 확인합니다.
    -   **Case C (Both Active)**: 두 참여자 모두 활성 상태일 때, Saga가 `CANCELLED` 상태로 전이되지 않는지 확인합니다.
-   **Integration Test (`test_tick_orchestrator.py`)**:
    -   전체 틱(`run_tick`)을 실행했을 때, `Phase_HousingSaga`가 `Phase_Bankruptcy`와 `Phase_SystemicLiquidation` 사이에서 실행되는지 확인합니다.
    -   `Phase3_Transaction` 내에서 `process_sagas`가 더 이상 호출되지 않음을 확인합니다.
-   **End-to-End Test**: 주택 구매 Saga 시나리오를 실행하되, 중간에 판매자 또는 구매자가 파산하는 케이스를 실행하여 Saga가 정상적으로 취소되는지 검증합니다.
