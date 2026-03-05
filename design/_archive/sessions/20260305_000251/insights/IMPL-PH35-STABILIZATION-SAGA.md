# communications/insights/IMPL-PH35-STABILIZATION-SAGA.md

## 1. [Architectural Insights]
- **Saga Payload Fragmentation & Interface Illusion**: During the initial caretaker design, `SagaCaretaker` mistakenly relied on an unstructured `payload` dictionary to extract participant IDs. However, the runtime DTO `HousingTransactionSagaStateDTO` lacks a `payload` attribute entirely, which would have caused an `AttributeError` crash. This highlighted the dangers of "Mock Fantasy" - where unit tests pass purely because the mock objects possess attributes that the real production objects do not.
- **DTO Interface Unification**: To resolve the structural mismatch and ensure type safety, `SagaStateDTO` and `HousingTransactionSagaStateDTO` were unified to implement a `participant_ids` property, guaranteeing homogeneous extraction.
- **Robust Failure Handling**: The `compensate_and_fail_saga` process in the orchestrator lacked proper state management when the inner `compensate_step` threw an exception. This led to a vulnerability where failing sagas remained in `active_sagas`, causing infinite retry loops across ticks. The design was hardened to ensure failing compensations transition the saga to a terminal error state (`FAILED_ROLLED_BACK_ERROR`) and safely evict it from the queue.
- **Protocol Deduplication & Purity**: Duplicate `ISagaOrchestrator` declarations across modules were purged in favor of a Single Source of Truth (`kernel/api.py`). The orchestrator initialization also correctly receives `current_tick` from the caretaker instead of hardcoding `0`, respecting Engine Purity.

## 2. [Regression Analysis]
- Fixing the DTO extraction logically changed how `SagaCaretaker` retrieves data from its interface, but as this is a new module, it did not break any legacy tests. Legacy Orchestrator tests correctly verify `find_and_compensate_by_agent` behavior.
- The adjustments to ensure `active_sagas` are purged even on `compensate_step` exceptions successfully resolve the infinite loop concern without negatively impacting the existing state machine's regression coverage.

## 3. [Test Evidence]
```
tests/unit/sagas/test_orchestrator.py::test_submit_saga
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga 1b058a97-90f7-4a0b-93ff-4171630e6df2 submitted.
PASSED                                                                   [  9%]
tests/unit/sagas/test_orchestrator.py::test_process_sagas_liveness_check
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga d16f0f5b-b9f0-45d4-ae40-c3d5e23c7f91 submitted.
INFO     modules.finance.sagas.orchestrator:orchestrator.py:144 SAGA_CLEANUP | Saga d16f0f5b-b9f0-45d4-ae40-c3d5e23c7f91 cancelled due to inactive participant. Buyer Active: False, Seller Active: True
PASSED                                                                   [ 18%]
tests/unit/sagas/test_orchestrator.py::test_process_sagas_active_participants
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga b9b02008-0114-419b-bafe-a19000c0f91a submitted.
PASSED                                                                   [ 27%]
tests/unit/sagas/test_orchestrator.py::test_find_and_compensate_by_agent_success
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga aab4860b-810a-4fb6-a496-e17bca858349 submitted.
WARNING  modules.finance.sagas.orchestrator:orchestrator.py:202 SAGA_AGENT_DEATH | Triggering compensation for Saga aab4860b-810a-4fb6-a496-e17bca858349 due to agent 999 death.
PASSED                                                                   [ 36%]
tests/unit/sagas/test_orchestrator.py::test_find_and_compensate_by_agent_no_handler
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga e581f44a-e4cc-4ab6-871c-43fbfb5349f7 submitted.
ERROR    modules.finance.sagas.orchestrator:orchestrator.py:193 SAGA_COMPENSATE_FAIL | No handler provided for find_and_compensate_by_agent
PASSED                                                                   [ 45%]
tests/unit/sagas/test_saga_caretaker.py::test_happy_path_sweep
-------------------------------- live log call ---------------------------------
INFO     modules.finance.saga.caretaker:caretaker.py:84 SagaCaretaker: Purged orphaned saga 6b84eb43-0570-4354-9e32-a5e227092921 due to dead agents: [2]
PASSED                                                                   [ 54%]
tests/unit/sagas/test_saga_caretaker.py::test_idempotency_ignores_already_failed_sagas PASSED [ 63%]
tests/unit/sagas/test_saga_caretaker.py::test_error_isolation
-------------------------------- live log call ---------------------------------
ERROR    modules.finance.saga.caretaker:caretaker.py:86 SagaCaretaker: Failed to compensate orphaned saga b471789c-a1f7-4180-8774-fb2c58972fb2 safely. Error: Failed to release lock!
INFO     modules.finance.saga.caretaker:caretaker.py:84 SagaCaretaker: Purged orphaned saga e892f392-1c2f-48e0-bb82-6f2bb93d5673 due to dead agents: [3, 4]
PASSED                                                                   [ 72%]
tests/unit/sagas/test_saga_cleanup.py::test_saga_cleanup_inactive_buyer
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga 51b8ea16-09a8-4229-bb3f-3a9d91a9f1db submitted.
INFO     modules.finance.sagas.orchestrator:orchestrator.py:144 SAGA_CLEANUP | Saga 51b8ea16-09a8-4229-bb3f-3a9d91a9f1db cancelled due to inactive participant. Buyer Active: False, Seller Active: True
PASSED                                                                   [ 81%]
tests/unit/sagas/test_saga_cleanup.py::test_saga_cleanup_and_compensate
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga d2e99351-c052-4753-9092-23c28bda1108 submitted.
INFO     modules.finance.sagas.orchestrator:orchestrator.py:144 SAGA_CLEANUP | Saga d2e99351-c052-4753-9092-23c28bda1108 cancelled due to inactive participant. Buyer Active: True, Seller Active: False
PASSED                                                                   [ 90%]
tests/unit/sagas/test_saga_cleanup.py::test_saga_compensate_failure_resilience
-------------------------------- live log call ---------------------------------
INFO     modules.finance.sagas.orchestrator:orchestrator.py:70 SAGA_SUBMITTED | Saga da467e41-afaf-45eb-9705-eb8b2de48de2 submitted.
ERROR    modules.finance.sagas.orchestrator:orchestrator.py:155 SAGA_COMPENSATE_FAIL | Critical Compensation Failure
PASSED                                                                   [100%]
```
