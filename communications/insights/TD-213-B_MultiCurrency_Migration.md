# Insights Report: Multi-Currency Migration & Fixes [TD-213-B, TD-240]

## 1. Technical Debt & Issues Identified

### TD-240: Altman Z Score Multi-Currency Incompatibility
The `calculate_altman_z_score` method in `FinanceDepartment` was designed for a single-currency world.
- **Issue**: It only retrieved the balance for `primary_currency`, ignoring all other currency holdings in the `total_assets` calculation.
- **Risk**: This leads to a severely underestimated Z-score for firms holding significant foreign reserves, potentially triggering false bankruptcy flags.
- **Fix**: The method will be updated to accept `exchange_rates` and sum all currency balances (converted to primary) for the `total_assets` calculation.

### TD-233: Law of Demeter Violation in Profit Distribution
Direct access to `household.portfolio.to_legacy_dict()` exposes internal implementation details of the `Portfolio` class.
- **Fix**: Implemented `get_stock_quantity(firm_id)` on the `Portfolio` class and updated `FinanceDepartment` to use this accessor.

### TD-213-B: Missing Metrics Updates
- **Issue**: `FinanceDepartment.last_revenue` was not being updated at the end of the turn, causing it to remain 0.0 or stale.
- **Fix**: Added logic to update `last_revenue` (sum of all currency revenues converted to primary) before resetting turn counters.

## 2. Refactoring Summary
- **Portfolio**: Added `get_stock_quantity` method.
- **FinanceDepartment**:
    - Updated `calculate_altman_z_score` to be currency-aware.
    - Updated `process_profit_distribution` to respect Law of Demeter.
    - Added `last_revenue` update logic.

## 3. Verification
- `reproduce_td240.py` (adapted) will verify Z-score calculation with multi-currency wallets.
- `tests/unit/test_firms.py` should pass.
