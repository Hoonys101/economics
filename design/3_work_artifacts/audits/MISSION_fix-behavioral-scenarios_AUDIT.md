# Mission Report: fix-behavioral-scenarios

## Executive Summary
The breeding logic in `HouseholdAI` is currently calibrated such that middle-income agents reject reproduction (Negative NPV), causing `test_scenario_d_middle_income` to fail. The survival override logic, while tested, produces a price mismatch (30.0 vs 11.0) according to the spec, though the source code for the decision engine handles is not provided for verification.

## Detailed Analysis

### 1. Breeding Scenario D (Middle Income Reproduction)
- **Status**: ❌ Fix Missing / Calibration Issue Confirmed
- **Evidence**: 
  - `simulation\ai\household_ai.py:L220-L245`: The `decide_reproduction` method calculates NPV.
  - `tests\integration\test_wo048_breeding.py:L90-L96`: The test documents the manual calculation showing a massive deficit (Cost 600k vs Benefit 296k) for a middle-income agent (Wage 25.0).
- **Notes**: The current default `OPPORTUNITY_COST_FACTOR` (0.5) and `CHILD_EMOTIONAL_VALUE_BASE` (200,000) result in a Net Present Value of -304,000. The test expects `True` (Positive NPV), but the code mathematically guarantees `False` under current defaults.

### 2. Survival Override & Animal Spirits
- **Status**: ❌ Fix Missing / Verification blocked
- **Evidence**: 
  - `tests\unit\decisions\test_animal_spirits_phase2.py:L39-L43`: The test `test_survival_override_triggered` expects a price of 11.0 (`10.0 * 1.1`).
  - `design\3_work_artifacts\specs\MISSION_fix-behavioral-scenarios_SPEC.md`: Reports an `AssertionError: assert 30.0 == 11.0`.
- **Notes**: The source code for `AIDrivenHouseholdDecisionEngine` (where the pricing logic likely resides) is not present in the context. The `HouseholdAI` class provided (`simulation\ai\household_ai.py`) handles `decide_action_vector` but does not appear to contain the specific limit price logic for the survival override order, implying the bug lies in the decision engine or interaction logic not visible here.

## Risk Assessment
- **Population Collapse**: The current breeding calibration prevents middle-class agents from reproducing. If this demographic is the primary driver of population stability, the simulation will face extinction events.
- **Test Integrity**: The survival override test expects a 10% premium, but the reported actual value (30.0) suggests a 200% premium or a hardcoded fallback is interfering.

## Conclusion
The breeding logic requires immediate re-calibration (lowering opportunity cost or increasing emotional utility) to satisfy Scenario D. The survival override logic source must be located to diagnose the 30.0 price artifact.