# Mission Insights: JULES_C_SYSTEMS

## Technical Debt & Insights

### Insight 1: InheritanceManager Purity Refactor
* **Phenomenon**: `test_inheritance_manager.py` was failing because it expected direct calls to `settlement_system.transfer`.
* **Cause**: `InheritanceManager` has been refactored to follow the Saga pattern, where it produces `Transaction` intent objects (e.g., `inheritance_distribution` with heir metadata) rather than executing side-effects directly.
* **Solution**: Updated unit tests to verify the generation and content of the returned `Transaction` objects instead of mocking the settlement system's execution.
* **Lesson Learned**: When refactoring for Purity/Saga patterns, ensure tests verify the *message* (DTO/Transaction) produced, not the *execution* of that message, which belongs to the Handler/System tests.

### Insight 2: OrderDTO Immutability and Signature
* **Phenomenon**: `test_order_book_market.py` failed with `AttributeError` on `order.quantity` updates and `TypeError` on `__init__`.
* **Cause**: `OrderDTO` is an immutable dataclass (`frozen=True`) and aliases `order_type` to `side` and `price` to `price_limit`. Tests were using legacy mutable behavior and old signature.
* **Solution**: Updated tests to use `side` and `price_limit`. For quantity assertions, verified the market's internal state (Order Book) instead of expecting the order object reference to update in-place.
* **Lesson Learned**: Immutable DTOs require tests to inspect the system state or returned new objects, as the input objects remain unchanged.

### Insight 3: Widespread Mocking Deficiencies (TD-122)
* **Phenomenon**: Multiple system tests (`test_social_system.py`, `test_registry_housing.py`, etc.) fail with `AttributeError: Mock object has no attribute '_econ_state'` or `_bio_state`.
* **Cause**: The `Household` class refactor moved state to `_econ_state` and `_bio_state` components, but many legacy mocks only mock the top-level attributes or use `spec=Household` without populating the sub-components.
* **Solution**: Fixed `test_housing_transaction_handler.py` by explicitly mocking `_econ_state`. Other tests remain broken and require similar updates.
* **Lesson Learned**: Mocks for complex entities like `Household` should be centralized or use a factory that ensures all required components (`_econ_state`, `_bio_state`) are present to avoid fragile, repetitive test setup.

### Insight 4: LoanMarket Logic Update (WO-024)
* **Phenomenon**: `test_loan_market.py` failed because `grant_loan` return signature changed and logic for generating transactions requires a `credit_tx`.
* **Cause**: `Bank.grant_loan` now returns `(LoanInfoDTO, Transaction)`. `LoanMarket` only appends a transaction if `credit_tx` is present, to avoid double counting with commercial loan transactions.
* **Solution**: Updated mocks to return a tuple `(dto, mock_tx)` to satisfy the `LoanMarket` logic and ensure a transaction is generated for the test to assert on.
