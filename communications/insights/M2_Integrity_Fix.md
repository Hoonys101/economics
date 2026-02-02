# Money Leak Resolution (TD-177) & M2 Integrity (Mission M2_Integrity_Fix)

## Executive Summary
The persistent 8,000 unit money leak has been diagnosed as a synchronization issue in the Transaction Processing phase, specifically related to Housing Market loans. The `trace_leak.py` script was updated to account for untracked authorized creation, but the housing loan creation remains structurally untracked in the current tick. Additionally, synchronous bond issuance was found to lack transaction persistence, creating gaps in the audit trail.

## Phenomenon
- **Leak Magnitude**: 8,000 units per tick (variable based on housing activity).
- **Observed Behavior**: `Actual Delta` (Physical Money Supply Change) exceeds `Authorized Delta` (Government/CB tracked creation).
- **Trace Results**:
    - Infrastructure Spending: 5,000.00 (Funded by assets/transfers, not creation).
    - CB Bond Purchases: 0.00 (No authorized creation via Bonds).
    - Housing Loan: 8,000.00 (Observed in logs).

## Root Cause Analysis
The leak stems from the **Order of Operations in `Phase3_Transaction`**:

1. `Phase3` collects initial transactions (including `Bank.run_tick`).
2. `Government.process_monetary_transactions` runs on this set.
3. `TransactionProcessor.execute` runs.
4. `TransactionProcessor` delegates to `HousingTransactionHandler`.
5. `HousingTransactionHandler` calls `Bank.grant_loan`, which generates a **new** `credit_creation` transaction (value 8,000).
6. This new transaction is appended to `state.transactions` *after* step 2.
7. Consequently, `Government` never processes this new transaction in the current tick.
8. `Government.total_money_issued` is not incremented.
9. `get_monetary_delta()` reports 0 for this creation.
10. `SettlementSystem` executes the transfer immediately (Bank Reserves -> Escrow), increasing M2 by 8,000.
11. **Result**: Physical M2 increases by 8,000, but Authorized Delta does not. -> **LEAK**.

## Technical Debt & Side Findings

### 1. `Government.reset_tick_flow` is Orphaned
- **Issue**: The method `reset_tick_flow`, responsible for resetting tick-based counters (like `start_tick_money_issued`), is defined but **never called** in the codebase.
- **Impact**: `get_monetary_delta` likely returns cumulative values rather than tick-specific deltas. In single-tick traces (where start=0), this masks the issue, but in multi-tick runs, it would yield incorrect data.

### 2. Synchronous Bond Issuance Auditing
- **Issue**: `FinanceSystem.issue_treasury_bonds_synchronous` performs settlements but does not persist the resulting `Transaction` objects to `world_state.transactions` (it ignores the return value of `settlement.transfer` and returns a boolean).
- **Impact**: While it correctly updates `total_money_issued` (avoiding a leak) in QE scenarios, it leaves no transaction record in the ledger for that specific bond purchase. This makes auditing impossible.

### 3. Infrastructure Spending
- **Observation**: Infrastructure spending (5,000) was detected but did not contribute to the leak in this specific trace because it was funded by existing Government assets (likely initial assets or tax), not by new money creation.

## Solution Strategy
1. **Structural Guarantee**: Modify `TickOrchestrator._drain_and_sync_state` to incrementally call `process_monetary_transactions` on all transactions passing through the drain. This ensures ANY transaction generated in ANY phase (including late-bound ones) is processed exactly once.
2. **Hook Reset Logic**: Call `Government.reset_tick_flow()` in `TickOrchestrator` at the start of each tick.
3. **Persist Sync Bonds**: Update `FinanceSystem.issue_treasury_bonds_synchronous` to return generated `Transaction` objects and ensure they are propagated to the transaction log via `InfrastructureManager`.
