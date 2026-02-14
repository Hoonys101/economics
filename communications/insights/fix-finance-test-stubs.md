# Insight Report: Fix Finance Test Stubs

**Date**: 2026-02-14
**Mission**: `fix-finance-test-stubs`
**Author**: Jules (AI Agent)

## 1. Architectural Insights

### A. Stub Compliance with Protocols
The `StubFirm` class in `tests/unit/modules/finance/test_system.py` was updated to fully comply with the `IFinancialFirm` protocol. This ensures that unit tests accurately reflect the contract expected by `FinanceSystem`. Specifically, the following properties were added:
- `balance_pennies` (mapped to `cash_reserve`)
- `capital_stock_pennies`
- `inventory_value_pennies`
- `monthly_wage_bill_pennies`
- `total_debt_pennies`
- `retained_earnings_pennies`
- `average_profit_pennies`

This aligns the test double with the strict typing requirements of the domain layer, facilitating the migration to integer-only financial calculations (`TD-INT-PENNIES-FRAGILITY`).

### B. Test Logic Alignment
The mapping of `balance_pennies` to `cash_reserve` necessitated updates to `test_evaluate_solvency_startup_pass` and `test_evaluate_solvency_startup_fail`. Previously, these tests modified a legacy `_assets` attribute. They now modify `cash_reserve` directly to influence the solvency check, ensuring the test inputs correctly propagate to the logic under test.

## 2. Test Evidence

The following output demonstrates that all tests in `tests/unit/modules/finance/test_system.py` passed after the changes:

```
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_startup_pass PASSED [ 10%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_startup_fail PASSED [ 20%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_established_pass PASSED [ 30%]
tests/unit/modules/finance/test_system.py::test_evaluate_solvency_established_fail PASSED [ 40%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_market
-------------------------------- live log call ---------------------------------
WARNING  modules.finance.system:system.py:325 BOND_ISSUANCE_WARNING | No SettlementSystem attached. Wallet updates skipped.
PASSED                                                                   [ 50%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_qe PASSED [ 60%]
tests/unit/modules/finance/test_system.py::test_issue_treasury_bonds_fail
-------------------------------- live log call ---------------------------------
WARNING  modules.finance.system:system.py:305 BOND_ISSUANCE_SKIPPED | Bank COMMERCIAL_BANK insufficient reserves: 10000000 < 20000000
PASSED                                                                   [ 70%]
tests/unit/modules/finance/test_system.py::test_bailout_fails_with_insufficient_government_funds
-------------------------------- live log call ---------------------------------
WARNING  modules.finance.system:system.py:414 BAILOUT_DENIED | Government insufficient funds: 10000 < 50000
PASSED                                                                   [ 80%]
tests/unit/modules/finance/test_system.py::test_grant_bailout_loan PASSED [ 90%]
tests/unit/modules/finance/test_system.py::test_service_debt_central_bank_repayment
-------------------------------- live log call ---------------------------------
WARNING  modules.finance.system:system.py:325 BOND_ISSUANCE_WARNING | No SettlementSystem attached. Wallet updates skipped.
PASSED                                                                   [100%]

============================== 10 passed in 0.39s ==============================
```
