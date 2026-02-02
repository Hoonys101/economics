# TD-192: Transient State Synchronization Protocol

## Phenomenon
The simulation architecture relies on passing a transient `SimulationState` DTO between phases. This DTO contains mutable collections (queues like `transactions`, `effects_queue`) that are expected to be synchronized back to the persistent `WorldState` at the end of the tick. However, this synchronization was implicit (relying on shared references) or manual (in `ActionProcessor`), leading to potential data loss if references were broken or manual syncs were missed. Specifically, `Phase3_Transaction` relies on `TransactionProcessor` executing transactions, but if the transactions were drained (moved to `WorldState`) before execution, they would be skipped.

## Cause
1.  **Implicit Synchronization**: Relying on `sim_state.transactions` being the *same list object* as `world_state.transactions`. This makes it dangerous to "clear" the transient queue without clearing the history.
2.  **Scattered Responsibility**: Logic for syncing back state was found in `ActionProcessor` (legacy) and `TickOrchestrator` (partial), with no centralized authority.
3.  **Execution vs. Storage Conflict**: The "Drain" pattern moves data to storage (`WorldState`), but `TransactionProcessor` needs that data for execution. This created a conflict where drained data was invisible to the processor.

## Solution
1.  **Centralized Drain**: Implemented `_drain_and_sync_state` in `TickOrchestrator` to explicitly move transient data to `WorldState` after *every* phase.
2.  **Transient Isolation**: `SimulationState` now initializes `transactions` as a *new, empty list* for each phase/tick, enforcing the drain pattern.
3.  **Unified Execution Context**: Modified `TransactionProcessor` and `Phase3_Transaction` to explicitly reconstruct the full transaction history (Persistent Log + Current Queue) for execution, ensuring no transactions are skipped despite the drain mechanism.
4.  **Legacy Cleanup**: Removed manual sync from `ActionProcessor`, delegating all sync responsibility to the orchestrator. `ActionProcessor` is now strictly for legacy test support and isolated execution, marked with a warning to prevent use in the main loop (which would cause double-execution).

## Tests & Adjustments
- **Tests Updated**: `tests/system/test_engine.py` was updated. Specifically, `test_process_transactions_labor_trade` had an incorrect tax expectation (1.25) based on Progressive Tax logic, while the test configuration explicitly set `TAX_MODE="FLAT"` (10%). The expectation was corrected to 2.0 (10% of 20.0).
- **Factory Update**: `tests/utils/factories.py` was updated to include missing `brand_resilience_factor` in `create_firm_config_dto`.

## Lesson Learned
When introducing a "Drain" pattern (moving data from A to B), ensure that consumers of that data (Execution Systems) are updated to look at the destination (B) or a combination of both, rather than just the source (A). "Transient" means "short-lived", so once it's drained, it's gone from the transient view. Also, legacy adapters (like `ActionProcessor`) must be carefully isolated from the new flow to prevent side-effect duplication.
