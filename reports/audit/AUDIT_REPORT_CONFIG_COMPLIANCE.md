# AUDIT_REPORT_CONFIG_COMPLIANCE

## 1. Magic Number 탐지
| File | Line | Code | Value |
| --- | --- | --- | --- |
| `modules/analysis/detectors/policy_effectiveness_detector.py` | 39 | `zlb_threshold = 0.001` | `0.001` |
| `modules/analysis/scenario_verifier/judges/sc001_female_labor.py` | 22 | `target_kpi_value=0.9,` | `0.9` |
| `modules/analysis/scenario_verifier/judges/sc001_female_labor.py` | 42 | `target = 0.90` | `0.90` |
| `modules/finance/central_bank/service.py` | 23 | `self._policy_rate: float = 0.05  # Default initial rate` | `0.05` |
| `modules/finance/engine_api.py` | 43 | `base_rate: float = 0.03` | `0.03` |
| `modules/finance/engines/interest_rate_engine.py` | 19 | `target_rate = 0.03 + (inflation * 0.5)` | `0.03` |
| `modules/finance/engines/loan_risk_engine.py` | 19 | `base_rate = 0.03` | `0.03` |
| `modules/finance/engines/loan_risk_engine.py` | 66 | `risk_premium = 0.05` | `0.05` |
| `modules/finance/engines/loan_risk_engine.py` | 68 | `risk_premium = 0.02` | `0.02` |
| `modules/finance/engines/monetary_engine.py` | 43 | `neutral_rate = 0.02` | `0.02` |
| `modules/finance/engines/monetary_engine.py` | 61 | `max_change = 0.0025` | `0.0025` |
| `modules/finance/monetary/api.py` | 62 | `inflation_target: float = 0.02` | `0.02` |
| `modules/finance/monetary/api.py` | 63 | `unemployment_target: float = 0.05` | `0.05` |
| `modules/finance/monetary/api.py` | 64 | `m2_growth_target: float = 0.03 # For Friedman Rule (k%)` | `0.03` |
| `modules/finance/monetary/api.py` | 65 | `ngdp_target_growth: float = 0.04 # For McCallum Rule` | `0.04` |
| `modules/finance/monetary/api.py` | 69 | `taylor_beta: float = 0.5  # Weight on Output Gap` | `0.5` |
| `modules/finance/monetary/api.py` | 70 | `neutral_rate: float = 0.02 # r*` | `0.02` |
| `modules/finance/monetary/api.py` | 74 | `max_interest_rate: float = 0.20` | `0.20` |
| `modules/finance/monetary/strategies.py` | 60 | `max_change = 0.0025 # 25 bps` | `0.0025` |
| `modules/firm/constants.py` | 5 | `DEFAULT_MARKET_INSIGHT = 0.5` | `0.5` |
| `modules/firm/constants.py` | 6 | `INSIGHT_DECAY_RATE = 0.001` | `0.001` |
| `modules/firm/constants.py` | 7 | `INSIGHT_BOOST_FACTOR = 0.05` | `0.05` |
| `modules/firm/constants.py` | 11 | `DEFAULT_MARKETING_BUDGET_RATE = 0.05` | `0.05` |
| `modules/firm/constants.py` | 25 | `DEFAULT_CORPORATE_TAX_RATE = 0.2` | `0.2` |
| `modules/governance/judicial/api.py` | 13 | `bankruptcy_threshold: int = -1000  # Debt level triggering bankruptcy` | `-1000` |
| `modules/government/ai/api.py` | 14 | `alpha: float = 0.1  # Learning Rate` | `0.1` |
| `modules/government/ai/api.py` | 15 | `gamma: float = 0.95 # Discount Factor` | `0.95` |
| `modules/government/ai/api.py` | 16 | `epsilon: float = 0.1 # Exploration Rate` | `0.1` |
| `modules/government/ai/api.py` | 23 | `w_approval: float = 0.7  # Weight for Approval Rating (Populism)` | `0.7` |
| `modules/government/ai/api.py` | 24 | `w_stability: float = 0.2 # Weight for Macro Stability (Technocracy)` | `0.2` |
| `modules/government/ai/api.py` | 25 | `w_lobbying: float = 0.1  # Weight for Lobbying Compliance (Corruption)` | `0.1` |
| `modules/government/ai/api.py` | 31 | `lobbying_threshold_high_tax: float = 0.25 # If > 0.25, Corp pressures for cuts` | `0.25` |
| `modules/government/ai/api.py` | 32 | `lobbying_threshold_high_unemployment: float = 0.05 # If > 0.05, Labor pressures for spending` | `0.05` |
| `modules/government/components/fiscal_policy_manager.py` | 108 | `income_tax_rate=0.1, # Default placeholder` | `0.1` |
| `modules/government/components/fiscal_policy_manager.py` | 109 | `corporate_tax_rate=0.2 # Default placeholder` | `0.2` |
| `modules/government/constants.py` | 5 | `DEFAULT_INFRASTRUCTURE_INVESTMENT_COST = 500000 # MIGRATION: pennies (was 5000.0)` | `500000` |
| `modules/government/constants.py` | 6 | `DEFAULT_ANNUAL_WEALTH_TAX_RATE = 0.02` | `0.02` |
| `modules/government/constants.py` | 7 | `DEFAULT_WEALTH_TAX_THRESHOLD = 5000000 # MIGRATION: pennies (was 50000.0)` | `5000000` |
| `modules/government/constants.py` | 8 | `DEFAULT_UNEMPLOYMENT_BENEFIT_RATIO = 0.8` | `0.8` |
| `modules/government/constants.py` | 9 | `DEFAULT_STIMULUS_TRIGGER_GDP_DROP = -0.05` | `-0.05` |
| `modules/government/dtos.py` | 42 | `corporate_tax_rate: float = 0.2` | `0.2` |
| `modules/government/dtos.py` | 43 | `income_tax_rate: float = 0.1` | `0.1` |
| `modules/government/dtos.py` | 47 | `target_interest_rate: float = 0.05` | `0.05` |
| `modules/government/dtos.py` | 48 | `inflation_target: float = 0.02` | `0.02` |
| `modules/government/dtos.py` | 49 | `unemployment_target: float = 0.05` | `0.05` |
| `modules/government/dtos.py` | 53 | `bailout_threshold_solvency: float = 0.1` | `0.1` |
| `modules/government/dtos.py` | 215 | `approval_low_asset: float = 0.5` | `0.5` |
| `modules/government/dtos.py` | 216 | `approval_high_asset: float = 0.5` | `0.5` |
| `modules/government/engines/fiscal_engine.py` | 205 | `interest_rate=0.05, # Default term` | `0.05` |
| `modules/government/policies/adaptive_gov_brain.py` | 134 | `next_state.gdp_growth_sma -= 0.001` | `0.001` |

