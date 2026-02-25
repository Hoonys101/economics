# WO-IMPL-FIN-CREDIT-EXPANSION-TRACKING Insight Report

## Architectural Insights
1.  **Bank as M2 Authority**: We shifted the responsibility of M2 event recording (Expansion/Contraction) from `FinanceSystem` (ledger state) to `Bank` (agent action). This aligns with the principle that the *act of transfer* (settlement) is what creates/destroys M2 when it crosses the boundary between Non-M2 (Bank Reserves) and M2 (Public). This eliminates the risk of "Phantom M2" where a ledger update claims expansion but settlement fails.
2.  **Government M2 Exclusion**: We explicitly excluded Government ID from M2 calculation. This forced a cleanup of legacy `get_monetary_delta` usage in `TickOrchestrator`, which was adding Government Balance Change to Expected M2. With Gov excluded, only *transfers* (Fiscal Injection/Leakage) matter, which are tracked by `MonetaryLedger`.
3.  **Protocol-Driven Checking**: Replaced fragile `hasattr` checks in `Bank` with `try-except AttributeError` patterns, paving the way for stricter `isinstance` checks once Protocols are fully stabilized.
4.  **Duck Typing in Accounting**: Refactored `AccountingSystem` to remove direct dependencies on concrete `Household` and `Firm` classes, using Duck Typing (`hasattr`) to check for `record_revenue` or `add_consumption_expenditure`. This reduces coupling and circular dependency risks.

## Regression Analysis
*   **Test Failure**: `tests/unit/test_bank.py::test_grant_loan_with_object_calls_transfer` failed initially because the mock `ISettlementSystem` lacked the `monetary_ledger` attribute required by the new logic.
*   **Fix**: Updated the test fixture to include `mock_settlement_system.monetary_ledger` and assert that `record_monetary_expansion` is called. This proves the integration logic is active.
*   **Legacy Cleanup**: Removed `government.get_monetary_delta()` from `TickOrchestrator` fallback logic as it relied on the obsolete assumption that Government Balance was part of M2.

## Test Evidence
```text
tests/unit/test_bank.py::test_bank_assets_delegation PASSED [ 12%]
tests/unit/test_bank.py::test_bank_deposit_delegation PASSED [ 25%]
tests/unit/test_bank.py::test_bank_withdraw_delegation PASSED [ 37%]
tests/unit/test_bank.py::test_grant_loan_delegation PASSED [ 50%]
tests/unit/test_bank.py::test_withdraw_for_customer PASSED [ 62%]
tests/unit/test_bank.py::test_run_tick_delegates_to_service_debt PASSED [ 75%]
tests/unit/test_bank.py::test_grant_loan_with_object_calls_transfer PASSED [ 87%]
tests/unit/test_bank.py::test_grant_loan_with_id_skips_transfer PASSED [100%]

tests/integration/test_m2_integrity.py::TestM2Integrity::test_credit_creation_expansion PASSED [ 12%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_credit_destruction_contraction PASSED [ 25%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_internal_transfers_are_neutral PASSED [ 37%]

tests/finance/test_settlement_integrity.py::TestSettlementIntegrity::test_transfer_float_raises_error PASSED [ 50%]
tests/finance/test_settlement_integrity.py::TestSettlementIntegrity::test_create_and_transfer_float_raises_error PASSED [ 75%]
tests/finance/test_settlement_integrity.py::TestSettlementIntegrity::test_issue_treasury_bonds_float_leak PASSED [100%]

tests/integration/test_reporting_pennies.py::TestReportingPennies::test_household_expenditure_tracking PASSED [ 75%]
tests/integration/test_reporting_pennies.py::TestReportingPennies::test_household_income_tracking PASSED [ 81%]
```
