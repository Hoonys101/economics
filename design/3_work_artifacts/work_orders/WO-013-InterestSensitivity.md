# Work Order: Phase 4.5 Organic Interest Sensitivity

> **To**: Jules (Implementation Agent)
> **From**: Team Leader (Antigravity)
> **Priority**: Critical
> **Reference**: `design/specs/phase4_5_interest_sensitivity_spec.md` (REVISED)

## Task Description
Implement the **3-Pillar Utility Competition Model**. This makes agents' internal decisions emergent and based on their core DNA.

## Assignments

### 1. DNA Mapping
Assign preference weights based on personality in `AIDrivenHouseholdDecisionEngine`:
- **MISER/CONSERVATIVE**: High `preference_asset` (1.5), Low `preference_social` (0.5).
- **STATUS_SEEKER/IMPULSIVE**: High `preference_social` (1.5), Low `preference_asset` (0.3).
- **NEUTRAL**: Balanced (1.0 each).

### 2. Decision Logic
- Calculate $U_{save}$, $U_{social}$, and $U_{growth}$ for each decision.
- In `make_decisions`, compare these utilities to determine `agg_buy`.
- Use the ratio $U_{consume} / U_{save}$ to attenuate or boost aggressiveness.
- Ensure the **DSR Wall** (0.4) remains as a hard liquidity barrier.

### 3. DSR Wall
- Implement the DSR-based liquidity constraint (DSR > 0.4 -> 50% reduction in aggressiveness).

## Verification
- Run `python scripts/iron_test.py`.
- Log the ROI comparison: `MONETARY_TRANS | SavingROI: 1.12 vs ConsROI: 0.95 -> Attenuating`.

## Success Criteria
- Agents reduce consumption "voluntarily" because saving is more attractive, not because of a hard-coded command.
- Inflation effectively slows down aggregate demand through this micro-level decision change.