*...and 196 more. Showing first 50.*

## 2. Dead Config 탐지
| Config Key |
| --- |
| `F` |
| `M` |
| `active` |
| `active_welfare_programs` |
| `adjusted_price` |
| `affected_entities` |
| `age` |
| `ai` |
| `ai_epsilon_decay_params` |
| `ai_reward_brand_value_multiplier` |
| `amount_issued` |
| `annual_wealth_tax_rate` |
| `approval_state` |
| `approved_loan_id` |
| `assets_death_threshold` |
| `assets_pennies` |
| `assets_value_pennies` |
| `attribute_name` |
| `audit_requirements` |
| `available_cash_pennies` |
| `average_prices` |
| `avg_skill` |
| `bailout_threshold_solvency` |
| `bank_credit_spread_base` |
| `bank_deposit_margin` |
| `bank_margin` |
| `bank_solvency_buffer` |
| `bankruptcy_consecutive_loss_ticks` |
| `bankruptcy_threshold` |
| `base_labor_skill` |
| `base_need_satisfaction` |
| `behavior_config` |
| `benchmark_rates` |
| `bond_id` |
| `bond_series_id` |
| `bonds_transacted_count` |
| `brand_awareness_saturation` |
| `brand_prestige` |
| `brand_resilience_factor` |
| `budget_allocation_max` |
| `budget_allocation_min` |
| `buffer_capital_pennies` |
| `bulk_buy_agg_threshold` |
| `bulk_buy_moderate_ratio` |
| `bulk_buy_need_threshold` |
| `capital_budget_pennies` |
| `cash_balance_pennies` |
| `cash_pennies` |
| `cash_transferred` |
| `cb_inflation_target` |

