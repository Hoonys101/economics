# Mission Report: Loan Saga Refactor

## 1. Overview
This mission focuses on refactoring the `LoanManager` (specifically `LoanMarket` in `simulation/loan_market.py`) to align with the new Saga pattern guidelines, ensuring synchronous logic does not block tick flow in the future and strictly adhering to the `ILoanMarket` interface defined in `modules/finance/sagas/housing_api.py`.

## 2. Technical Debt & Insights

### TD-New: Interface Duplication for `ILoanMarket`
- **Location**: `modules/market/housing_planner_api.py` and `modules/finance/sagas/housing_api.py`.
- **Description**: Two conflicting definitions of `ILoanMarket` exist. One expects `stage_mortgage` returning `LoanDTO` (legacy/sync), the other expects `stage_mortgage_application` returning `str` (Saga/async).
- **Impact**: Confusion in type hints and potential runtime errors if consumers assume one interface but get the implementation of the other. `HousingTransactionSagaHandler` was importing the Saga version but calling methods from the Legacy version.
- **Resolution**: Refactoring `LoanMarket` to implement the Saga interface and updating the legacy interface definition to match.

### TD-New: Synchronous Bank Dependency
- **Location**: `simulation/loan_market.py` -> `IBankService`.
- **Description**: `LoanMarket` depends on `IBankService.stage_loan`, which returns a `LoanDTO` immediately. This forces `LoanMarket` to be synchronous.
- **Impact**: "Non-blocking" behavior is simulated. True async processing would require the Bank to accept a request and process it in a future tick.
- **Mitigation**: We wrap the synchronous call in a method with an async-compatible signature (`stage_mortgage_application` returning ID), allowing future refactoring of the Bank without breaking the Loan Market interface.

### Insight: DTO Alignment
- `MortgageApplicationDTO` (Finance API) and `MortgageApplicationRequestDTO` (Loan API) are structurally similar but separate types. Sagas use the former, `LoanMarket` logic uses the latter. Duck typing (using `TypedDict` compatibility) is currently bridging this gap.

## 3. Changes
- Refactored `LoanMarket` to expose `stage_mortgage_application`.
- Updated `HousingTransactionSagaHandler` to use the new method.
- Updated `ILoanMarket` protocol in `modules/market/housing_planner_api.py`.
