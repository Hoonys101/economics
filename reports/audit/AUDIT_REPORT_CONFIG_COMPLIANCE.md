# AUDIT_REPORT_CONFIG_COMPLIANCE
**Date**: 2026-03-05
**Target**: `simulation/`, `modules/`, `config/`

## 1. Executive Summary
이 보고서는 `AUDIT_SPEC_CONFIG_COMPLIANCE.md` 사양에 따라 코드베이스의 설정 외부화 수준을 검증한 결과입니다.
- **탐지된 Magic Numbers**: 197건
- **Dead Configs (미참조 설정)**: 24건
- **High Blast Radius 설정 (>10 참조)**: 25건
- **Default Drift 의심 항목**: 81건

## 2. 세부 발견 사항

### 2.1 Critical / High Risk: Magic Numbers (일부 발췌)
코드베이스 내 하드코딩된 주요 상수값들입니다. (전체 목록은 제외하고 주요 항목만 표기)
| File | Variable | Value | Line |
| :--- | :--- | :--- | :--- |
| `engine.py` | `base_rate` | `0.05` | 272 |
| `models.py` | `int` | `10000` | 103 |
| `models.py` | `float` | `0.5` | 136 |
| `bank.py` | `_DEFAULT_INITIAL_BASE_ANNUAL_RATE` | `0.03` | 32 |
| `loan_market.py` | `max_ltv` | `0.8` | 66 |
| `loan_market.py` | `max_dti` | `0.43` | 67 |
| `firms.py` | `sensitivity` | `0.1` | 1615 |
| `firms.py` | `corp_tax_rate` | `0.2` | 1836 |
| `schemas.py` | `float` | `0.5` | 13 |
| `schemas.py` | `float` | `0.5` | 18 |
| `constants.py` | `SYSTEM_MARKET_MAKER_ID` | `999999` | 4 |
| `core_agents.py` | `trust_score` | `0.5` | 298 |
| `taylor_rule_policy.py` | `neutral_rate` | `0.02` | 47 |
| `agent_factory.py` | `mutation_range` | `0.1` | 177 |
... 외 177건

### 2.2 Medium Risk: Dead Config (YAML 정의이나 미참조)
| Config Key | Location |
| :--- | :--- |
| `deposit_margin` | `config/*.yaml` |
| `base_labor_skill` | `config/*.yaml` |
| `hostile_takeover_premium` | `config/*.yaml` |
| `merger_employee_retention_rates` | `config/*.yaml` |
| `foreclosure_fire_sale_discount` | `config/*.yaml` |
| `epsilon_decay_params` | `config/*.yaml` |
| `actuator_bounds` | `config/*.yaml` |
| `bank_margin` | `config/*.yaml` |
| `friendly_merger_premium` | `config/*.yaml` |
| `housing_annual_maintenance_rate` | `config/*.yaml` |
| `chaos_events` | `config/*.yaml` |
| `reward_brand_value_multiplier` | `config/*.yaml` |
| `hostile_takeover_success_prob` | `config/*.yaml` |
| `default_loan_term_ticks` | `config/*.yaml` |
| `fallback_survival_cost` | `config/*.yaml` |
| `default_mortgage_interest_rate` | `config/*.yaml` |
| `actuator_step_sizes` | `config/*.yaml` |
| `sma_buffer_window` | `config/*.yaml` |
| `solvency_buffer` | `config/*.yaml` |
| `housing_npv_horizon_years` | `config/*.yaml` |
| `housing_npv_risk_premium` | `config/*.yaml` |
| `mortgage_default_down_payment_rate` | `config/*.yaml` |
| `ai_housing` | `config/*.yaml` |
| `price_volatility_window_ticks` | `config/*.yaml` |

### 2.3 Medium Risk: High Blast Radius Configs
| Config Key | Reference Count |
| :--- | :--- |
| `system` | 454 |
| `agent` | 393 |
| `bank` | 216 |
| `tick` | 196 |
| `ai` | 194 |
| `asset` | 135 |
| `value` | 132 |
| `housing` | 119 |
| `tax` | 93 |
| `survival` | 75 |
| `corporate_tax_rate` | 56 |
| `social` | 53 |
| `base_rate` | 46 |
| `taxation` | 28 |
| `policy` | 25 |
| `labor_market` | 22 |
| `improvement` | 18 |
| `rate` | 16 |
| `ticks_per_year` | 15 |
| `budget` | 13 |
| `liquidity_need` | 11 |