*...and 385 more. Showing first 50.*

## 3. Config Blast Radius 분석
| Config Key | Reference Count | Example Locations |
| --- | --- | --- |
| `config` | **379** | `simulation/firms.py:138` |
| `logger` | **348** | `simulation/engine.py:89` |
| `config_module` | **217** | `simulation/loan_market.py:31` |
| `time` | **215** | `simulation/engine.py:143` |
| `settlement_system` | **209** | `simulation/engine.py:57` |
| `error` | **196** | `simulation/engine.py:157` |
| `is_active` | **157** | `simulation/firms.py:136` |
| `bank` | **132** | `simulation/engine.py:254` |
| `item_id` | **126** | `simulation/loan_market.py:279` |
| `agents` | **114** | `simulation/world_state.py:170` |
| `agent_registry` | **102** | `simulation/engine.py:58` |
| `government` | **96** | `simulation/engine.py:264` |
| `wallet` | **96** | `simulation/firms.py:309` |
| `assets` | **89** | `simulation/engine.py:258` |
| `markets` | **79** | `simulation/world_state.py:82` |
| `needs` | **76** | `simulation/bank.py:69` |
| `inventory` | **75** | `simulation/firms.py:303` |
| `market_data` | **67** | `simulation/firms.py:1195` |
| `portfolio` | **67** | `simulation/core_agents.py:519` |
| `metadata` | **65** | `simulation/models.py:32` |
| `households` | **59** | `simulation/world_state.py:178` |
| `firms` | **56** | `simulation/world_state.py:186` |
| `current_tick` | **55** | `simulation/firms.py:740` |
| `is_employed` | **49** | `simulation/core_agents.py:491` |
| `production` | **49** | `simulation/decisions/rule_based_firm_engine.py:27` |
| `price_pennies` | **48** | `simulation/firms.py:1252` |
| `employees` | **45** | `simulation/firms.py:923` |
| `transactions` | **44** | `simulation/engine.py:202` |
| `owner_id` | **43** | `simulation/portfolio.py:11` |
| `tick` | **42** | `simulation/components/engines/sales_engine.py:76` |
| `specialization` | **41** | `simulation/firms.py:171` |
| `corporate_tax_rate` | **41** | `simulation/firms.py:1728` |
| `path` | **41** | `simulation/utils/golden_loader.py:25` |
| `base_rate` | **39** | `simulation/engine.py:274` |
| `income_tax_rate` | **37** | `simulation/firms.py:1449` |
| `sensory_data` | **37** | `simulation/policies/smart_leviathan_policy.py:71` |
| `currency` | **37** | `simulation/components/engines/hr_engine.py:366` |
| `buyer_id` | **36** | `simulation/models.py:61` |
| `finance` | **35** | `simulation/decisions/rule_based_firm_engine.py:139` |
| `owned_properties` | **34** | `simulation/firms.py:1026` |
| `seller_id` | **33** | `simulation/models.py:66` |
| `children_ids` | **33** | `simulation/core_agents.py:458` |
| `balance_pennies` | **32** | `simulation/bank.py:366` |
| `side` | **32** | `simulation/firms.py:1251` |
| `market_signals` | **32** | `simulation/firms.py:1408` |
| `amount_pennies` | **32** | `simulation/firms.py:1799` |
| `real_estate_units` | **32** | `simulation/world_state.py:106` |
| `education_level` | **30** | `simulation/firms.py:931` |
| `loans` | **29** | `simulation/loan_market.py:180` |
| `potential_gdp` | **29** | `simulation/policies/taylor_rule_policy.py:19` |

*...and 766 more. Showing first 50.*

