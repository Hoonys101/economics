# Wave 2.2: Market & Policy Refinement Insight Report

**Date**: 2026-02-21
**Author**: Jules (AI Agent)
**Status**: COMPLETED

## 1. Architectural Insights

### Stock Market Hardening
- **Insight**: The `StockMarket` previously relied on brittle string parsing (`split('_')`) to extract firm IDs from stock IDs. This was a violation of robust input handling.
- **Decision**: Implemented `StockIDHelper` in `modules/market/api.py` to centralize ID validation, parsing, and formatting. This ensures consistent `stock_<id>` format across the system and prevents `IndexError`/`ValueError` crashes in the market engine.
- **Refactor**: `StockMarket.get_price` and `StockMarket.place_order` now use `StockIDHelper` for safe ID handling. Legacy fallback logic was retained in `get_price` to minimize disruption but strict parsing is enforced in `place_order`.

### Progressive Taxation Foundation
- **Insight**: `TaxBracketDTO` and `FiscalPolicyDTO` were inconsistent with the new progressive tax specification. `TaxBracketDTO` used `floor`/`ceiling` which complicated sorting and overlap logic.
- **Decision**: Refactored `TaxBracketDTO` to use a simplified `threshold` (int pennies) and `rate` (float) model. This aligns with standard progressive tax algorithms where brackets are applied to income chunks above a threshold.
- **Implementation**:
    - `FiscalPolicyDTO` now uses a `tax_brackets` list instead of `progressive_tax_brackets`.
    - `FiscalPolicyManager` was rewritten to generate brackets using the new model (Threshold 0 @ 0%, Threshold 1.0*Survival @ 10%, etc.).
    - `FiscalPolicyManager.calculate_tax_liability` now sorts brackets by threshold (descending) and applies rates to marginal income segments, ensuring accurate progressive calculation.
- **Compatibility**: Legacy property `progressive_tax_brackets` was added to `FiscalPolicyDTO` to maintain backward compatibility for read access, though write access via `__init__` was deprecated and usages updated.

## 2. Regression Analysis

- **Regression Risk**: High, due to changes in core DTOs (`FiscalPolicyDTO`, `TaxBracketDTO`) used by Government agents and tests.
- **Mitigation**:
    - Identified all call sites using `grep`.
    - Updated `tests/integration/test_fiscal_policy.py`, `tests/integration/test_government_fiscal_integration.py`, and `scripts/verify_penny_migration_gov.py` to match the new DTO structure.
    - Updated `tests/unit/modules/government/components/test_fiscal_policy_manager.py` to verify the new tax calculation logic with integer math.
- **Outcome**: All 32 relevant tests passed. No regressions observed in Stock Market or Government Fiscal logic.

## 3. Test Evidence

