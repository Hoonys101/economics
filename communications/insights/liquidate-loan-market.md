# Insight Report: Liquidate LoanMarket Dict-Leak

## 1. Architectural Insights

### Technical Debt Resolved: [TD-DTO-DESYNC-2026]
- **Issue**: `LoanMarket` methods (`convert_staged_to_loan`, etc.) and `Bank` mocks were leaking raw dictionaries instead of strict `LoanInfoDTO` objects. This caused `AttributeError` in consumers expecting dot-notation access.
- **Resolution**:
    1. Refactored `modules/finance/api.py` to enforce strict DTO definitions for `LoanInfoDTO` and `BorrowerProfileDTO` (aligning with mandatory spec).
    2. Updated `simulation/loan_market.py` to construct and return `LoanInfoDTO` objects.
    3. Updated `simulation/bank.py` to handle new DTO signatures and return types.
    4. Liquidated legacy dictionary mocks in `tests/unit/markets/test_loan_market_mortgage.py`.

### Architectural Decisions
- **Strict DTOs**: Moved to `dataclass` for `LoanInfoDTO` and `BorrowerProfileDTO`.
- **Protocol Compliance**: `IBankService` introduced to enforce strict contract between Markets and Bank.
- **Penny Migration**: Explicitly mapped `remaining_principal` (legacy) to `outstanding_balance` (new standard) while ensuring underlying data remains in pennies (via `LoanStateDTO` mapping in `FinanceSystem`).

## 2. Test Evidence

### Unit Test Verification
Command: `python3 -m pytest tests/unit/markets/test_loan_market_mortgage.py`

Output:
```
tests/unit/markets/test_loan_market_mortgage.py::TestLoanMarketMortgage::test_evaluate_mortgage_success PASSED [ 14%]
tests/unit/markets/test_loan_market_mortgage.py::TestLoanMarketMortgage::test_evaluate_mortgage_fail_ltv PASSED [ 28%]
tests/unit/markets/test_loan_market_mortgage.py::TestLoanMarketMortgage::test_evaluate_mortgage_fail_dti PASSED [ 42%]
tests/unit/markets/test_loan_market_mortgage.py::TestLoanMarketMortgage::test_evaluate_mortgage_fail_dti_with_existing_debt PASSED [ 57%]
tests/unit/markets/test_loan_market_mortgage.py::TestLoanMarketMortgage::test_stage_mortgage_success PASSED [ 71%]
tests/unit/markets/test_loan_market_mortgage.py::TestLoanMarketMortgage::test_stage_mortgage_fail_eval PASSED [ 85%]
tests/unit/markets/test_loan_market_mortgage.py::TestLoanMarketMortgage::test_end_to_end_dto_purity PASSED [100%]

============================== 7 passed in 0.32s ===============================
```

### Regression Test Verification
Command: `python3 -m pytest tests/unit/finance tests/unit/test_bank.py tests/unit/test_bank_decomposition.py`

Output:
```
============================== 47 passed in 0.55s ==============================
```
