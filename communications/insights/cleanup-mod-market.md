# Technical Insight Report: Market Module Cleanup

**ID:** INSIGHT-MARKET-CLEANUP-001
**Date:** 2024-05-22 (Simulated)
**Author:** Jules (AI Agent)
**Scope:** `mod-market` (`simulation/markets`, `modules/market`, `tests/unit/markets`)

## 1. Problem Phenomenon
During the Unit Test Cleanup Campaign, the following failures were observed:

1.  **`tests/unit/markets/test_circuit_breaker_relaxation.py`**:
    -   `TypeError: an integer is required` when initializing `deque(maxlen=window_size)`.
    -   `window_size` was retrieved from `config_module` which was a `MagicMock`, returning another Mock instead of an int.

2.  **`tests/unit/markets/test_housing_transaction_handler.py`**:
    -   `TypeError: '<' not supported between instances of 'MagicMock' and 'float'` during `buyer_assets < down_payment` check.
    -   `AssertionError: expected call not found` for `settlement_system.transfer`.
    -   `AssertionError: assert True is False` (Loan Rejected test passed unexpectedly).
    -   Logic failures indicated `isinstance(buyer, IHousingTransactionParticipant)` was returning `False`, causing the handler to fallback to cash-only path or fail validation.

3.  **`tests/unit/markets/test_loan_market.py`**:
    -   `AssertionError: expected call not found`.
    -   Expected `grant_loan(borrower_id='1', ...)` but received `grant_loan(borrower_id=1, ...)` (int vs str).

## 2. Root Cause Analysis

1.  **Mock Configuration Gaps**:
    -   `MagicMock` objects return new Mocks by default for any attribute access.
    -   `config_mock.PRICE_VOLATILITY_WINDOW_TICKS` was accessed but not set, returning a Mock which caused `deque` initialization failure.
    -   `buyer.get_balance` was accessed but not configured, returning a Mock which failed numerical comparison.

2.  **Protocol vs Mock Incompatibility**:
    -   `IHousingTransactionParticipant` is a `@runtime_checkable` Protocol.
    -   Using `MagicMock(spec=Household)` creates an object that satisfies `isinstance(obj, Household)`.
    -   However, `isinstance(obj, Protocol)` checks for the presence of specific attributes/methods.
    -   If these attributes are not explicitly set or accessed on the Mock (which creates them lazily), the Protocol check fails.
    -   `Household` class itself implements the protocol, but the Mock derived from it was not automatically satisfying the runtime check in the test environment.

3.  **Legacy Type Assumptions**:
    -   `test_loan_market.py` was written assuming `borrower_id` is passed as a string.
    -   The actual implementation in `LoanMarket` casts `agent_id` to `AgentID` (int alias) or keeps it as int if it came from `Order` object (where `agent_id` is int).

## 3. Solution Implementation Details

1.  **Fixed Mock Configuration**:
    -   Explicitly set `config_mock.PRICE_VOLATILITY_WINDOW_TICKS = 20` in `test_circuit_breaker_relaxation.py`.
    -   Configured `buyer.get_balance.return_value = 100000.0` in `test_housing_transaction_handler.py`.

2.  **Protocol Compliance for Mocks**:
    -   Changed `spec=Household` to `spec=IHousingTransactionParticipant` (and `IPropertyOwner` for seller) in `test_housing_transaction_handler.py` to better align with the code's expectations.
    -   Manually added required attributes (`owned_properties`, `add_property`, `remove_property`, `deposit`, `withdraw`, etc.) to the Mocks to ensure `isinstance(mock, Protocol)` returns `True`.

3.  **Updated Test Assertions**:
    -   Updated `test_loan_market.py` to expect `borrower_id=1` (int) in `assert_called_once_with`.

4.  **Hardcoded Constants Verification**:
    -   Verified no hardcoded `"USD"` or `"KRW"` strings existed in the scope.

## 4. Lessons Learned & Technical Debt

-   **Mocking Protocols**: When code uses `isinstance(obj, Protocol)`, simple `MagicMock(spec=Class)` is often insufficient. It is more robust to use `spec=Protocol` (if it's a class) or manually ensure all protocol members exist on the mock.
-   **Type Consistency**: The mix of `int` and `str` for Agent IDs is a recurring source of friction. The codebase is moving towards `AgentID` (int), but tests often lag behind.
-   **Test Isolation**: `test_loan_market.py` testing `simulation/loan_market.py` (outside `markets/` folder) caused some initial confusion but was correctly identified as in-scope.

**Technical Debt Identified:**
-   `TD-PROTOCOL-MOCK`: Need a standard utility for creating Protocol-compliant mocks to avoid repetitive manual attribute setting in tests.
-   `TD-AGENT-ID`: Ensure all tests strictly use `int` for agent IDs to match `AgentID` type alias.
