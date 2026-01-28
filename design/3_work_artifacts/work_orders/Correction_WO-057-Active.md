## 🛑 Correction Required: Strict Spec Adherence (WO-057-Active)

Your implementation of **WO-057-Active** is partially complete but missing critical components defined in the specification (`design/work_orders/WO-057-Active.md`). 

Please address the following omissions immediately:

### 1. Missing Configuration (config.py)
Add the following parameters to the 'Phase 7: Adaptive Fiscal Policy' section:
- DEFICIT_SPENDING_ENABLED = True
- DEFICIT_SPENDING_LIMIT_RATIO = 0.30
- EMERGENCY_BUDGET_MULTIPLIER_CAP = 2.0
- NORMAL_BUDGET_MULTIPLIER_CAP = 1.0

### 2. Missing Debt Ceiling Logic (government.py)
In provide_subsidy(), you removed the asset check but failed to implement the **Debt Limit**.
- Use current_gdp * config.DEFICIT_SPENDING_LIMIT_RATIO to calculate the limit.
- If abs(projected_assets) > debt_limit, you MUST reject the payment and log FISCAL_CLIFF_REACHED.
- Update self.total_debt value based on abs(self.assets) if negative.

### 3. Missing Emergency AI Levers (smart_leviathan_policy.py)
In decide(), you must implement the **Emergency Mode** for the budget_max cap:
- Check for crisis condition: gdp_growth_sma < -0.05 OR unemployment_sma > 0.10.
- Use EMERGENCY_BUDGET_MULTIPLIER_CAP (2.0) during crisis, otherwise NORMAL_BUDGET_MULTIPLIER_CAP (1.0).

### 4. Missing Unit Tests (tests/test_government.py)
Add test_deficit_spending to verify functionality, including the debt limit rejection.

Please update your PR branch accordingly.
