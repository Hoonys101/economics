# WO-WAVE5-MONETARY-FIX: M2 Integrity & Audit Restoration

## Architectural Insights

### 1. Ledger Synchronization via Transaction Injection
The root cause of the M2 leakage was identified as "ghost money" creation during implicit system operations, specifically Lender of Last Resort (LLR) injections. These operations used the `SettlementSystem` but failed to bubble up the resulting transactions to the `WorldState` transaction queue, which is the single source of truth for the `MonetaryLedger`.

To fix this, we implemented a **Transaction Injection Pattern** for the `CentralBankSystem`. By injecting the `WorldState.transactions` list into the `CentralBankSystem` upon initialization, we enable it to directly append side-effect transactions (like LLR minting) to the global ledger. This ensures that every penny created or destroyed is visible to the audit system, regardless of where in the call stack the operation occurred.

### 2. Orchestrator Phase Consolidation
We removed the redundant `Phase_MonetaryProcessing` from the `TickOrchestrator`. Previously, this phase attempted to process transactions independently, leading to potential double-counting or race conditions with `Phase3_Transaction`. By consolidating all transaction processing logic (including `MonetaryLedger` updates) into `Phase3_Transaction`, we ensure a strictly linear and atomic execution flow: Execute -> Verify -> Record.

### 3. M2 Perimeter Harmonization
We refined the definition of M2 (Total Money Supply) in `WorldState.calculate_total_money`. The `PublicManager` (ID 4) and System Agent (ID 5) are now explicitly excluded from the M2 calculation, aligning them with the Central Bank (ID 0) as "System Sinks". This prevents money held by these administrative agents (e.g., from escheatment) from being counted as circulating supply, eliminating "phantom" M2 fluctuations. ID comparisons were also robustified using string conversion to preventing type mismatch errors.

### 4. Bond Repayment Logic
We enhanced the `MonetaryLedger` to respect the split between Principal and Interest during bond repayments. Previously, the ledger treated the entire repayment (Principal + Interest) as money destruction (Contraction). Now, if metadata is available, only the Principal portion is counted as M0/M2 destruction, while Interest is treated as a transfer to the System (which may or may not be recycled), aligning the ledger with standard accounting practices where only asset redemption contracts the supply.

## Regression Analysis
No regressions are expected in agent behavior, as the changes are primarily accounting-related. The core logic of LLR and Social Policy execution remains unchanged; only the reporting of these actions has been altered. Existing tests relying on M2 consistency should now pass more reliably. The updates to `CentralBankSystem` initialization and `Government.execute_social_policy` signature were propagated to all call sites and tests.

## Test Evidence
All unit and integration tests passed (1033 passed, 11 skipped).
Tests covering LLR expansion (`test_lender_of_last_resort_expansion`), asset liquidation (`test_asset_liquidation_expansion`), and tax collection (`test_atomic_wealth_tax_collection_success`) were updated and verified.
