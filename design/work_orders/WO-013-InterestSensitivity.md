# Work Order: Phase 4.5 Organic Interest Sensitivity

> **To**: Jules (Implementation Agent)
> **From**: Team Leader (Antigravity)
> **Priority**: Critical
> **Reference**: `design/specs/phase4_5_interest_sensitivity_spec.md` (REVISED)

## Task Description
Implement the **Organic Monetary Transmission Mechanism**. The previous design was rejected for being "too hard-coded." We are moving to a **Utility Competition Model** where saving is treated as a competing product.

## Assignments

### 1. ROI Calculation
- Implement `calculate_saving_roi` and `calculate_consumption_roi`.
- Use **Time Preference** based on personality:
    - ANT group (Time Pref = 1.2)
    - GRASSHOPPER group (Time Pref = 0.8)

### 2. Emerging Behavior
- In `make_decisions`, compare the ROIs.
- If $ROI_{savings} > ROI_{consumption}$, attenuate the `agg_buy` using the ratio $(U_c / U_s)$.
- This ensures that agents only consume if the current need satisfaction is greater than the future value of the money and its interest.

### 3. DSR Wall
- Implement the DSR-based liquidity constraint (DSR > 0.4 -> 50% reduction in aggressiveness).

## Verification
- Run `python scripts/iron_test.py`.
- Log the ROI comparison: `MONETARY_TRANS | SavingROI: 1.12 vs ConsROI: 0.95 -> Attenuating`.

## Success Criteria
- Agents reduce consumption "voluntarily" because saving is more attractive, not because of a hard-coded command.
- Inflation effectively slows down aggregate demand through this micro-level decision change.
