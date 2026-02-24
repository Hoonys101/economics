# WO-WAVE-B-3-SAGA: Saga Recovery & Cleanup Insight Report

## 1. Architectural Insights

### Liveness-Aware Saga Orchestration
The `SagaOrchestrator` has been hardened to prevent "Zombie Sagas" by integrating directly with the `AgentRegistry`. Previously, the orchestrator relied on ad-hoc checks against `simulation_state.agents`, which was fragile and prone to errors if agents were removed from the state map but not fully cleaned up.

**Key Changes:**
- **Dependency Injection:** `IAgentRegistry` is now injected into `SagaOrchestrator` via the constructor. This aligns with the architectural goal of using dedicated registries for state queries rather than raw dictionary access.
- **Protocol-Based Liveness:** The orchestrator now uses `agent_registry.is_agent_active(agent_id)` to determine participant status. This abstracts the underlying implementation of "activity" (e.g., handling dead agents, bankrupt agents, or system agents).
- **Proactive Cleanup:** When an inactive participant is detected, the saga is immediately cancelled, logged with `SAGA_CLEANUP`, and removed from the active set. This prevents the system from wasting cycles on dead transactions.
- **Error Resilience:** Compensation logic is wrapped in robust error handling. If `compensate_step` fails (e.g., because the counterparty is also dead), the error is logged as `SAGA_COMPENSATE_FAIL` but the cleanup proceeds, ensuring the orchestrator remains stable.

### Technical Debt Resolution
- **TD-FIN-SAGA-REGRESSION:** The spam of `SAGA_SKIP` logs (implied by repeated processing of dead sagas) is resolved by the proactive cleanup mechanism.
- **Layering Compliance:** By injecting `AgentRegistry` in `SimulationInitializer` (Phase 1), we respect the initialization order and ensure the orchestrator has access to the necessary services without circular dependencies.

## 2. Regression Analysis

### Impact on Legacy Tests
- `tests/unit/sagas/test_orchestrator.py`: This test suite verifies the core saga submission and processing logic.
- **Regression Check:** The constructor signature change (`agent_registry` argument) is backward compatible (defaulting to `None`). Existing tests that instantiate `SagaOrchestrator` without arguments continue to pass, verifying that the fallback logic for liveness checks (using `simulation_state`) remains functional. This ensures that we haven't broken environments where the registry might not be fully wired up yet (e.g., unit tests mocking only parts of the system).

### New Verification Logic
- A new test file `tests/unit/sagas/test_saga_cleanup.py` was created to specifically target the new functionality.
- This "Chaos Test" confirms:
    1. **Cleanup:** Sagas with inactive participants are removed.
    2. **Logging:** `SAGA_CLEANUP` logs are generated with correct context.
    3. **Resilience:** `SAGA_COMPENSATE_FAIL` is handled gracefully without crashing the loop.

## 3. Test Evidence

### New Feature Verification (`tests/unit/sagas/test_saga_cleanup.py`)
```
tests/unit/sagas/test_saga_cleanup.py::test_saga_cleanup_inactive_buyer
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:61 SAGA_SUBMITTED | Saga fe13951b-ea39-46fd-9627-2ad406a677dd submitted.
INFO     modules.finance.sagas.orchestrator:orchestrator.py:142 SAGA_CLEANUP | Saga fe13951b-ea39-46fd-9627-2ad406a677dd cancelled due to inactive participant. Buyer Active: False, Seller Active: True
PASSED                                                                   [ 33%]
tests/unit/sagas/test_saga_cleanup.py::test_saga_cleanup_and_compensate
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:61 SAGA_SUBMITTED | Saga eded76f4-94f7-45f7-90cb-d4eb7f2d666d submitted.
INFO     modules.finance.sagas.orchestrator:orchestrator.py:142 SAGA_CLEANUP | Saga eded76f4-94f7-45f7-90cb-d4eb7f2d666d cancelled due to inactive participant. Buyer Active: True, Seller Active: False
PASSED                                                                   [ 66%]
tests/unit/sagas/test_saga_cleanup.py::test_saga_compensate_failure_resilience
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:61 SAGA_SUBMITTED | Saga fa604ff2-b0d6-40d4-943f-7e4767266bae submitted.
ERROR    modules.finance.sagas.orchestrator:orchestrator.py:153 SAGA_COMPENSATE_FAIL | Critical Compensation Failure
PASSED                                                                   [100%]
```

### Full Regression Suite (`tests/unit/sagas/`)
```
tests/unit/sagas/test_orchestrator.py::test_submit_saga
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:61 SAGA_SUBMITTED | Saga c10a53bc-2770-4a40-93c4-54e9857b343e submitted.
PASSED                                                                   [ 12%]
tests/unit/sagas/test_orchestrator.py::test_process_sagas_liveness_check
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:61 SAGA_SUBMITTED | Saga 9675e527-7225-4903-b099-8f7a1063b373 submitted.
INFO     modules.finance.sagas.orchestrator:orchestrator.py:142 SAGA_CLEANUP | Saga 9675e527-7225-4903-b099-8f7a1063b373 cancelled due to inactive participant. Buyer Active: False, Seller Active: True
PASSED                                                                   [ 25%]
tests/unit/sagas/test_orchestrator.py::test_process_sagas_active_participants
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:61 SAGA_SUBMITTED | Saga daf8bd6a-caa7-41e2-b4ed-8e439f5f91ac submitted.
PASSED                                                                   [ 37%]
tests/unit/sagas/test_orchestrator.py::test_find_and_compensate_by_agent_success
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:61 SAGA_SUBMITTED | Saga b0386a26-8b80-4f16-adfe-4730dd22159c submitted.
WARNING  modules.finance.sagas.orchestrator:orchestrator.py:200 SAGA_AGENT_DEATH | Triggering compensation for Saga b0386a26-8b80-4f16-adfe-4730dd22159c due to agent 999 death.
PASSED                                                                   [ 50%]
tests/unit/sagas/test_orchestrator.py::test_find_and_compensate_by_agent_no_handler
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:61 SAGA_SUBMITTED | Saga 0f024e83-0727-4d23-895a-f2512d2e43f7 submitted.
ERROR    modules.finance.sagas.orchestrator:orchestrator.py:191 SAGA_COMPENSATE_FAIL | No handler provided for find_and_compensate_by_agent
PASSED                                                                   [ 62%]
```
