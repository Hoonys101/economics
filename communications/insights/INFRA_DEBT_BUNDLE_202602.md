# Infrastructure Debt Bundle Resolution (TD-203, TD-204, TD-210, TD-223)

## Technical Debt Resolutions

### TD-203: Update Stale SettlementSystem Unit Tests
- **Context:** `SettlementSystem`'s unit tests were relying heavily on mocking the `HousingTransactionSagaHandler` class, potentially masking integration issues with the actual handler logic.
- **Resolution:** Created `tests/unit/systems/test_settlement_saga_integration.py`. This test suite verifies the orchestration loop by using the *real* `HousingTransactionSagaHandler` class with mocked dependencies (Agents, HousingService, LoanMarket). This ensures that the `SettlementSystem` correctly delegates to the handler and processes the returned state transitions (e.g., INITIATED -> CREDIT_CHECK).
- **Insight:** Mocking the orchestrator's delegate (Handler) is good for unit testing the orchestrator's state machine, but integration tests using the real delegate are crucial to verify that the delegate's contract matches what the orchestrator expects.

### TD-204: Refactor BubbleObservatory (SRP)
- **Context:** `BubbleObservatory` violated SRP by coupling complex metric calculation logic with CSV logging and state management.
- **Resolution:** Extracted calculation logic into a new `BubbleMetricsCalculator` class. `BubbleObservatory` now acts as a coordinator, instantiating the calculator and handling the side-effect (logging).
- **Insight:** State access patterns differed between the calculator (using `world_state`) and the test suite (using `simulation.agents`). The refactor highlighted this discrepancy. We updated the design to allow injecting `agents` explicitly, making the component more testable and flexible.

### TD-210: Clean Conftest.py
- **Context:** `tests/conftest.py` contained commented-out imports and references to heavy classes (`CentralBank`, `Bank`) that were causing import overhead or confusion.
- **Resolution:** Removed the commented code. Verified that `mock_central_bank` and `mock_bank` fixtures remain lightweight mocks, preventing inadvertent loading of heavy libraries like `numpy` during test collection.

### TD-223: Unify Mortgage DTOs
- **Context:** Duplicate DTOs `MortgageApplicationDTO` (Finance API) and `MortgageApplicationRequestDTO` (Loan API) caused confusion and potential drift.
- **Resolution:** Deprecated `MortgageApplicationRequestDTO`. Updated `LoanMarket`, `HousingSystem`, and `HousingPlanner` to use `MortgageApplicationDTO` from `modules.finance.api`. Added an alias in `modules/market/loan_api.py` for transitional safety, though all internal usages were updated.
- **Insight:** Unifying DTOs required careful updates across multiple systems (Housing, Loan, Finance). Using a shared `api.py` in `modules/finance` as the source of truth helps enforce consistency.

## Remaining Debt / Future Work
- **DTO Alias:** `MortgageApplicationRequestDTO` alias remains in `modules/market/loan_api.py`. It should be removed in a future cleanup once external consumers (if any) are confirmed to be updated.
- **HousingPlanner Logic:** `HousingPlanner` logic is becoming complex. It duplicates some logic found in `LoanMarket` (e.g., DTI estimation). Future refactoring should centralize credit assessment logic even further, perhaps exposing a `Bank.estimate_max_loan()` method.
