# WO-4.2: Orchestrator Phase Alignment

**Status**: 🟢 Ready for Implementation (PR-Chunk #3)
**Target**: `simulation/orchestration/tick_orchestrator.py`, `simulation/orchestration/phases.py`
**Goal**: Address `TD-216` by moving agent-specific lifecycle methods from the orchestrator into dedicated Phases.

## 1. Scope of Work
- Move `government.reset_tick_flow()` call.
- Move `government.process_monetary_transactions()` call.

## 2. Implementation Details

### 2.1. Phase 0 (Pre-Sequence)
- Move `state.government.reset_tick_flow()` from `TickOrchestrator.run_tick` to `Phase0_PreSequence.execute`.

### 2.2. Phase 3 (Transaction)
- Move `sim_state.government.process_monetary_transactions(sim_state.transactions)` from `TickOrchestrator._drain_and_sync_state` to the end of `Phase3_Transaction.execute`.
- Ensure it processes the union of `world_state.transactions` and current `state.transactions`.

## 3. Verification
- Monitor `M2` money supply or `CentralBank` totals during a 100-tick run to ensure no drift occurs due to the sequence change.