### 2.4 High Risk: Default Drift (설정 vs 코드 불일치 의심)
동일한 설정 키에 대해 코드 내에서 여러 다른 기본값을 사용하는 경우입니다.
| Config Key | Found Defaults in Code |
| :--- | :--- |
| `assets` | `{}, 0, 0.0` |
| `base_rate` | `0.05, 0.0` |
| `max_ltv_ratio` | `0.8, max_ltv` |
| `housing` | `None, {}` |
| `loan_market` | `{}, None, loan_market_state` |
| `labor_skill` | `s_wrapper.dto.brand_info.get('quality', 1.0, 1.0` |
| `age` | `5, 0, 0.0` |
| `education_level` | `0, 0.0` |
| `labor` | `{}, None` |
| `avg_wage` | `0.0, 10.0, config.labor_market_min_wage` |
| `firm_min_employees` | `hr_context.min_employees, 1` |
| `firm_max_employees` | `hr_context.max_employees, 100` |
| `severance_pay_weeks` | `hr_context.severance_pay_weeks, 2, 2.0` |
| `inputs` | `{}, prod_context.input_goods` |
| `quality_sensitivity` | `prod_context.quality_sensitivity, 0.5` |
| `sale_timeout_ticks` | `sales_context.sale_timeout_ticks, 10` |
| `dynamic_price_reduction_factor` | `sales_context.dynamic_price_reduction_factor, 0.9` |
| `ticks_per_year` | `365, 360` |
| `gdp` | `None, 0, 0.0` |
| `goods_price_index` | `[], 0.0` |
| `unemployment_rate` | `1.0, 0.0` |
| `is_active` | `True, False` |
| `initial_price` | `1000, 500` |
| `TICKS_PER_YEAR` | `100.0, DEFAULT_TICKS_PER_YEAR, 100` |
| `AUTO_COUNTER_CYCLICAL_ENABLED` | `True, False` |
| `total_debt` | `None, 0` |
| `income_tax_rate` | `0.2, 0.1` |
| `corporate_tax_rate` | `0.2, 0.0` |
| `liquidity_need` | `0, 0.0` |
| `item_id` | `None, '', 'unknown'` |
| `quantity` | `0, 0.0` |
| `MITOSIS_MUTATION_PROBABILITY` | `0.2, 0.1` |
| `sector` | `"OTHER", "FOOD"` |
| `avg_goods_price` | `[], 10.0, 0.0` |
| `money_supply` | `0, 0.0` |
| `inflation_rate` | `state.config_module.DEFAULT_INFLATION_RATE, 0.0` |
| `gender` | `None, "N/A", "M"` |
| `major` | `IndustryDomain.GENERAL, 'GENERAL', "GENERAL"` |
| `wage` | `min_wage, 0, 1000` |
| `DEFAULT_FALLBACK_PRICE` | `5.0, 1000` |
| `USD` | `0, 0.0` |
| `basic_food` | `{}, DEFAULT_BASIC_FOOD_PRICE, 0.0` |
| `STARTUP_COST` | `15000.0, 30000.0` |
| `side` | `None, getattr(order, 'order_type', None` |
| `market_signals` | `None, {}` |
| `price_limit` | `order.price, getattr(order, 'price', 0.0` |
| `best_bid` | `None, 0.0` |
| `last_traded_price` | `None, 0.0` |
| `market_data` | `None, {}` |
| `stock_market` | `{}, None` |
| `avg_price` | `price_estimate, food_price_float, 0.0` |
| `survival` | `50.0, 100.0, 0` |
| `current_wage` | `None, 0.0` |
| `aptitude` | `0.5, 0.0` |
| `interest_rate` | `0.03, 0.05, config.default_mortgage_rate` |
| `current_wage_pennies` | `0, getattr(household, 'current_wage', 0` |
| `basic_food_current_sell_price` | `5.0, 500` |
| `loans` | `[], {}` |
| `current_price` | `price_estimate, food_price_float, 0.0` |
| `cpi` | `None, 0.0` |
| `needs` | `{}, None` |
| `social_status` | `0, 0.0` |
| `inventory` | `{}, None` |
| `OPPORTUNITY_COST_FACTOR` | `0.5, 0.3` |
| `CHILD_EMOTIONAL_VALUE_BASE` | `200000.0, 500000.0` |
| `social_rank` | `0.5, 0.0` |
| `currency` | `DEFAULT_CURRENCY, 0.0` |
| `HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK` | `1.0, DEFAULT_HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK, 2.0` |
| `owner_id` | `None, 'Unknown'` |
| `holdings` | `{}, None` |
| `outstanding_balance` | `0, 0.0` |
| `markets` | `None, {}` |
| `generation` | `getattr(agent, "generation", 0, 1, 0` |
| `labor_need` | `0, 0.0` |
| `price` | `5.0, 0, default_price` |
| `agents` | `{}, getattr(self.simulation.world_state, 'agents', {}` |
| `goods_data` | `[], {}` |
| `agent_id` | `None, -1` |
| `_batch_depth` | `None, 0` |

## 3. 권고 사항 (Recommendations)
1. **Magic Number 외부화**: `simulation/`, `modules/` 등 비즈니스 로직에 존재하는 하드코딩된 상수들을 `config/` 내의 적절한 YAML 파일이나 파이썬 상수(예: `constants.py`)로 분리해야 합니다.
2. **Dead Config 제거 또는 활용**: YAML 파일에 존재하지만 참조되지 않는 설정 항목(`ai_housing`, `foreclosure_fire_sale_discount` 등)을 정리하거나 필요한 로직에 연결해야 합니다.
3. **Centralized Config Access**: `getattr(config, 'key', DEFAULT)` 패턴이 코드 여러 곳에 흩어져 Default Drift를 발생시키고 있습니다. `ConfigManager`나 중앙 집중화된 접근 계층을 사용하여 기본값을 한 곳에서 관리해야 합니다.
4. **Blast Radius 통제**: `balance`, `inventory` 와 같은 키워드가 많이 참조되는 것은 객체 구조에 대한 의존성이 높음을 의미합니다. 가능한 DTO를 활용하여 구조 결합도를 낮추는 것을 권장합니다.