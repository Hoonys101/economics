# Technical Report: Post-Merge Stabilization Audit (Wave 3.3/4.0)

## Executive Summary
The recent merge of Wave 3.3 (Monetary Hardening/Pennies) and Wave 4.0 (Componentization/DTO Purity) has introduced critical regression in financial data consistency and test integrity. The audit reveals a mismatch in DTO schemas leading to `TypeError` in household tests and a unit mismatch (Pennies vs. Dollars) causing a `0 == 10.0` assertion failure in the economic indicator pipeline.

## Detailed Analysis

### 1. TypeError in Household Tests (`EconStateDTO`)
- **Status**: ❌ Missing Fields in Test Fixture
- **Evidence**: `modules\household\dtos.py:L40-85` vs `tests\unit\modules\household\test_consumption_manager.py:L26-72`
- **Notes**: Wave 4.0 added `consumption_expenditure_this_tick_pennies` and `food_expenditure_this_tick_pennies` to the mandatory fields of `EconStateDTO`. The test fixture in `test_consumption_manager.py` was not updated to include these, causing `TypeError: __init__() missing 2 required positional arguments` when instantiating the DTO in the `econ_state` fixture.

### 2. Economic Indicator Failure (`0 == 10.0`)
- **Status**: ❌ Unit Mismatch (Penny Drift)
- **Evidence**: 
  - `simulation\metrics\economic_tracker.py:L248-251` (Implementation)
  - `tests\integration\scenarios\diagnosis\test_indicator_pipeline.py:L14-23` (Test)
- **Notes**: 
  - The test sets `simple_household._econ_state.current_consumption = 10.0` (Legacy float/dollar field).
  - The `EconomicIndicatorTracker` now aggregates `h._econ_state.consumption_expenditure_this_tick_pennies` (New Wave 3.3 int/penny field).
  - Since the test does not update the `_pennies` field, the tracker reports `0`, leading to the failure `assert 0 == 10.0`.

### 3. DTO Callsite Consistency (Schema Lag)
- **Status**: ⚠️ Partial Implementation
- **Evidence**: 
  - `simulation\dtos\api.py:L43-65` defines `EconomicIndicatorData` where `total_consumption` is `Optional[int]`.
  - `simulation\metrics\economic_tracker.py:L274-279` converts `total_labor_income` to dollars (`/ 100.0`) but leaves `total_consumption` as pennies.
- **Risk**: The `AnalyticsSystem` aggregates these mixed-unit indicators into a single database record, leading to distorted macro-economic analysis (e.g., Labor Share calculation using Dollars vs. Production in Pennies).

## Stabilization Spec (Phase 4.1 Fix)

### Step 1: DTO Schema Synchronization
1.  **Update `test_consumption_manager.py`**: Add missing fields to `econ_state` fixture.
    ```python
    # tests/unit/modules/household/test_consumption_manager.py
    consumption_expenditure_this_tick_pennies=0,
    food_expenditure_this_tick_pennies=0
    ```
2.  **Harden `EconStateDTO` Defaults**: Consider providing default `0` for transient tracking fields to prevent future `TypeError` during test expansion.

### Step 2: Financial Unit Normalization (The "Dollar-Reporting" Rule)
To maintain architectural purity while supporting human-readable analytics, the following rule is established:
- **Internal State**: All `_pennies` fields MUST be `int`.
- **Reporting DTOs**: `EconomicIndicatorTracker` MUST convert all `pennies` to `dollars` (float) before storing in `self.metrics` for consistency with `avg_goods_price` and `avg_wage`.

1.  **Fix `EconomicIndicatorTracker.track`**:
    ```python
    # Correcting L251 & L253
    record["total_consumption"] = total_consumption_pennies / 100.0
    record["total_food_consumption"] = total_food_consumption_pennies / 100.0
    ```

### Step 3: Test Case Correction
1.  **Update `test_indicator_pipeline.py`**:
    - The test must update `consumption_expenditure_this_tick_pennies` instead of (or in addition to) `current_consumption`.
    - **Note**: Ensure the expected value matches the unit (if the tracker is fixed to dollars, the expectation of `10.0` is correct).

## Risk Assessment
- **Zero-Sum Integrity**: If `AnalyticsSystem` (L127-145) reads `total_consumption` as dollars but expects pennies, the M2 Supply calculations will fail audit.
- **Technical Debt**: `TD-TRANS-INT-SCHEMA` (Schema Lag) remains **High Priority** as `simulation\models.py` still uses `float` price, creating a translation layer overhead.

## Conclusion
The merge succeeded in establishing the DTO structure but failed in data-type synchronization across boundaries. Immediate action is required to fix the test fixtures and enforce the **Dollar-Reporting** rule in the `EconomicIndicatorTracker` to resolve the pipeline breakage.

**Insight Report Generated**: `communications/insights/spec-post-merge-stabilization.md` (Draft ready for filesystem commit by Developer Agent).