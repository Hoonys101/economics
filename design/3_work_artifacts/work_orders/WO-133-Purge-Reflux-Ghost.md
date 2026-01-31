# Work Order: - Purge the Reflux Ghost

## 1. Context & Objective
Following the merge of "Holy Ledger" (Track A) and "Scheduler Decomposition" (Track B), the `EconomicRefluxSystem` has been deprecated and its core logic removed. However, lingering references (ghosts) in the new orchestration phases and agent classes are causing `AttributeError` during runtime because `SimulationState` and `DecisionContext` no longer carry the `reflux_system` field.

The objective is a **total purge** of `reflux_system` from the codebase, ensuring zero runtime errors and 100% adherence to the new centralized `FinanceSystem` / `SettlementSystem` architecture.

## 2. Exhaustive Search List
Perform a case-sensitive search and remove/replace matches:
- `.reflux_system` (Object attribute)
- `reflux_system` (Variable/Argument/Key)
- `EconomicRefluxSystem` (Class reference)
- `reflux` (Generic search - check for leftovers)

## 3. High-Priority Sectors
- **Orchestration**: `simulation/orchestration/phases.py`, `simulation/orchestration/tick_orchestrator.py`
- **Agents**: `simulation/firms.py`, `simulation/agents/government.py`, `simulation/bank.py`, `simulation/core_agents.py`
- **Systems**: `simulation/systems/housing_system.py`, `simulation/systems/ma_manager.py`
- **DTOs**: `simulation/dtos/api.py`

## 4. Specific Instructions
1. **Remove References**: In methods where `reflux_system` was passed as an argument (e.g., `make_decision`, `invest_infrastructure`), remove the argument from both the call site and the definition.
2. **Replace Logic**: If `reflux_system.distribute()` or similar was used for monetary tracking, ensure the logic is either handled by `SettlementSystem.transfer` or explicitly removed if it's part of the old "shadow economy" mechanics.
3. **Clean up SimulationState**: Confirm `SimulationState` in `simulation/dtos/api.py` does not have `reflux_system`.
4. **Verification**:
 - Run `python scripts/trace_leak.py` and ensure it completes without `AttributeError` and shows `delta: 0.00`.
 - Run `python scripts/verify_td_111.py` to confirm M2 reporting is accurate.
 - Run `pytest tests/test_engine.py` to ensure core engine integrity.

## 5. Success Criteria
- Codebase is 100% free of `reflux_system` references.
- `trace_leak.py` runs successfully (Tick 0 to Tick 1).
- No `AttributeError` related to missing attributes in `SimulationState`.
