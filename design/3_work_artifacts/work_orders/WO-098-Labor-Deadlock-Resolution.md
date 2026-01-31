# Work Order Diagnostic Investigation of Economic Deadlock

## 1. Objective
Identify the root cause of why the "Great Harvest" (Phase 23) simulation fails (Population Crash, Zero Tech Adoption) and verify the solution.

## 2. Mandatory Diagnostic Phase (Hypothesis & Verification)
Jules must not start with a "Fix". Jules must start with a "Diagnostic".

### Hypothesis A: Labor Market Deadlock
**Hypothesis**: Rule-based households skip labor participation when they have high survival needs but no cash, leading to a permanent poverty trap.
**Verification**: Check `simulation/decisions/rule_based_household_engine.py` line 110. Run a 10-tick micro-simulation and log `Order` generation for hungry households with 0 assets.

### Hypothesis B: Inconsistent Market IDs
**Hypothesis**: Firms are buying `"labor_market"` while households are selling `"labor"`, or vice versa.
**Verification**: Compare `rule_based_firm_engine.py` and `rule_based_household_engine.py`.

### Hypothesis C: Tech Diffusion Lag
**Hypothesis**: `TECH_AGRI_CHEM_01` is unlocked but not adopted due to low sensitivity or HCI (Human Capital Index) calculation issues.
**Verification**: Run `scripts/debug_phase23_tech.py`.

## 3. Tasks
1. **Analyze**: Examine the failure report from (`reports/WO-097_HARVEST_REPORT.md` available in git history/last run) and the current code.
2. **Experiment**: Create a small diagnostic script to prove one of the hypotheses above.
3. **Fix & Re-balance**: Based on proven diagnostics, apply fixes.
4. **Validation**: Run `scripts/verify_phase23_harvest.py` and ensure the verdict is **ESCAPE VELOCITY ACHIEVED**.

## 4. Success Criteria
- [ ] Documented evidence of the root cause.
- [ ] Population > 300.
- [ ] Engel Coefficient < 0.15.
- [ ] Harvest Report: **SUCCESS**.
