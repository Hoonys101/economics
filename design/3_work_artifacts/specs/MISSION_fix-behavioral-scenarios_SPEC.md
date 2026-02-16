# Mission Spec: Scenario & AI Behavior Fix

## Goal
Re-align breeding and survival override logic with current engine calibration.

## Identified Failures

### 1. Breeding Scenario D
- **Error**: `AssertionError: False is not true : Middle income agent should accept reproduction.`
- **Cause**: Economic calibration change. Manual calculation shows NPV is indeed negative (-304k), but test expects positive.
- **Fix**: Adjust `HouseholdAI.decide_reproduction` calibration or the test's `OPPORTUNITY_COST_FACTOR` patch to allow middle-income agents to reproduce in the "Golden Mean" scenario.

### 2. Survival Override
- **Error**: `AssertionError: assert 30.0 == 11.0` in `test_survival_override_triggered`.
- **Cause**: Pricing logic mismatch in `AIDrivenHouseholdDecisionEngine`.
- **Fix**: Verify why the bidding premium (0.1) resulted in 30.0 instead of 11.0. Check for unintended cost-plus or other overrides.

### 3. Animal Spirits
- **Error**: `AssertionError: assert 30.0 == 11.0` (Shared with above).

## Verification
- Run `pytest tests/integration/test_wo048_breeding.py`
- Run `pytest tests/unit/decisions/test_animal_spirits_phase2.py`
