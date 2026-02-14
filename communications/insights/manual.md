# Manual Insight Report

## Architectural Insights

### 1. Restoration of Sales ROI Logic
The "Dynamic Marketing Budget" feature, where marketing spend rate adjusts based on ROI (Return On Investment), was identified as missing from the stateless `SalesEngine`.
- **Logic Restoration**: The logic was reintroduced into `SalesEngine.adjust_marketing_budget`. It now calculates ROI using `(revenue_this_turn - last_revenue) / last_marketing_spend`.
- **State Updates**: `Firm` (the state orchestrator) now passes `last_revenue` and `last_marketing_spend` from `FinanceState` to the engine, and updates `SalesState.marketing_budget_rate` based on the engine's return value.
- **DTO Update**: `MarketingAdjustmentResultDTO` was extended to include `new_marketing_rate`.
- **Testing**: `tests/unit/test_marketing_roi.py` was restored by removing `@unittest.skip`, updating attribute names to match the "Pennies Migration" (e.g., `last_revenue_pennies`), and verifying the integration of `Firm` and `SalesEngine`.

### 2. Integration Test Mock Hardening
The regression in `tests/integration/mission_int_02_stress_test.py` highlighted a mismatch between the `CommandService` requirements and the test mocks.
- **Interface Compliance**: `MockSettlementSystem` was updated to implement `get_account_holders(bank_id)`, mirroring the reverse-index lookup required by `FORCE_WITHDRAW_ALL` commands.
- **Strict Mocking**: The `registry` mock was updated to use `create_autospec(IGlobalRegistry, instance=True)` instead of `MagicMock(spec=...)`. This ensures stricter adherence to the Protocol definition, preventing future interface drift from going unnoticed in tests.

### 3. Test Suite Status
- **Targeted Fixes**: `tests/unit/test_marketing_roi.py` and `tests/integration/mission_int_02_stress_test.py` are now passing.
- **Clarification on `test_household_ai.py`**: The mission mandate requested analysis of skipped tests in `tests/unit/test_household_ai.py`. Upon inspection, **no tests were found skipped** in this file (all passed). It is likely the instruction referred to `tests/unit/decisions/test_household_integration_new.py` (which contains skips) or was based on outdated information. Given the strict scope of "Restore behavioral tests... in `test_marketing_roi.py`, `test_household_ai.py`", and finding no skips in the latter, no changes were made to `test_household_ai.py` to avoid regressions in working code.

## Test Evidence

### Unit Tests (`tests/unit/test_marketing_roi.py`)
```
tests/unit/test_marketing_roi.py::TestMarketingROI::test_budget_decrease_on_low_efficiency PASSED [ 25%]
tests/unit/test_marketing_roi.py::TestMarketingROI::test_budget_increase_on_high_efficiency PASSED [ 50%]
tests/unit/test_marketing_roi.py::TestMarketingROI::test_budget_stable_on_saturation PASSED [ 75%]
tests/unit/test_marketing_roi.py::TestMarketingROI::test_first_tick_skip PASSED [100%]
```

### Integration Tests (`tests/integration/mission_int_02_stress_test.py`)
```
tests/integration/mission_int_02_stress_test.py::test_hyperinflation_scenario PASSED [ 25%]
tests/integration/mission_int_02_stress_test.py::test_bank_run_scenario PASSED [ 50%]
tests/integration/mission_int_02_stress_test.py::test_inventory_destruction_scenario PASSED [ 75%]
tests/integration/mission_int_02_stress_test.py::test_parameter_rollback PASSED [100%]
```
