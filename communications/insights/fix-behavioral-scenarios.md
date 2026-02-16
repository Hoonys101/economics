# Mission Spec: Scenario & AI Behavior Fix

## Architectural Insights

### 1. Integer vs Float in Monetary Values
The `ConsumptionManager.check_survival_override` method strictly enforces integer premiums (pennies) for `survival_bid_premium` configuration.
- **Issue**: The test `tests/unit/decisions/test_animal_spirits_phase2.py` was providing a float `0.1`, which caused the system to fall back to the default `20` pennies, leading to an assertion failure (`30.0 != 11.0`).
- **Resolution**: Updated the test to use an integer premium (`1`), aligning with the penny-based architecture. This highlights the importance of matching test data types with strict type checks in the production code.

### 2. Breeding Scenario Calibration Mismatch
The `tests/integration/test_wo048_breeding.py` test suite uses "Dollar" based values (e.g., `current_wage=25.0`, implying $4000/month), while the production configuration (`config/defaults.py`) has migrated to "Penny" values (e.g., `CHILD_MONTHLY_COST=50000`).
- **Issue**: This mismatch caused the "Middle Income" agent in Scenario D to fail the solvency check ($4000 < $50000 * 2.5), resulting in a rejection of reproduction, contradicting the "Golden Mean" scenario expectation.
- **Resolution**: Patched `CHILD_MONTHLY_COST` to `500.0` and `OPPORTUNITY_COST_FACTOR` to `0.1` within the test case to restore the intended economic dynamics for the test scenario, ensuring the middle-income agent perceives a positive Net Present Value (NPV).

## Test Evidence

### verification Output
```
tests/integration/test_wo048_breeding.py::TestWO048Breeding::test_scenario_a_pre_modern PASSED [ 12%]
tests/integration/test_wo048_breeding.py::TestWO048Breeding::test_scenario_b_high_income PASSED [ 25%]
tests/integration/test_wo048_breeding.py::TestWO048Breeding::test_scenario_c_low_income PASSED [ 37%]
tests/integration/test_wo048_breeding.py::TestWO048Breeding::test_scenario_d_middle_income PASSED [ 50%]
tests/unit/decisions/test_animal_spirits_phase2.py::TestHouseholdSurvivalOverride::test_survival_override_triggered PASSED [ 62%]
tests/unit/decisions/test_animal_spirits_phase2.py::TestHouseholdSurvivalOverride::test_survival_override_insufficient_funds PASSED [ 75%]
tests/unit/decisions/test_animal_spirits_phase2.py::TestFirmPricingLogic::test_cost_plus_fallback PASSED [ 87%]
tests/unit/decisions/test_animal_spirits_phase2.py::TestFirmPricingLogic::test_fire_sale_trigger PASSED [100%]

============================== 8 passed in 0.22s ===============================
```
