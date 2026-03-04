# Insight Report: fix_household_tests

## 1. [Architectural Insights]
- **Protocol Purity Enforced**: Replaced `hasattr(housing_system, 'initiate_purchase')` with `isinstance(housing_system, IHousingSystem)` in `DecisionUnit`, strictly adhering to the architectural protocol rules and restoring type safety.
- **DTO Purity & Clean Access**: Eliminated raw dictionary and missing attribute fallbacks by replacing numerous `hasattr()` calls (e.g., `hasattr(stress_scenario_config, "inflation_expectation_multiplier")`, `hasattr(gov_data, "party")`) with `getattr(..., None)` across `DecisionUnit`, `ConsumptionEngine`, `EconComponent`, `BeliefEngine`, `BudgetEngine`, and `SocialEngine` preserving the codebase's strict stateless engine and SSoT principles.
- **Unit Clarity (Pennies vs Dollars)**: Added explicit inline documentation verifying that both `assets_val` and `config.panic_selling_asset_threshold` in the deflation panic logic are properly evaluated in integer pennies (via `wallet.get_balance(DEFAULT_CURRENCY)`), neutralizing a major "pennies vs. dollars" unit mismatch risk.

## 2. [Regression Analysis]
- Tests were initially broken due to the `isinstance` change in `test_decision_unit.py` as the mock housing system was lacking the `IHousingSystem` spec.
- Fixed `test_orchestrate_housing_buy` by explicitly initializing `mock_housing_system = MagicMock(spec=IHousingSystem)`, maintaining strict Mock/Protocol Fidelity without altering the underlying production intent.

## 3. [Test Evidence]
```text
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
plugins: mock-3.15.1, asyncio-1.3.0, anyio-4.12.1
asyncio: mode=Mode.STRICT, default_loop_scope=None
collected 9 items

tests/unit/modules/household/test_bio_component.py .                     [ 11%]
tests/unit/modules/household/test_consumption_manager.py .               [ 22%]
tests/unit/modules/household/test_decision_unit.py ..                    [ 44%]
tests/unit/modules/household/test_econ_component.py ..                   [ 66%]
tests/unit/modules/household/test_new_engines.py ...                     [100%]

============================== 9 passed in 5.83s ===============================
```
