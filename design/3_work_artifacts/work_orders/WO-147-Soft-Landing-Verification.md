# Work Order: - Soft Landing Verification Suite

**Phase:** 28 (Structural Stabilization)
**Priority:** HIGH
**Prerequisite:** ,

## 1. Objective
Create a new, dedicated verification suite to prove the effectiveness of the fiscal and monetary stabilizers. This script will replace deprecated scenario tests and become the new benchmark for macroeconomic stability.

## 2. Implementation Plan

### Task A: Create Verification Script
1. Create a new script: `scripts/verify_soft_landing.py`.

### Task B: Implement Baseline Scenario
1. Add logic to run a 1000-tick simulation with the new stabilizers **disabled**. This should be controlled by a configuration flag.
2. Record and calculate key metrics: GDP, inflation, unemployment, Gini coefficient, and their volatility (standard deviation).
3. Count the number and duration of recessions (defined as >= 2 consecutive ticks of negative GDP growth).
4. Save the aggregated results to `reports/soft_landing_baseline.json`.

### Task C: Implement Stabilizer Scenario
1. Add logic to run the same 1000-tick simulation with the new stabilizers **enabled**.
2. Record and calculate the same metrics as the baseline.
3. Save the aggregated results to `reports/soft_landing_stabilized.json`.

### Task D: Implement Verification and Reporting
1. Add assertion logic to the script that compares the two scenarios.
2. The script should generate comparison plots, such as `gdp_volatility.png` and `inflation_stability.png`, to visualize the difference.

## 3. Technical Constraints

- **Test Suite Transition**: This script explicitly marks the deprecation of old scenario tests (e.g., `verify_golden_age.py`).
- **Configurability**: The script must be easily configurable to toggle the stabilizers on or off for the two separate runs.

## 4. Success Sign-off Criteria

- [ ] **Script Execution**: The `scripts/verify_soft_landing.py` script runs to completion without errors for both scenarios.
- [ ] **Artifact Generation**: The script successfully generates all specified output files.
- [ ] **Verification Pass**: The final assertions within the script pass, confirming reduced volatility and recessionary periods.
