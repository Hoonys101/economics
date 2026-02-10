# Mission Insights: Core Agent & Protocol Restoration

## Technical Debt & Insights

### 1. Mock fragility in System Tests
`tests/system/test_engine.py` uses a mix of real objects (`Firm`, `Simulation`) and Mocks (`Household`, `Transaction`). This hybrid approach causes significant friction when protocols change (e.g., `IFinancialAgent` requiring `get_balance`). The mocks often lack the full behavior required by complex systems like `SettlementSystem` (e.g., side effects for `withdraw` working but state not persisting correctly for rollback logic, or method signature mismatches).
**Recommendation:** Refactor system tests to use lightweight real implementations of `Household` (stubbed engines) instead of pure Mocks where possible, or use a strictly typed `FakeAgent` that fully implements `IAgent` protocols.

### 2. Protocol Adherence
The shift to `IFinancialAgent` (withdraw/deposit with currency) and `IInventoryHandler` is largely complete in code but tests lag behind. The strict enforcement of `currency` in `withdraw` exposed that many mocks were naive.
**Recommendation:** Add a linting step or a test utility that verifies Mocks against Protocols (`verify_object=True` or custom checker) to catch signature drifts early.

### 3. State Access Patterns
Direct access to attributes like `agent.inventory` (dict) or `agent.finance.balance` persists in tests despite the codebase moving to `agent.get_quantity()` and `agent.wallet.get_balance()`.
**Action Taken:** Fixed several occurrences in `test_engine.py`, but a global audit of test assertions is recommended.

### 4. Settlement System Complexity
The `settle_atomic` failure in `test_process_transactions_labor_trade` (rollback despite valid conditions) suggests a subtle issue with Mock state interactions or `TaxationSystem` configuration in the test environment. The lack of visibility (swallowed logs in tests) made debugging difficult.
**Recommendation:** Ensure `mock_logger` in tests is configured to print to stderr on failure, or use `caplog` fixture more effectively.

## Protocol Deviations Fixed
- `Household.__init__`: Updated to use `AgentCoreConfigDTO` and `engine`.
- `Firm.__init__`: Updated to use `AgentCoreConfigDTO` and `engine`.
- `MockAgent`: Updated `withdraw`/`deposit` to accept `currency`.
- `test_api_extensions.py`: Updated to use `_econ_state.assets` structure.
