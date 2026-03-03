# communications/insights/IMPL-PH35-STABILIZATION-SAGA.md

## 1. [Architectural Insights]
- **Saga Payload Fragmentation**: During the caretaker spec design, it was identified that `SagaStateDTO.payload` is an unstructured dictionary (`dict[str, Any]`). This presents a structural risk for the Caretaker, which needs to homogeneously extract participant IDs across different saga domains (Housing, Bonds, FX). *Decision*: A structural mandate is proposed to either enforce a `participant_ids` field on `SagaStateDTO` or implement a standard extraction protocol in the repository.
- **Decoupling State from Execution**: The Orchestrator historically acted as both the repository and the executor. By enforcing `ISagaRepository` and `ISagaOrchestrator` segregation, we protect the Caretaker from unintentionally triggering side-effects while querying states.

## 2. [Regression Analysis]
- Tests for saga orchestrator required extending the `SagaOrchestrator` to include `compensate_and_fail_saga`.
- Extended `ISagaOrchestrator` in `kernel/api.py` and implemented `compensate_and_fail_saga` in `orchestrator.py`. No legacy regressions found.

## 3. [Test Evidence]
```
tests/unit/sagas/test_orchestrator.py::test_submit_saga
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga 96c04509-dee4-417e-8045-cd5159a538ae submitted.
PASSED                                                                   [  9%]
tests/unit/sagas/test_orchestrator.py::test_process_sagas_liveness_check
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga 920eaafe-2d9b-4991-9028-19fec4217d1d submitted.
INFO     modules.finance.sagas.orchestrator:orchestrator.py:144 SAGA_CLEANUP | Saga 920eaafe-2d9b-4991-9028-19fec4217d1d cancelled due to inactive participant. Buyer Active: False, Seller Active: True
PASSED                                                                   [ 18%]
tests/unit/sagas/test_orchestrator.py::test_process_sagas_active_participants
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga 531460d6-f37c-478e-aac3-0c3d41acc646 submitted.
PASSED                                                                   [ 27%]
tests/unit/sagas/test_orchestrator.py::test_find_and_compensate_by_agent_success
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga 08372a61-62ae-4225-986e-8607aa4d1b00 submitted.
WARNING  modules.finance.sagas.orchestrator:orchestrator.py:202 SAGA_AGENT_DEATH | Triggering compensation for Saga 08372a61-62ae-4225-986e-8607aa4d1b00 due to agent 999 death.
PASSED                                                                   [ 36%]
tests/unit/sagas/test_orchestrator.py::test_find_and_compensate_by_agent_no_handler
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga 2622b7b0-7dc8-4de3-95ba-a32182069058 submitted.
ERROR    modules.finance.sagas.orchestrator:orchestrator.py:193 SAGA_COMPENSATE_FAIL | No handler provided for find_and_compensate_by_agent
PASSED                                                                   [ 45%]
tests/unit/sagas/test_saga_caretaker.py::test_happy_path_sweep
-------------------------------- live log call ---------------------------------
INFO     modules.finance.saga.caretaker:caretaker.py:84 SagaCaretaker: Purged orphaned saga 9000f9a0-b640-4382-9783-f280d9115397 due to dead agents: [2]
PASSED                                                                   [ 54%]
tests/unit/sagas/test_saga_caretaker.py::test_idempotency_ignores_already_failed_sagas PASSED [ 63%]
tests/unit/sagas/test_saga_caretaker.py::test_error_isolation
-------------------------------- live log call ---------------------------------
ERROR    modules.finance.saga.caretaker:caretaker.py:86 SagaCaretaker: Failed to compensate orphaned saga 91af24b4-2915-498b-90fd-b4bddafcdf61 safely. Error: Failed to release lock!
INFO     modules.finance.saga.caretaker:caretaker.py:84 SagaCaretaker: Purged orphaned saga ca4b606c-6900-4df6-8047-8febf7e6f704 due to dead agents: [3, 4]
PASSED                                                                   [ 72%]
tests/unit/sagas/test_saga_cleanup.py::test_saga_cleanup_inactive_buyer
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga 65ce5956-1b22-4480-a482-2098d50e6f0f submitted.
INFO     modules.finance.sagas.orchestrator:orchestrator.py:144 SAGA_CLEANUP | Saga 65ce5956-1b22-4480-a482-2098d50e6f0f cancelled due to inactive participant. Buyer Active: False, Seller Active: True
PASSED                                                                   [ 81%]
tests/unit/sagas/test_saga_cleanup.py::test_saga_cleanup_and_compensate
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga 010d8143-6f99-4969-b7a6-88c4ed434b0e submitted.
INFO     modules.finance.sagas.orchestrator:orchestrator.py:144 SAGA_CLEANUP | Saga 010d8143-6f99-4969-b7a6-88c4ed434b0e cancelled due to inactive participant. Buyer Active: True, Seller Active: False
PASSED                                                                   [ 90%]
tests/unit/sagas/test_saga_cleanup.py::test_saga_compensate_failure_resilience
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga f7c2573b-9d57-4ff3-b8de-eb22a0e9a806 submitted.
ERROR    modules.finance.sagas.orchestrator:orchestrator.py:155 SAGA_COMPENSATE_FAIL | Critical Compensation Failure
PASSED                                                                   [100%]
```
