# WO-MYPY-LOGIC-B5-ANALYTICS: Analytics & DB Logic Hardening

## 1. Architectural Insights
The "Penny Standard" migration revealed a critical mismatch in the Analytics layer (`simulation/metrics`), where legacy code treated `Household.assets` or `_econ_state.assets` as a scalar value (float/int), whereas in the multi-currency architecture, it is a `Dict[CurrencyCode, int]`.

This mismatch caused runtime errors in:
- `EconomicIndicatorTracker`: Summing assets without conversion or dictionary handling.
- `StockMarketTracker`: Arithmetic operations (sum/division) on dictionaries.
- `InequalityTracker`: Sorting households by a dictionary, which raises `TypeError`.

**Decision:**
- Adopted `Household.total_wealth` (property) as the standard scalar metric for wealth in analytics. This property sums all currency balances (1:1 basis currently, but scalable).
- Updated `EconomicIndicatorTracker` to explicitly type `deque` buffers as `deque[float]` to satisfy Mypy strictness.
- Enforced `float` casting for reporting metrics while preserving `int` precision for internal wallet dictionaries.

## 2. Regression Analysis
- **Broken Tests:** None initially, as there were no specific unit tests for `StockMarketTracker` arithmetic or `InequalityTracker` sorting logic.
- **New Failures:** Initial runs of new tests failed due to strict `MagicMock` vs `int` comparisons. This highlighted that `total_firm_assets` calculation in `EconomicIndicatorTracker` was propagating Mocks because `Firm.get_financial_snapshot` was mocked to return a Mock instead of a `dict`, and `Firm.get_balance` was not mocked.
- **Fixes:**
    - Refactored `simulation/metrics/*.py` to handle `Dict` returns from `get_all_items()` safely.
    - Updated `StockTracker` and `InequalityTracker` to use `total_wealth` (int) instead of `assets` (dict).
    - Created `tests/unit/test_metrics_hardening.py` with proper `MagicMock` configuration to verify the fixes.

## 3. Test Evidence
The new test suite `tests/unit/test_metrics_hardening.py` passes 100%, covering:
- `EconomicIndicatorTracker.track`: Verifies correct aggregation of household/firm assets and consumption.
- `StockMarketTracker`: Verifies "Penny Standard" arithmetic for personality group statistics.
- `InequalityTracker`: Verifies quintile assignment and Gini calculation using `total_wealth`.

```
tests/unit/test_metrics_hardening.py::TestMetricsHardening::test_economic_tracker_track PASSED [ 33%]
tests/unit/test_metrics_hardening.py::TestMetricsHardening::test_inequality_tracker_quintiles PASSED [ 66%]
tests/unit/test_metrics_hardening.py::TestMetricsHardening::test_stock_tracker_arithmetic PASSED [100%]
```

Legacy tests also pass:
```
tests/unit/test_watchtower_hardening.py::TestWatchtowerHardening::test_repo_birth_counts PASSED [ 50%]
tests/unit/test_watchtower_hardening.py::TestWatchtowerHardening::test_tracker_sma_logic PASSED [100%]
```
