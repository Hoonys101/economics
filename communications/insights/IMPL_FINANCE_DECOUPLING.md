# IMPL_FINANCE_DECOUPLING Insight Report

## Architectural Insights
1.  **SagaOrchestrator Decoupling**: Successfully removed `ISimulationState` dependency from `SagaOrchestrator` and `HousingTransactionSagaHandler`.
2.  **Explicit Dependency Injection**: Implemented `set_dependencies` in `SagaOrchestrator` to inject `SettlementSystem`, `HousingService`, `LoanMarket`, `Bank`, and `Government` explicitly. This aligns with the "DTO Purity" and "Logic Separation" mandates.
3.  **Tick Propagation**: Updated `process_sagas` to accept `current_tick` explicitly, ensuring time-awareness without god-object access.
4.  **Agent Liveness**: Replaced ad-hoc `simulation.agents.get` lookups with `IAgentRegistry` access, ensuring robust liveness checks.

## Regression Analysis
*   **Initialization Sequence**: The `SagaOrchestrator` is initialized in Phase 1 (Infrastructure) but its dependencies (Bank, HousingService) are created in Phase 2 and 3. We resolved this by adding a `set_dependencies` call at the end of Phase 3 in `SimulationInitializer`.
*   **Protocol Changes**: Updated `ISagaOrchestrator` protocol to include `process_sagas(current_tick: int)`. This required updating `Phase_HousingSaga` to pass the tick.
*   **Test Updates**: Updated unit tests to mock and inject the new dependencies instead of `SimulationState` god object.

## Test Evidence

**1. `tests/unit/sagas/test_orchestrator.py`**
```
tests/unit/sagas/test_orchestrator.py::test_submit_saga PASSED
tests/unit/sagas/test_orchestrator.py::test_process_sagas_liveness_check PASSED
tests/unit/sagas/test_orchestrator.py::test_process_sagas_active_participants PASSED
tests/unit/sagas/test_orchestrator.py::test_find_and_compensate_by_agent_success PASSED
tests/unit/sagas/test_orchestrator.py::test_find_and_compensate_by_agent_no_handler PASSED
```

**2. `tests/unit/systems/test_settlement_saga_integration.py`**
```
tests/unit/systems/test_settlement_saga_integration.py::TestSettlementSagaIntegration::test_process_sagas_integration_initiated_to_credit_check PASSED
tests/unit/systems/test_settlement_saga_integration.py::TestSettlementSagaIntegration::test_process_sagas_integration_cancellation PASSED
```

**3. `tests/forensics/test_saga_integrity.py`**
```
tests/forensics/test_saga_integrity.py::test_saga_orchestrator_rejects_incomplete_dto PASSED
```
