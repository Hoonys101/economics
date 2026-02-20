# Mission Guide: Final Stabilization & Regression Fixes

## 1. Objectives
- Resolve the final 7 test failures remaining after the Phase 22 merges and Phase 23 hygiene adjustments.
- Ensure the `SagaOrchestrator` protocol update (`process_sagas` signature) is correctly applied across all callers and tests.
- Harden `TickOrchestrator` against mocked properties from `SimulationState` in tests.

## 2. Reference Context (MUST READ)
- **Primary Failures to Fix**:
  1. `test_lifecycle_transactions_processed_in_next_tick_strong_verify`: `AttributeError: Mock object has no attribute 'tick_withdrawal_pennies'` in `TickOrchestrator`.
  2. `test_phase29_depression.py` (`test_crisis_monitor_logging`, `test_depression_scenario_triggers`): `TypeError: SagaOrchestrator.process_sagas() takes 1 positional argument but 2 were given`.
  3. `test_orchestrator.py` (`test_process_sagas_liveness_check`, `test_process_sagas_active_participants`): `TypeError: SagaOrchestrator.process_sagas() takes 1 positional argument but 2 were given`.
  4. `test_settlement_saga_integration.py` (`test_process_sagas_integration_initiated_to_credit_check`, `test_process_sagas_integration_cancellation`): Assertion errors due to mismatch in SagaOrchestrator's internal dictionary indexing or caching issues.

## 3. Implementation Roadmap
### Phase 1: TickOrchestrator Hardening
- **Target**: `simulation/orchestration/tick_orchestrator.py`
- Modify Phase 4.1 panic index calculation to correctly handle when `tick_withdrawal_pennies` is accessed from a `MagicMock` object without the attribute. 
- Use safe `getattr(state, 'tick_withdrawal_pennies', 0)` and robust `float()` casting inside `try-except`.

### Phase 2: Call Signature Alignment
- **Target**: `tests/system/test_phase29_depression.py`, `tests/unit/sagas/test_orchestrator.py`, and `simulation/orchestration/phases/housing_saga.py`.
- **Target**: Ensure that `state.saga_orchestrator.process_sagas(state)` is updated. The new protocol is:
  ```python
  orchestrator.simulation_state = state
  orchestrator.process_sagas() # NO ARGUMENTS
  ```
- Replace all legacy `process_sagas(sim_state)` calls with the two-line property injection logic.

### Phase 3: Integration Test Assertions
- **Target**: `tests/unit/systems/test_settlement_saga_integration.py`
- Review why `assert 'saga-integration-1' in {}` is failing. Ensure `submit_saga` is correctly storing the saga with the right key and that `active_sagas` isn't being inadvertently cleared or checked incorrectly. Ensure dict-to-DTO conversion inside `process_sagas` isn't dropping the integration test payloads.

## 4. Verification
Run the following command and ensure 100% pass rate:
`pytest -rfE --tb=line --no-header tests/`
