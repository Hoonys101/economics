# Work Order: Phase 7 - Adaptive Fiscal Policy (Government)

## 🎯 Objective
Implement a counter-cyclical adaptive fiscal policy in the `Government` class. The government should now adjust tax rates and spending based on the **Output Gap** (GDP trend) and respect a **Debt Ceiling**.

## 📂 Reference
- Spec: `design/specs/adaptive_fiscal_policy_spec.md`

## 🛠️ Tasks

### Task A: Update Config
File: `config.py`
Add the following constants:
- `FISCAL_SENSITIVITY_ALPHA`: 0.5
- `POTENTIAL_GDP_WINDOW`: 50
- `TAX_RATE_MIN`: 0.05
- `TAX_RATE_MAX`: 0.30
- `TAX_RATE_BASE`: 0.10
- `DEBT_CEILING_RATIO`: 1.0
- `FISCAL_STANCE_EXPANSION_THRESHOLD`: 0.025
- `FISCAL_STANCE_CONTRACTION_THRESHOLD`: -0.025

### Task B: Modify Government Class
File: `simulation/agents/government.py`
1.  **Initialization**: Add `potential_gdp`, `gdp_ema`, `fiscal_stance`, `effective_tax_rate`, and `total_debt` fields.
2.  **Implementation**: Add `adjust_fiscal_policy(self, current_gdp)` method.
    - Calculate `potential_gdp` using EMA logic.
    - Calculate `output_gap` and `fiscal_stance`.
    - Adjust `effective_tax_rate` based on `fiscal_stance`.
3.  **Integration**:
    - Update `run_welfare_check` to call `adjust_fiscal_policy`.
    - Update `calculate_income_tax` to use `self.effective_tax_rate`.
    - Update `provide_subsidy` to include the **Debt Ceiling** check and track `total_debt`.

### Task C: Verification
Create `tests/test_fiscal_policy.py`:
1.  Verify tax rate decreases when GDP drops (Expansion).
2.  Verify tax rate increases when GDP rises (Contraction).
3.  Verify subsidy is blocked when `debt/GDP > 1.0`.
4.  Verify `potential_gdp` (EMA) calculation accuracy.

## 🚀 Deliverables
- Modified `simulation/agents/government.py`
- Modified `config.py`
- New `tests/test_fiscal_policy.py`
- Report test success.
