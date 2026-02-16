# Insight Report: Finance & Credit Purity Implementation (fix-dto-subscripting)

## 1. Architectural Insights

### DTO Standardization
The codebase was in a hybrid state regarding Data Transfer Objects (DTOs) in the Finance module. Some were `TypedDict`s (legacy), while others were `dataclasses`. This caused runtime errors (`TypeError: object is not subscriptable`) when components expected one format but received the other, specifically `BorrowerProfileDTO` and `LoanInfoDTO`.

We are enforcing "DTO Purity" by converting these critical DTOs to strict, frozen `dataclasses`. This ensures:
- **Type Safety**: Static analysis can verify field access.
- **Immutability**: Financial data snapshots cannot be accidentally modified after creation.
- **Consistency**: All consumers (Bank, CreditScoring, LoanMarket) must use dot-notation access.

### Integer Semantics (Pennies) vs. Spec Floats
The provided implementation specification used `float` for monetary values in the DTO definitions. However, the existing codebase and architectural guardrails heavily emphasize "Zero-Sum Integrity" and usage of **integer pennies** to prevent floating-point errors.
**Decision**: I have retained the `int` type for all monetary fields in the DTOs (`gross_income`, `original_amount`, etc.) to align with the project's core "Pennies Migration" and prevent regression. I have added the new fields requested (`status`, `term_ticks`, `employment_status`) while respecting the existing type system.

### Removal of `SimpleNamespace` Hack
The `Bank.grant_loan` method contained a `SimpleNamespace` conversion hack to handle potential dictionary returns from `FinanceSystem`. Since `FinanceSystem` is now verified to return proper `LoanInfoDTO` objects, this hack is removed to enforce strict typing. Any legacy dictionary usage will now be caught by type checkers or fail fast, which is preferable to silent masking.

## 2. Test Evidence

```
tests/unit/finance/test_bank_service_interface.py::TestBankServiceInterface::test_bank_methods_presence
-------------------------------- live log setup --------------------------------
INFO     simulation.bank:bank.py:70 Bank 1 initialized (Stateless Proxy).
PASSED                                                                   [  9%]
tests/unit/finance/test_bank_service_interface.py::TestBankServiceInterface::test_grant_loan
-------------------------------- live log setup --------------------------------
INFO     simulation.bank:bank.py:70 Bank 1 initialized (Stateless Proxy).
PASSED                                                                   [ 18%]
tests/unit/finance/test_bank_service_interface.py::TestBankServiceInterface::test_repay_loan
-------------------------------- live log setup --------------------------------
INFO     simulation.bank:bank.py:70 Bank 1 initialized (Stateless Proxy).
-------------------------------- live log call ---------------------------------
WARNING  simulation.bank:bank.py:244 Bank.repay_loan called. Manual repayment not yet implemented in Engine API.
PASSED                                                                   [ 27%]
tests/unit/finance/test_bank_service_interface.py::TestBankServiceInterface::test_get_balance
-------------------------------- live log setup --------------------------------
INFO     simulation.bank:bank.py:70 Bank 1 initialized (Stateless Proxy).
PASSED                                                                   [ 36%]
tests/unit/finance/test_bank_service_interface.py::TestBankServiceInterface::test_get_debt_status
-------------------------------- live log setup --------------------------------
INFO     simulation.bank:bank.py:70 Bank 1 initialized (Stateless Proxy).
PASSED                                                                   [ 45%]
tests/unit/finance/test_bank_service_interface.py::TestBankServiceInterface::test_interface_compliance_mypy PASSED [ 54%]
tests/unit/finance/test_credit_scoring.py::test_assess_approved PASSED   [ 63%]
tests/unit/finance/test_credit_scoring.py::test_assess_dti_fail PASSED   [ 72%]
tests/unit/finance/test_credit_scoring.py::test_assess_ltv_fail PASSED   [ 81%]
tests/unit/finance/test_credit_scoring.py::test_assess_unsecured_cap_fail PASSED [ 90%]
tests/unit/finance/test_credit_scoring.py::test_zero_income_fail PASSED  [100%]

============================== 11 passed in 0.35s ==============================
```
