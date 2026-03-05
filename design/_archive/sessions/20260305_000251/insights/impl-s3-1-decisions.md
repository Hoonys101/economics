# Insight Report: Decisions Mocks Refactor

## 1. Architectural Insights
The refactoring effort addressed mock object drift and cyclic references causing memory leak risks in testing, particularly concerning `tests/unit/decisions/conftest.py`. The legacy God Class firm structure often had deeply nested mocks without any `spec=RealClass` specifications, leading to silent failures where tests evaluated on non-existent properties.
- Introduced the `ICleanable` protocol into `modules/system/api.py` and implemented its cleanup behavior in `CorporateManager`.
- Adjusted all nested mock creations in `conftest.py` (e.g., `FinanceState`, `ProductionState`) to adhere to `spec=RealClass`, ensuring that missing properties correctly raise `AttributeError`.
- Reset mocks upon fixture teardown to explicitly break circular reference chains (like those involving `system2_planner`).

## 2. Regression Analysis
During the process of converting pure `Mock()` objects into domain-specific mocks (like `Mock(spec=FinanceStateDTO)` and `Mock(spec=FinanceState)`), we noted properties previously missing from tests but expected during execution. Properties like `marketing_budget_pennies` vs. `marketing_budget` and correct initialization of `revenue_this_turn` as dictionaries rather than floats had to be adjusted inside `create_firm_state_dto` to match reality, correcting years of technical debt and mock drift in legacy tests. The entire suite, particularly `tests/unit/decisions/`, now relies on strictly verified objects and attributes, preventing future feature breakages hiding behind unverified mocks.

## 3. Test Evidence
```text
tests/unit/decisions/test_animal_spirits_phase2.py::TestHouseholdSurvivalOverride::test_survival_override_triggered PASSED [  5%]
tests/unit/decisions/test_animal_spirits_phase2.py::TestHouseholdSurvivalOverride::test_survival_override_insufficient_funds PASSED [ 11%]
tests/unit/decisions/test_animal_spirits_phase2.py::TestFirmPricingLogic::test_cost_plus_fallback PASSED [ 16%]
tests/unit/decisions/test_animal_spirits_phase2.py::TestFirmPricingLogic::test_fire_sale_trigger PASSED [ 22%]
tests/unit/decisions/test_finance_rules.py::TestFinanceRules::test_rd_investment PASSED [ 27%]
tests/unit/decisions/test_finance_rules.py::TestFinanceRules::test_capex_investment PASSED [ 33%]
tests/unit/decisions/test_finance_rules.py::TestFinanceRules::test_dividend_setting PASSED [ 38%]
tests/unit/decisions/test_household_engine_refactor.py::test_engine_execution_parity_smoke PASSED [ 44%]
tests/unit/decisions/test_household_integration_new.py::TestHouseholdIntegrationNew::test_make_decision_integration PASSED [ 50%]
tests/unit/decisions/test_hr_rules.py::TestHRRules::test_make_decisions_hires_labor PASSED [ 55%]
tests/unit/decisions/test_hr_rules.py::TestHRRules::test_make_decisions_does_not_hire_when_full PASSED [ 61%]
tests/unit/decisions/test_hr_rules.py::TestHRRules::test_make_decisions_fires_excess_labor PASSED [ 66%]
tests/unit/decisions/test_production_rules.py::TestProductionRules::test_initialization PASSED [ 72%]
tests/unit/decisions/test_production_rules.py::TestProductionRules::test_make_decisions_overstock_reduces_target PASSED [ 77%]
tests/unit/decisions/test_production_rules.py::TestProductionRules::test_make_decisions_understock_increases_target PASSED [ 83%]
tests/unit/decisions/test_production_rules.py::TestProductionRules::test_make_decisions_target_within_bounds_no_change PASSED [ 88%]
tests/unit/decisions/test_production_rules.py::TestProductionRules::test_make_decisions_target_min_max_bounds PASSED [ 94%]
tests/unit/decisions/test_sales_rules.py::TestSalesRules::test_sales_aggressiveness_impact_on_price PASSED [100%]

======================== 18 passed, 1 warning in 0.38s =========================
```
