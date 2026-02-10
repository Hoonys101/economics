# Technical Insight: Mod-Agents Cleanup

## 1. Problem Phenomenon
During the Unit Test Cleanup Campaign for `mod-agents`, several test failures were observed due to recent architectural refactoring in `Core Agents` (`Firm`, `Household`, `Bank`, `Government`).

### Symptoms
- **`test_firm_profit.py`**: `TypeError: Firm.__init__() got an unexpected keyword argument 'id'`.
- **`test_household_refactor.py`**: `TypeError: Household.__init__() missing 2 required positional arguments`.
- **`test_bank.py`**: ID type mismatches (`str` vs `int`) causing `payment_callback` failures and missing interest transactions.
- **`test_bank_decomposition.py`**: Invalid usage of `get_balance` for customer lookups and ID type mismatches.
- **`agents/test_government.py`**: `AttributeError: ... does not have the attribute 'WelfareService'`, and logic failure in deficit spending tests due to missing side effects in mocks.

## 2. Root Cause Analysis
1.  **Orchestrator-Engine Refactor**: `Firm` and `Household` constructors were updated to accept `AgentCoreConfigDTO` and Engines, but unit tests were using legacy arguments (e.g., passing `id` directly).
2.  **ID Typing Discrepancy**: The codebase is migrating to strict `int` based `AgentID`, but older tests were casting IDs to `str` or mixing types, causing dictionary lookups to fail.
3.  **Renamed Services**: `WelfareService` was renamed/refactored to `WelfareManager`, but `test_government.py` was still trying to patch the old name.
4.  **Mock Logic Gaps**: Mocks for `issue_treasury_bonds` returned values but didn't simulate the state change (wallet update) required for subsequent logic checks in `Government`.
5.  **Hardcoded Constants**: Tests contained hardcoded "USD" strings instead of using `DEFAULT_CURRENCY`.

## 3. Solution Implementation Details
1.  **Updated Test Fixtures**: Refactored `mock_firm` and `Household` initialization in tests to use `AgentCoreConfigDTO` and `create_firm_config_dto` factory.
2.  **Strict ID Typing**: Updated `test_bank.py` and `test_bank_decomposition.py` to use `int` for `borrower_id` consistently.
3.  **Corrected API Usage**: Updated `test_bank_decomposition.py` to use `get_customer_balance` instead of `get_balance`.
4.  **Patched Correct Classes**: Updated `test_government.py` to patch `WelfareManager`.
5.  **Enhanced Mocks**: Added `side_effect` to `mock_finance.issue_treasury_bonds` to update government wallet, ensuring `provide_household_support` logic proceeds correctly.
6.  **Removed Hardcoding**: Replaced `"USD"` with `DEFAULT_CURRENCY`.

## 4. Lessons Learned & Technical Debt
- **Lesson**: When refactoring constructors or core APIs, updating unit tests immediately is crucial to avoid "rot".
- **Lesson**: Mocks should simulate side effects (state changes) if the code under test relies on those changes, not just return values.
- **Debt**: `Firm.record_revenue` did not update `current_profit` in `FinanceState`, which was fixed, but indicates a need for better synchronization or encapsulation between `Firm` (Orchestrator) and `FinanceEngine` (Logic).
- **Debt**: `FinanceEngine` relies on `mock` objects in tests which iterate over them causing TypeErrors if not properly configured (return_value=[]).
