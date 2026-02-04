# TD Audit Fixes & Architectural Insights

**Mission Key:** TD-Audit-Fixes
**Date:** 2026-02-05

## 1. Resolved Technical Debt

### TD-231: CommerceSystem Sales Tax Planning Leak
- **Issue**: Consumption planning ignored sales tax, leading to execution failures.
- **Fix**: Updated `CommerceSystem.plan_consumption_and_leisure` to include `SALES_TAX_RATE` (default 5%) in affordability calculations.

### TD-232: InheritanceManager Encapsulation Violation
- **Issue**: `InheritanceManager` was bypassing `TransactionProcessor` and manually mutating agent state (`portfolio`, `owned_properties`) while creating "fake" executed transactions.
- **Fix**: Refactored `InheritanceManager` to:
    - Stop manual mutation.
    - Create `asset_liquidation` and `asset_transfer` transactions.
    - Execute them synchronously via `simulation.transaction_processor.execute(..., [tx])`.
    - Rely on `MonetaryTransactionHandler` (and `AssetTransferHandler`) to perform the state mutations.

### TD-233: FinanceDepartment Law of Demeter Violation
- **Issue**: `FinanceDepartment` directly accessed `Household._econ_state` internals.
- **Fix**:
    - Added `portfolio` property to `Household` (via `HouseholdFinancialsMixin`).
    - Updated `FinanceDepartment` to use `household.portfolio`.
    - Refactored `MonetaryTransactionHandler` and `StockTransactionHandler` to prefer `agent.portfolio` interface, removing broken legacy access to `shares_owned`.

### TD-234: WelfareService Abstraction Leak
- **Issue**: `WelfareService` used fragile `hasattr` checks and directly mutated `Government.gdp_history`.
- **Fix**:
    - Defined `IWelfareRecipient` protocol (runtime checkable).
    - Encapsulated `gdp_history` mutation in `Government.record_gdp()`.
    - Updated `WelfareService` to use these abstractions.

## 2. Architectural Insights

### TransactionProcessor Synchronous Execution Pattern
- **Pattern**: When a System (like `InheritanceManager`) needs to perform a complex sequence of transactions where subsequent steps depend on the result (e.g. cash raised) of previous ones, it should use `transaction_processor.execute(state, [tx])` synchronously.
- **Benefit**: Maintains "Sacred Sequence" and centralization of transaction logic (in Handlers) while allowing dynamic workflows.
- **Observation**: `AgentLifecycleManager` captures the return values of these transactions for logging/reporting, ensuring visibility.

### Legacy Test Brittleness
- **Observation**: Several unit tests (`test_commerce_system.py`, `test_finance_department_bankruptcy.py`) were broken or outdated, checking for non-existent methods or incorrectly assuming data types (float vs Dict).
- **Action**: Patched strictly necessary tests to verify TD fixes, but a broader "Test Debt" cleanup is recommended.

## 3. Remaining Issues
- `FinanceDepartment.check_bankruptcy` logic seems to miss the "Brand Resilience" feature tested in `test_finance_department_bankruptcy.py`. This feature might have been lost in a previous refactor.
- `CommerceSystem` tests refer to `execute_consumption_and_leisure` which no longer exists.
