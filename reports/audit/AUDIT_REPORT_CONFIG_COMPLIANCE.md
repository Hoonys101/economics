# AUDIT_REPORT_CONFIG_COMPLIANCE (v1.0)

**Objective**: Verify the externalization level of the codebase to identify hardcoded magic numbers, unused configurations, and the blast radius of config changes.

**SoC Boundary**: This audit only covers 'Configuration Hygiene' (parameter externalization, magic numbers, dead config, blast radius, default drift).

## 1. Executive Summary
- **Total Config Keys Analyzed:** 916
- **Magic Numbers Found:** 164
- **Dead Configs:** 501
- **High Blast Radius Configs (>10 locations):** 4
- **Default Drifts Detected:** 484

## 2. Magic Number Analysis
Found potentially hardcoded numbers in business logic that should be externalized (Top 20):
- `simulation/engine.py:272:base_rate = 0.05`
- `simulation/models.py:103:estimated_value: int = 10000  # Changed from float to int (pennies)`
- `simulation/models.py:136:observability: float = 0.5`
- `simulation/bank.py:32:_DEFAULT_INITIAL_BASE_ANNUAL_RATE = 0.03`
- `simulation/loan_market.py:66:max_ltv = 0.8`
- `simulation/loan_market.py:67:max_dti = 0.43`
- `simulation/loan_market.py:234:interest_rate = 0.05`
- `simulation/firms.py:1552:if productivity_factor <= 0: needed_labor = 999999.0`
- `simulation/firms.py:1615:sensitivity = 0.1`
- `simulation/firms.py:1836:corp_tax_rate = 0.2`
- `simulation/firms.py:1848:cost_per_point = 10000 # 10000 pennies = 100 credits.`
- `simulation/core_agents.py:298:self._social_state.trust_score = 0.5`
- `simulation/policies/taylor_rule_policy.py:47:neutral_rate = 0.02`
- `simulation/policies/adaptive_gov_policy.py:69:welfare_min, welfare_max = 0.1, 2.0`
- `simulation/policies/adaptive_gov_policy.py:70:tax_min, tax_max = 0.05, 0.6`
- `simulation/factories/agent_factory.py:177:mutation_range = 0.1`
- `simulation/factories/household_factory.py:294:mutation_range = 0.1`
- `simulation/decisions/portfolio_manager.py:12:CONST_INFLATION_TARGET = 0.02`
- `simulation/decisions/portfolio_manager.py:112:# Sigma_Equity ~= 0.2 (20% Volatility - assumption)`
- `simulation/decisions/portfolio_manager.py:113:sigma_equity_sq = 0.2 ** 2  # 0.04`
- *... and 144 more*

## 3. Dead Config Analysis
The following configuration keys are defined in YAML/DTOs/Constants but not referenced in code (Top 20):
- `population`
- `bankruptcy_rate_max`
- `valuation_modifier_base`
- `predicted_reward`
- `household_stockpiling_bonus_factor`
- `technology_bonus`
- `gdp_growth_rate`
- `policy_bonus_factor`
- `household_asset_price_multiplier`
- `labor_need`
- `orders`
- `satisfaction`
- `firm_pre_states`
- `macro_context`
- `liquidity_ratio_max`
- `unnamed_child_mortality_rate`
- `tfp_multiplier`
- `bank_defaults`
- `new_budget`
- `net_income`
- *... and 481 more*

## 4. Blast Radius Analysis
Config keys referenced in >10 locations (High Risk):
- `GOODS`: 16 locations
- `goods`: 16 locations
- `is_active`: 16 locations
- `ticks_per_year`: 16 locations

## 5. Default Drift Analysis
Instances where code uses fallback values (`getattr(config, 'key', DEFAULT)`) that may drift from configuration defaults:
- `batch_save_interval` in `simulation/engine.py:207` (fallback: `10`)
- `base_rate` in `simulation/engine.py:274` (fallback: `0.05`)
- `default_mortgage_interest_rate` in `simulation/loan_market.py:106` (fallback: `0.05`)
- `default_mortgage_interest_rate` in `simulation/loan_market.py:150` (fallback: `0.05`)
- `max_dti_ratio` in `simulation/loan_market.py:77` (fallback: `max_dti`)
- `regulations` in `simulation/loan_market.py:70` (fallback: `None`)
- `default_loan_term_ticks` in `simulation/loan_market.py:296` (fallback: `50`)
- `max_dti` in `simulation/loan_market.py:87` (fallback: `max_dti`)
- `max_ltv_ratio` in `simulation/loan_market.py:76` (fallback: `max_ltv`)
- `max_ltv` in `simulation/loan_market.py:86` (fallback: `max_ltv`)
- `housing` in `simulation/loan_market.py:80` (fallback: `None`)
- `dynamic_price_reduction_factor` in `simulation/firms.py:1379` (fallback: `sales_context.dynamic_price_reduction_factor`)
- `dynamic_price_reduction_factor` in `simulation/firms.py:1698` (fallback: `0.9`)
- `sale_timeout_ticks` in `simulation/firms.py:1378` (fallback: `sales_context.sale_timeout_ticks`)
- `sale_timeout_ticks` in `simulation/firms.py:1697` (fallback: `10`)
- `firm_min_employees` in `simulation/firms.py:1348` (fallback: `hr_context.min_employees`)
- `firm_min_employees` in `simulation/firms.py:1580` (fallback: `1`)
- `ticks_per_year` in `simulation/firms.py:1467` (fallback: `365`)
- `firm_max_employees` in `simulation/firms.py:1349` (fallback: `hr_context.max_employees`)
- `firm_max_employees` in `simulation/firms.py:1581` (fallback: `100`)
- *... and 464 more*