```
tests/market/test_stock_market_pennies.py::TestStockMarketPennies::test_stock_matching_fractional_shares PASSED [  3%]
tests/market/test_stock_market_pennies.py::TestStockMarketPennies::test_stock_matching_integer_math PASSED [  6%]
tests/unit/test_stock_market.py::TestStockMarketInitialization::test_initialization PASSED [  9%]
tests/unit/test_stock_market.py::TestStockMarketInitialization::test_update_reference_prices PASSED [ 12%]
tests/unit/test_stock_market.py::TestStockOrderPlacement::test_place_buy_order
-------------------------------- live log call ---------------------------------
INFO     simulation.markets.stock_market:stock_market.py:165 Stock BUY order placed: 10.0 shares of firm 100 at 50.00
PASSED                                                                   [ 15%]
tests/unit/test_stock_market.py::TestStockOrderPlacement::test_place_sell_order
-------------------------------- live log call ---------------------------------
INFO     simulation.markets.stock_market:stock_market.py:165 Stock SELL order placed: 10.0 shares of firm 100 at 45.00
PASSED                                                                   [ 18%]
tests/unit/test_stock_market.py::TestStockOrderPlacement::test_price_clamping
-------------------------------- live log call ---------------------------------
WARNING  simulation.markets.stock_market:stock_market.py:151 Stock order price 120.00 out of limit range [85.00, 115.00] for firm 100
INFO     simulation.markets.stock_market:stock_market.py:165 Stock BUY order placed: 1.0 shares of firm 100 at 115.00
WARNING  simulation.markets.stock_market:stock_market.py:151 Stock order price 80.00 out of limit range [85.00, 115.00] for firm 100
INFO     simulation.markets.stock_market:stock_market.py:165 Stock SELL order placed: 1.0 shares of firm 100 at 85.00
PASSED                                                                   [ 21%]
tests/unit/test_stock_market.py::TestStockOrderPlacement::test_order_sorting
-------------------------------- live log call ---------------------------------
INFO     simulation.markets.stock_market:stock_market.py:165 Stock BUY order placed: 1.0 shares of firm 100 at 45.00
INFO     simulation.markets.stock_market:stock_market.py:165 Stock BUY order placed: 1.0 shares of firm 100 at 55.00
INFO     simulation.markets.stock_market:stock_market.py:165 Stock BUY order placed: 1.0 shares of firm 100 at 50.00
PASSED                                                                   [ 25%]
tests/unit/test_stock_market.py::TestStockOrderMatching::test_full_match
-------------------------------- live log call ---------------------------------
INFO     simulation.markets.stock_market:stock_market.py:165 Stock BUY order placed: 10.0 shares of firm 100 at 50.00
INFO     simulation.markets.stock_market:stock_market.py:165 Stock SELL order placed: 10.0 shares of firm 100 at 45.00
PASSED                                                                   [ 28%]
tests/unit/test_stock_market.py::TestStockOrderMatching::test_partial_match
-------------------------------- live log call ---------------------------------
INFO     simulation.markets.stock_market:stock_market.py:165 Stock BUY order placed: 15.0 shares of firm 100 at 50.00
INFO     simulation.markets.stock_market:stock_market.py:165 Stock SELL order placed: 10.0 shares of firm 100 at 45.00
INFO     simulation.markets.stock_market:stock_market.py:165 Stock SELL order placed: 5.0 shares of firm 100 at 45.00
PASSED                                                                   [ 31%]
tests/unit/test_stock_market.py::TestOrderExpiry::test_clear_expired_orders
-------------------------------- live log call ---------------------------------
INFO     simulation.markets.stock_market:stock_market.py:165 Stock BUY order placed: 5.0 shares of firm 100 at 50.00
PASSED                                                                   [ 34%]
tests/market/test_stock_id_helper.py::TestStockIDHelper::test_stock_id_helper_valid PASSED [ 37%]
tests/market/test_stock_id_helper.py::TestStockIDHelper::test_stock_id_helper_invalid PASSED [ 40%]
tests/market/test_stock_id_helper.py::TestStockIDHelper::test_format_stock_id_handles_string PASSED [ 43%]
tests/unit/modules/government/components/test_fiscal_policy_manager.py::TestFiscalPolicyManager::test_determine_fiscal_stance_calculates_survival_cost_correctly PASSED [ 46%]
tests/unit/modules/government/components/test_fiscal_policy_manager.py::TestFiscalPolicyManager::test_determine_fiscal_stance_defaults_if_no_config PASSED [ 50%]
tests/unit/modules/government/components/test_fiscal_policy_manager.py::TestFiscalPolicyManager::test_calculate_tax_liability_progressive PASSED [ 53%]
tests/unit/modules/government/components/test_fiscal_policy_manager.py::TestFiscalPolicyManager::test_calculate_tax_liability_zero_or_negative PASSED [ 56%]
scripts/verify_penny_migration_gov.py::TestPennyMigrationGov::test_fiscal_policy_manager_survival_cost PASSED [ 59%]
scripts/verify_penny_migration_gov.py::TestPennyMigrationGov::test_tax_service_wealth_tax PASSED [ 62%]
scripts/verify_penny_migration_gov.py::TestPennyMigrationGov::test_taxation_system_calculate_income_tax PASSED [ 65%]
scripts/verify_penny_migration_gov.py::TestPennyMigrationGov::test_taxation_system_calculate_tax_intents_food_price PASSED [ 68%]
scripts/verify_penny_migration_gov.py::TestPennyMigrationGov::test_welfare_manager_survival_cost PASSED [ 71%]
tests/integration/test_fiscal_policy.py::test_potential_gdp_ema_convergence
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
-------------------------------- live log call ---------------------------------
INFO     modules.common.utils.shadow_logger:shadow_logger.py:36 ShadowLogger initialized at logs/shadow_hand_stage1.csv
PASSED                                                                   [ 75%]
tests/integration/test_fiscal_policy.py::test_counter_cyclical_tax_adjustment_recession
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
PASSED                                                                   [ 78%]
tests/integration/test_fiscal_policy.py::test_counter_cyclical_tax_adjustment_boom
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
PASSED                                                                   [ 81%]
tests/integration/test_fiscal_policy.py::test_debt_ceiling_enforcement
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
-------------------------------- live log call ---------------------------------
INFO     modules.finance.system:system.py:311 BOND_REGISTERED | BOND_1_1 registered to MOCK_BUYER
INFO     modules.finance.system:system.py:311 BOND_REGISTERED | BOND_1_2 registered to MOCK_BUYER
WARNING  simulation.agents.government:government.py:465 WELFARE_FAILED | Insufficient funds even after bond issuance attempt. Needed: 100, Has: 0
PASSED                                                                   [ 84%]
tests/integration/test_fiscal_policy.py::test_calculate_income_tax_uses_current_rate
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
PASSED                                                                   [ 87%]
tests/integration/test_government_fiscal_integration.py::TestGovernmentFiscalIntegration::test_calculate_income_tax_uses_fiscal_policy_manager
-------------------------------- live log call ---------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
PASSED                                                                   [ 90%]
tests/integration/test_government_fiscal_integration.py::TestGovernmentFiscalIntegration::test_make_policy_decision_updates_fiscal_policy
-------------------------------- live log call ---------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
PASSED                                                                   [ 93%]
tests/modules/government/test_tax_service.py::test_collect_wealth_tax PASSED [ 96%]
tests/modules/government/test_tax_service.py::test_collect_wealth_tax_below_threshold PASSED [100%]

======================== 32 passed, 2 warnings in 0.51s ========================
```
