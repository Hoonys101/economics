# [Structural Runtime Failure & Cleanup Analysis Report]

## Executive Summary
This report identifies the root causes of structural failures observed during simulation runtime, including agent reference leaks, missing transaction handlers, budget overruns, and type integrity violations. The system is currently in a state of partial migration between `float`-based and `int`-based monetary logic, leading to critical crashes in the M&A and Settlement modules.

## Detailed Analysis

### 1. Ghost Destination Leaks (Agent 120/124)
- **Status**: ⚠️ Partial Implementation / ❌ Logic Fragility
- **Evidence**: `runtime_audit.log:L315` and `L450`.
- **Diagnosis**: 
    - **Startup Phase**: In `firm_management.py`, the system attempts to transfer seed capital to a new Firm ID (e.g., 124) before that agent has been successfully committed to the `AgentRegistry`. The `SettlementSystem` uses `RegistryAccountAccessor`, which fails if the ID is not found.
    - **Liquidation Phase**: After a Hostile Takeover or Death, agents are removed from the active `WorldState`, but pending transactions in the `inter_tick_queue` or `effects_queue` still reference the stale IDs.
- **Notes**: This is tracked under `TD-RUNTIME-DEST-MISS`.

### 2. Missing Handler: `bond_interest`
- **Status**: ❌ Missing
- **Evidence**: `TECH_DEBT_LEDGER.md:L15` (`TD-RUNTIME-TX-HANDLER`) and `transaction_processor.py:L140-150`.
- **Diagnosis**: The `FiscalEngine` generates `bond_interest` transaction types, but these are not registered in the `TransactionProcessor`'s dispatcher. 
- **Notes**: Falling back to the "default" handler is insufficient if the default handler doesn't know how to route interest payments between the Government and Bondholders.

### 3. Government Budget Overruns (Insufficient Funds)
- **Status**: ⚠️ Partially Implemented (Missing Guardrails)
- **Evidence**: `runtime_audit.log:L120`, `L250`, `L380`.
- **Diagnosis**: 
    - The `InfrastructureManager` and `SocialSafetyNet` modules calculate expenditures based on target levels rather than current `Government.balance_pennies`.
    - `settlement_system.py:L215-230` (`_prepare_seamless_funds`) correctly identifies the shortfall but can only log an error and fail the transaction, leaving the system in an inconsistent state (e.g., Infrastructure level "Pending" but never paid).
- **Notes**: Policy execution lacks a "Pre-flight Check" against the treasury balance.

### 4. Fatal Float Crash (M&A Merger)
- **Status**: ❌ Integrity Violation
- **Evidence**: `runtime_audit.log:L510-525` (Traceback).
- **Diagnosis**: 
    - `MAManager._execute_merger` passes `offer_price` (calculated as a `float`) to `settlement_system.transfer`.
    - `settlement_system.py:L252` explicitly raises a `TypeError` if the amount is not an `int`.
- **Notes**: This is a side effect of `TD-CRIT-FLOAT-CORE`. The M&A module was not updated during the "Pennies Migration."

## Risk Assessment
- **Determinism Risk**: The mix of `float` and `int` in the `MatchingEngine` vs `SettlementSystem` will cause "Penny Leaks" where the total M2 money supply drifts over time.
- **State Corruption**: Failed transfers during agent creation (Firm Startup) leave orphaned agent objects that are "partially initialized" but unreachable.

## Conclusion
The simulation is suffering from **Lifecycle-Settlement Desync**. Transactions are being generated for agents that are either "Not Yet Live" or "Already Dead," and the monetary authority is enforcing strict integer math on modules that still operate in floating-point space.

### Action Items
1. **Integrity Guard**: Implement a `Pre-Settlement Validator` in the `TransactionProcessor` to filter transactions referencing non-existent agents.
2. **Cleanup Sync**: Ensure `DeathSystem` and `MAManager` flush the `inter_tick_queue` of any references to liquidated IDs.
3. **Budget Guard**: Add `has_budget(amount)` checks to `FiscalPolicy` execution paths.
4. **Hardening**: Force `round_to_pennies()` in `MAManager` and `StockMarket` before calling `transfer`.