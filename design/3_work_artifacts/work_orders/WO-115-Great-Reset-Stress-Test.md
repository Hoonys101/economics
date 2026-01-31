# Work Order: - Great Reset Long-Run Verification

## 1. Context
- **Objective**: Verify the systemic stability of the new `SettlementSystem` and `FinanceSystem`.
- **Reference**: `design/HANDOVER_2026-01-23.md`

## 2. Tasks for Jules
1. **Develop Verification Script**:
 - Create `scripts/verify_great_reset_stability.py`.
 - The script should run a standard simulation for at least **1,000 ticks**.
2. **Monitoring**:
 - Monitor for "ATOMICITY_FAILURE" in logs.
 - Track the total money supply (M2). It must strictly follow the Zero-Sum principle except for explicitly defined creation/destruction events.
 - TrackGovernment Debt-to-GDP ratio.
3. **Report**:
 - Provide a summarized report on the long-term stability.
 - Highlight any "residual leaks" discovered.

## 3. Reporting Requirement
- Document any numerical drift or precision errors found in asset movements.
- Suggest tuning for fiscal parameters if debt spirals uncontrollably.
