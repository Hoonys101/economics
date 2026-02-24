# Insight Report: WO-IMPL-LEDGER-HARDENING

## 1. Architectural Insights
### Penny Standard Enforcement
The transition to a strict Integer-based Penny Standard revealed several areas where floating-point math was still prevalent, particularly in the core `TickOrchestrator` and `MonetaryLedger`.
- **Decision**: We enforced `int` types for all monetary values (`baseline_money_supply`, `total_money_issued`, etc.) to eliminate floating-point drift.
- **Impact**: M2 verification is now exact. Tolerance is defined in pennies (1000 pennies = $10.00) rather than a ratio of floats that might suffer from precision errors.

### Shadow Transaction Elimination & Liability Drift
"Shadow Transactions" were identified where balances were modified directly without a corresponding `Transaction` object being emitted or processed.
- **Problem**: Initially, we removed *all* direct updates in `DebtServicingEngine` to rely on the `FinancialTransactionHandler`.
- **Critical Finding**: This caused "Liability Drift". The Handler updates the *Cash Wallet* (Assets), but the Engine updates the *Accounting Ledger* (DTOs). If the Engine stops updating the DTO (Deposit Balance), the Bank's liability to the customer remains unchanged while the customer's cash decreases (via Settlement), creating an infinite liability glitch.
- **Solution**: We restored the `deposit.balance_pennies -= ...` logic in the Engine. The Engine updates the *Internal Ledger* (DTO), while the emitted Transaction drives the *Settlement System* (Real Cash). Both must happen to maintain Double-Entry integrity across the distinct Accounting and Cash domains.

### Receipt Transaction Safeguards
New transactions emitted for Taxes and Liquidation are effectively "Receipts" for actions already settled atomically.
- **Risk**: Double-Counting or Double-Spending if these receipts are re-processed by handlers.
- **Safeguard**: These transactions are marked with `metadata={"executed": True}`. We explicitly verified and documented that `TransactionProcessor` skips these transactions, ensuring they serve as audit records only.

## 2. Regression Analysis
- **`tests/unit/government/test_monetary_ledger_units.py`**:
    - **Failure**: `test_monetary_ledger_uses_pennies_source_and_returns_dollars` failed because `get_monetary_delta` now returns pennies (int) instead of dollars (float).
    - **Fix**: Updated the test to expect `100` (pennies) instead of `1.0` (dollars).
- **`tests/unit/test_transaction_handlers.py`**:
    - **Update**: Enhanced the test to verify that `context.transaction_queue` is populated with tax transactions after a successful goods trade.

## 3. Test Evidence
```
tests/unit/government/test_monetary_ledger_units.py::test_monetary_ledger_uses_pennies_source_and_returns_pennies PASSED [ 50%]
tests/simulation/test_initializer.py::TestSimulationInitializer::test_registry_linked_before_bootstrap PASSED [100%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_startup_pass PASSED [  5%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_startup_fail PASSED [ 11%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_established_pass PASSED [ 16%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_established_fail PASSED [ 22%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_market PASSED [ 27%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_qe PASSED [ 33%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_fail PASSED [ 38%]
tests/unit/modules/finance/test_system.py::test_bailout_fails_with_insufficient_government_funds PASSED [ 44%]
tests/unit/modules/finance/test_system.py::test_grant_bailout_loan PASSED [ 50%]
tests/unit/modules/finance/test_system.py::test_service_debt_central_bank_repayment PASSED [ 55%]
tests/unit/systems/test_liquidation_manager.py::TestLiquidationManager::test_asset_liquidation_integration PASSED [ 61%]
tests/unit/systems/test_liquidation_manager.py::TestLiquidationManager::test_bank_claim_handling PASSED [ 66%]
tests/unit/systems/test_liquidation_manager.py::TestLiquidationManager::test_initiate_liquidation_orchestration PASSED [ 72%]
tests/unit/systems/lifecycle/test_death_system.py::TestDeathSystem::test_firm_liquidation PASSED [ 77%]
tests/unit/systems/lifecycle/test_death_system.py::TestDeathSystem::test_firm_liquidation_cancels_orders PASSED [ 83%]
tests/unit/test_transaction_handlers.py::TestGoodsTransactionHandler::test_goods_settle_fail PASSED [ 88%]
tests/unit/test_transaction_handlers.py::TestGoodsTransactionHandler::test_goods_success_atomic PASSED [ 94%]
tests/unit/test_transaction_handlers.py::TestLaborTransactionHandler::test_labor_atomic_settlement PASSED [100%]
tests/unit/test_ledger_safety.py::TestLedgerSafety::test_financial_handler_does_not_touch_ledger_dto PASSED [ 50%]
tests/unit/test_ledger_safety.py::TestLedgerSafety::test_processor_skips_executed_transactions PASSED [100%]
```
