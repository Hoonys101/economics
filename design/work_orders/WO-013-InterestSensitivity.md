# Work Order: Phase 4.5 Interest Sensitivity

> **To**: Jules (Implementation Agent)
> **From**: Team Leader (Antigravity)
> **Priority**: High
> **Reference**: `design/specs/phase4_5_interest_sensitivity_spec.md`

## Task Description
Implement the **Monetary Transmission Mechanism** in the AI Decision Engine for households. This will make agents react to Central Bank interest rates by adjusting their consumption aggressiveness.

## Assignments

### 1. Decision Logic (Python)
- **File**: `simulation/decisions/ai_driven_household_engine.py`
- **Method**: 
    - Implement `adjust_consumption_for_interest_rate()` following the logic in the spec.
    - Integrate it into the `make_decisions()` consumption loop.
- **Goal**: Ant personalities must save more when rates are high; Debt-heavy agents must spend less when rates are high.

### 2. Personality Mapping
- Group `Personality.MISER` and `Personality.CONSERVATIVE` as **ANT** ($S=10.0$).
- Group `Personality.STATUS_SEEKER` and `Personality.IMPULSIVE` as **Grasshopper** ($S=2.5$).
- Default sensitivity = 5.0.

### 3. Verification
- Use `python scripts/iron_test.py` to verify the behavior.
- Add debug logging with prefix `MONETARY_TRANSMISSION |`.

## Success Criteria
- Consumption aggressiveness (`agg_buy`) responds dynamically to both `nominal_rate` and `expected_inflation`.
- DSR-based "panic" reduction triggers for agents with high debt.
