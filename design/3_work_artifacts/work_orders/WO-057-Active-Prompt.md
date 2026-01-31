## Mission: Implement Deficit Spending for Government Stimulus

You are implementing **** to solve the Mass Starvation crisis by enabling the Government to spend beyond its assets (Deficit Spending).

## Context Files
| Role | File | Purpose |
|------|------|---------|
| **Destination** | simulation/agents/government.py | Modify provide_subsidy() to allow deficit spending |
| **Destination** | simulation/policies/smart_leviathan_policy.py | Increase budget_max for Emergency Mode |
| **Destination** | config.py | Add deficit spending config params |
| **Contract** | simulation/dtos.py | Reference for GovernmentStateDTO |
| **Spec** | design/work_orders/WO-057-Active.md | Full specification with pseudo-code |

## Tasks

### 1. Config Changes (config.py)
Add to the Phase 7 Adaptive Fiscal Policy section:
- DEFICIT_SPENDING_ENABLED = True
- DEFICIT_SPENDING_LIMIT_RATIO = 0.30
- EMERGENCY_BUDGET_MULTIPLIER_CAP = 2.0
- NORMAL_BUDGET_MULTIPLIER_CAP = 1.0

### 2. Government Agent (government.py)
Modify provide_subsidy() around line 266-310:
- After calculating effective_amount, check if assets are sufficient
- If NOT sufficient AND DEFICIT_SPENDING_ENABLED is True:
 - Calculate debt_limit = current_gdp * DEFICIT_SPENDING_LIMIT_RATIO
 - Allow payment if abs(projected_assets) is less than or equal to debt_limit
 - Log FISCAL_CLIFF_REACHED if limit exceeded
- Update self.total_debt = abs(self.assets) if self.assets is negative else 0

### 3. Smart Leviathan Policy (smart_leviathan_policy.py)
Modify decide() around line 84-101:
- Before applying budget limits, check for Emergency Condition:
 - gdp_growth_sma less than -0.05 OR unemployment_sma greater than 0.10
- If Emergency: use EMERGENCY_BUDGET_MULTIPLIER_CAP (2.0)
- Otherwise: use NORMAL_BUDGET_MULTIPLIER_CAP (1.0)

### 4. Unit Test (tests/test_government.py)
Add test_deficit_spending:
- Test normal payment (assets sufficient)
- Test deficit payment (assets insufficient but within limit)
- Test fiscal cliff (exceeds debt limit, should reject)

## Constraints
- DO NOT modify any interfaces or DTOs
- Preserve existing logging format
- Use getattr(self.config_module, PARAM, default) pattern

## Verification
Run: pytest tests/test_government.py -v -k deficit
Run: python scripts/iron_test.py --ticks 100

## Insight Reporting
If you find issues with GDP fluctuation causing unstable debt ceilings, report in communications/insights/.