## 4. Default Drift 탐지
| Config Key | File | Line | Fallback | Code |
| --- | --- | --- | --- | --- |
| `assets` | `simulation/engine.py` | 258 | `0.0` | `bank_reserves = getattr(self.world_state.bank, "assets", 0.0)` |
| `is_circuit_breaker_active` | `simulation/engine.py` | 270 | `False` | `circuit_breaker = getattr(self.world_state.stock_market, "is_circuit_breaker_active", False)` |
| `base_rate` | `simulation/engine.py` | 274 | `0.05` | `base_rate = getattr(self.world_state.central_bank, "base_rate", 0.05)` |
| `max_ltv_ratio` | `simulation/loan_market.py` | 76 | `max_ltv` | `max_ltv = getattr(regulations, 'max_ltv_ratio', max_ltv)` |
| `housing` | `simulation/loan_market.py` | 80 | `None` | `housing_config = getattr(self.config_module, 'housing', None)` |
| `labor_market` | `simulation/firms.py` | 178 | `{}` | `labor_market_config = getattr(self.config, 'labor_market', {})` |
| `labor_skill` | `simulation/firms.py` | 929 | `1.0` | `"skill": getattr(e, 'labor_skill', 1.0),` |
| `education_level` | `simulation/firms.py` | 931 | `0` | `"education_level": getattr(e, 'education_level', 0)` |
| `labor_skill` | `simulation/firms.py` | 1079 | `1.0` | `"skill": getattr(e, 'labor_skill', 1.0),` |
| `education_level` | `simulation/firms.py` | 1081 | `0` | `"education_level": getattr(e, 'education_level', 0)` |
| `severance_pay_weeks` | `simulation/firms.py` | 1350 | `hr_context.severance_pay_weeks` | `severance_pay_weeks=getattr(context.config_override, 'severance_pay_weeks', hr_context.severance_pay_weeks)` |
| `sale_timeout_ticks` | `simulation/firms.py` | 1378 | `sales_context.sale_timeout_ticks` | `sale_timeout_ticks=getattr(context.config_override, 'sale_timeout_ticks', sales_context.sale_timeout_ticks),` |
| `dynamic_price_reduction_factor` | `simulation/firms.py` | 1379 | `sales_context.dynamic_price_reduction_factor` | `dynamic_price_reduction_factor=getattr(context.config_override, 'dynamic_price_reduction_factor', sales_context.dynamic_price_reduction_factor)` |
| `ticks_per_year` | `simulation/firms.py` | 1467 | `365` | `ticks_per_year=getattr(self.config, "ticks_per_year", 365),` |
| `severance_pay_weeks` | `simulation/firms.py` | 1468 | `2.0` | `severance_pay_weeks=getattr(self.config, "severance_pay_weeks", 2.0)` |
| `labor_skill` | `simulation/firms.py` | 1504 | `1.0` | `base_skill = getattr(emp, "labor_skill", 1.0)` |
| `labor_skill` | `simulation/firms.py` | 1559 | `1.0` | `employee_skills = {AgentID(e.id): getattr(e, "labor_skill", 1.0) for e in self.hr_state.employees}` |
| `severance_pay_weeks` | `simulation/firms.py` | 1582 | `2` | `severance_pay_weeks=getattr(self.config, 'severance_pay_weeks', 2),` |
| `sale_timeout_ticks` | `simulation/firms.py` | 1697 | `10` | `sale_timeout_ticks=getattr(self.config, 'sale_timeout_ticks', 10),` |
| `dynamic_price_reduction_factor` | `simulation/firms.py` | 1698 | `0.9` | `dynamic_price_reduction_factor=getattr(self.config, 'dynamic_price_reduction_factor', 0.9)` |
| `is_active` | `simulation/world_state.py` | 336 | `True` | `getattr(agent, "is_active", True)` |
| `initial_household_age_range` | `simulation/core_agents.py` | 131 | `(20, 60` | `age_range = getattr(self.config, 'initial_household_age_range', (20, 60))` |
| `elasticity_mapping` | `simulation/core_agents.py` | 273 | `{}` | `demand_elasticity=getattr(self.config, 'elasticity_mapping', {}).get(` |
| `elasticity_mapping` | `simulation/core_agents.py` | 275 | `{}` | `getattr(self.config, 'elasticity_mapping', {}).get("DEFAULT", 1.0)` |
| `insight_decay_rate` | `simulation/core_agents.py` | 610 | `0.001` | `decay_rate = getattr(self.config, "insight_decay_rate", 0.001)` |
| `insight_learning_multiplier` | `simulation/core_agents.py` | 980 | `5.0` | `multiplier = getattr(self.config, "insight_learning_multiplier", 5.0)` |
| `education_boost_amount` | `simulation/core_agents.py` | 1156 | `0.05` | `boost = getattr(self.config, "education_boost_amount", 0.05)` |
| `labor_skill` | `simulation/service_firms.py` | 67 | `1.0` | `total_labor_skill = sum(getattr(emp, 'labor_skill', 1.0) for emp in employees)` |
| `labor_skill` | `simulation/service_firms.py` | 87 | `1.0` | `total_skill = sum(getattr(emp, 'labor_skill', 1.0) for emp in employees)` |
| `settlement_system` | `simulation/action_processor.py` | 65 | `None` | `settlement_system=getattr(self.world_state, "settlement_system", None),` |
| `total_debt` | `simulation/policies/smart_leviathan_policy.py` | 49 | `None` | `total_debt = getattr(government, 'total_debt', None)` |
| `total_wealth` | `simulation/policies/smart_leviathan_policy.py` | 53 | `getattr(government, 'assets', 0` | `total_wealth = getattr(government, 'total_wealth', getattr(government, 'assets', 0))` |
| `assets` | `simulation/policies/smart_leviathan_policy.py` | 53 | `0` | `total_wealth = getattr(government, 'total_wealth', getattr(government, 'assets', 0))` |
| `policy` | `simulation/policies/smart_leviathan_policy.py` | 58 | `None` | `policy_dto = getattr(government, 'policy', None)` |
| `assets` | `simulation/policies/smart_leviathan_policy.py` | 65 | `{}` | `assets=getattr(government, 'assets', {}),` |
| `income_tax_rate` | `simulation/policies/smart_leviathan_policy.py` | 67 | `0.2` | `income_tax_rate=getattr(government, 'income_tax_rate', 0.2),` |
| `corporate_tax_rate` | `simulation/policies/smart_leviathan_policy.py` | 68 | `0.2` | `corporate_tax_rate=getattr(government, 'corporate_tax_rate', 0.2),` |
| `approval_rating` | `simulation/policies/smart_leviathan_policy.py` | 70 | `0.5` | `approval_rating=getattr(government, 'approval_rating', 0.5),` |
| `sensory_data` | `simulation/policies/smart_leviathan_policy.py` | 71 | `None` | `sensory_data=getattr(government, 'sensory_data', None),` |
| `ruling_party` | `simulation/policies/smart_leviathan_policy.py` | 72 | `None` | `ruling_party=getattr(government, 'ruling_party', None),` |
| `welfare_budget_multiplier` | `simulation/policies/smart_leviathan_policy.py` | 73 | `1.0` | `welfare_budget_multiplier=getattr(government, 'welfare_budget_multiplier', 1.0),` |
| `fiscal_policy` | `simulation/policies/smart_leviathan_policy.py` | 75 | `None` | `fiscal_policy=getattr(government, 'fiscal_policy', None),` |
| `policy_lockouts` | `simulation/policies/smart_leviathan_policy.py` | 76 | `{}` | `policy_lockouts=getattr(government, 'policy_lockouts', {}),` |
| `gdp_history` | `simulation/policies/smart_leviathan_policy.py` | 77 | `[]` | `gdp_history=getattr(government, 'gdp_history', []),` |
| `potential_gdp` | `simulation/policies/smart_leviathan_policy.py` | 78 | `0.0` | `potential_gdp=getattr(government, 'potential_gdp', 0.0),` |
| `fiscal_stance` | `simulation/policies/smart_leviathan_policy.py` | 79 | `0.0` | `fiscal_stance=getattr(government, 'fiscal_stance', 0.0)` |
| `strategy` | `simulation/factories/agent_factory.py` | 192 | `None` | `strategy = getattr(simulation, "strategy", None)` |
| `initial_household_age_range` | `simulation/factories/household_factory.py` | 214 | `(20, 60` | `age_range = getattr(self.context.core_config_module, "initial_household_age_range", (20, 60))` |
| `initial_household_assets_mean` | `simulation/factories/household_factory.py` | 251 | `1000` | `mean_assets = int(getattr(self.context.core_config_module, "initial_household_assets_mean", 1000) * 100) # Pennies` |
| `initial_household_age_range` | `simulation/factories/household_factory.py` | 259 | `(20, 60` | `age_range = getattr(self.context.core_config_module, "initial_household_age_range", (20, 60))` |

*...and 308 more. Showing first 50.*
