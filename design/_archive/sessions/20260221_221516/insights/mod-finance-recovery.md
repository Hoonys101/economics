# Module A Fix: Finance & Accounting Integrity - Insight Report

## Architectural Insights
*   **Protocol Mismatch**: `simulation.models.Transaction` was not compliant with `modules.finance.api.ITransaction`. This was fixed by adding property aliases (`sender_id`, `receiver_id`, `amount_pennies`, `tick`) to the dataclass.
*   **Zero-Sum Integrity Violation (Fixed TD-ECON-M2-INV)**: `FinanceSystem.issue_treasury_bonds` incorrectly calculated `total_pennies` as `amount * 100`, assuming `amount` was dollars while other logic treated it as pennies. This caused 100x inflation in recorded transaction value. This was fixed to strictly respect the `amount` input as pennies. This resolves **TD-ECON-M2-INV** (Double-Penny Inflation Bug).
*   **Unit Confusion**: `InfrastructureManager` and `tests/integration/test_fiscal_integrity.py` mixed Dollar and Penny units (e.g. `5000 - 1000 = 4000` where 5000 was dollars and 1000 was pennies). This was remediated by ensuring `InfrastructureManager` converts Dollars to Pennies before interacting with `FinanceSystem`, and `Transaction` prices are correctly recorded as Dollars (float) while `total_pennies` remains the integer truth.
*   **DTO Purity**: `process_loan_application` allowed `Dict` inputs, bypassing type safety. This was restricted to `BorrowerProfileDTO`, and call sites in `Bank` and tests were updated.
*   **Protocol Purity**: `FinanceSystem` constructor now strictly uses `ICentralBank` protocol instead of a string forward reference. Call sites using mock objects were updated to ensure protocol compliance (e.g. `Bank.get_debt_status`).

## Regression Analysis
*   **Infrastructure Investment**: The integration test `test_infrastructure_investment_generates_transactions_and_issues_bonds` revealed that `InfrastructureManager` was issuing bonds with incorrect values due to unit confusion. The manager was updated to handle currency conversion correctly, and the test assertions were updated to reflect corrected scaled values (e.g. Price 50.0 for 5000 pennies).
*   **Bank Service Interface**: Unit tests for `Bank` mocked `FinanceSystem` responses using outdated DTO structures or implicit types. These were updated to match the strict `DebtStatusDTO` and `LoanInfoDTO` definitions.
*   **Inheritance Manager**: Tests relying on mocked `Bank.get_debt_status` failed because the mock returned a generic object instead of a DTO with `total_outstanding_pennies`. Mocks were updated to return valid DTO-like structures.

## Test Evidence
All tests passed, including:
*   `tests/system/test_audit_integrity.py`: Verifies birth/inheritance integrity.
*   `tests/unit/finance/`: Verifies core finance logic.
*   `tests/integration/test_fiscal_integrity.py`: Verifies government spending and bond issuance.
*   `tests/integration/test_government_finance.py`: Verifies transaction generation.
*   Full suite `pytest tests/`.

```
============================= 964 passed in 17.64s =============================
```
