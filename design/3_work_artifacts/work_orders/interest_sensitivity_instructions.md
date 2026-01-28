# Work Order: Phase 4.5 Interest Sensitivity (The Missing Link)

## 🎯 Objective
Restore the "Monetary Transmission Mechanism" by linking Interest Rates to Household Consumption/Savings decisions.

## 📂 Reference
- Spec: `design/specs/interest_sensitivity_spec.md` (Read this first!)

## 🛠️ Tasks

### Task A: Core Logic Implementation (Priority)
1.  **Config Update**: Add constants to `config.py`.
    ```python
    NEUTRAL_REAL_RATE = 0.02
    DSR_CRITICAL_THRESHOLD = 0.4
    INTEREST_SENSITIVITY_ANT = 5.0
    INTEREST_SENSITIVITY_GRASSHOPPER = 1.0
    ```
2.  **Engine Logic**: Modify `AIDrivenHouseholdDecisionEngine.make_decisions`.
    *   Calculate **Subjective Real Rate** ($i - \pi^e$).
    *   Calculate **Savings Incentive** (Substitution Effect).
    *   Calculate **Debt Penalty** (Income Effect / DSR check).
    *   Apply `(1 - Incentive - Penalty)` modifier to `consumption_aggressiveness`.
    *   *Important*: Do NOT reduce consumption if `survival_need` > `MASLOW_SURVIVAL_THRESHOLD`.

### Task B: Verification Script
1.  Create `tests/verify_monetary_transmission.py`.
2.  **Scenario**:
    *   Initialize simulation.
    *   Force central bank rate to **10%** (High Rate Shock).
    *   Run 50 ticks.
    *   Assert that `Household.consumption` decreases compared to baseline (Rate 2%).
    *   Assert that `Ant` type households reduce consumption MORE than `Grasshopper` types (unless Grasshoppers are debt-burdened).

## 🚀 Deliverables
- Modified `config.py`
- Modified `simulation/decisions/ai_driven_household_engine.py` (Search for "Missing Link" comment)
- New `tests/verify_monetary_transmission.py`
- Run the verification script and report results.
