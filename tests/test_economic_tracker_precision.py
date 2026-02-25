import unittest
from unittest.mock import MagicMock, PropertyMock
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.core_markets import Market
from modules.system.api import DEFAULT_CURRENCY

class TestEconomicTrackerPrecision(unittest.TestCase):
    def setUp(self):
        self.config_module = MagicMock()
        self.tracker = EconomicIndicatorTracker(self.config_module)
        # Mock exchange engine
        self.tracker.exchange_engine = MagicMock()
        self.tracker.exchange_engine.convert.side_effect = lambda amount, from_curr, to_curr: amount # 1:1 conversion

    def test_tracker_returns_integers(self):
        """
        Verify that EconomicIndicatorTracker returns integers (Pennies) for consumption, income, and assets.
        """
        # Mock Household
        h1 = MagicMock(spec=Household)
        # Bio state
        h1._bio_state = MagicMock()
        h1._bio_state.is_active = True
        h1._bio_state.needs = {"survival": 0.5}

        # Econ state
        h1._econ_state = MagicMock()
        h1._econ_state.assets = {DEFAULT_CURRENCY: 10000} # 100.00 currency
        h1._econ_state.consumption_expenditure_this_tick_pennies = 5000 # 50.00 currency
        h1._econ_state.food_expenditure_this_tick_pennies = 2000 # 20.00 currency
        h1._econ_state.labor_income_this_tick_pennies = 3000 # 30.00 currency
        h1._econ_state.education_level = 1.0
        h1._econ_state.aptitude = 0.5
        h1._econ_state.portfolio.holdings = {}

        # Social state
        h1._social_state = MagicMock()
        h1._social_state.trust_score = 0.5

        # Mock Firm
        f1 = MagicMock(spec=Firm)
        f1.is_active = True
        f1.get_all_balances.return_value = {DEFAULT_CURRENCY: 20000} # 200.00 currency
        f1.get_balance.return_value = 20000
        f1.get_financial_snapshot.return_value = {"total_assets": 20000} # Only cash
        f1.current_production = 10.0
        f1.sales_volume_this_tick = 5.0
        f1.get_all_items.return_value = {"item1": 10.0}

        # Mock Markets
        m1 = MagicMock(spec=Market)
        m1.get_daily_avg_price.return_value = 100 # 1.00 currency
        m1.get_daily_volume.return_value = 10.0
        markets = {"goods": m1, "labor": MagicMock(), "loan_market": MagicMock(), "stock_market": MagicMock()}

        # Run track
        self.tracker.track(
            time=1,
            households=[h1],
            firms=[f1],
            markets=markets,
            money_supply=100000.0,
            m2_leak=0.0,
            monetary_base=50000.0
        )

        latest = self.tracker.get_latest_indicators()

        # Check types and values (Pennies)

        # Consumption
        # Expectation: 5000 pennies (int)
        # Current Implementation (before fix): 50.0 (float)
        print(f"DEBUG: Total Consumption: {latest['total_consumption']} (Type: {type(latest['total_consumption'])})")
        self.assertIsInstance(latest['total_consumption'], int)
        self.assertEqual(latest['total_consumption'], 5000)

        # Food Consumption
        # Expectation: 2000 pennies (int)
        print(f"DEBUG: Total Food Consumption: {latest['total_food_consumption']} (Type: {type(latest['total_food_consumption'])})")
        self.assertIsInstance(latest['total_food_consumption'], int)
        self.assertEqual(latest['total_food_consumption'], 2000)

        # Labor Income
        # Expectation: 3000 pennies (int)
        print(f"DEBUG: Total Labor Income: {latest['total_labor_income']} (Type: {type(latest['total_labor_income'])})")
        self.assertIsInstance(latest['total_labor_income'], int)
        self.assertEqual(latest['total_labor_income'], 3000)

        # Assets
        # Expectation: 10000 pennies (int)
        print(f"DEBUG: Total Household Assets: {latest['total_household_assets']} (Type: {type(latest['total_household_assets'])})")
        self.assertIsInstance(latest['total_household_assets'], int)
        self.assertEqual(latest['total_household_assets'], 10000)

        # Firm Assets
        # Expectation: 20000 pennies (int)
        print(f"DEBUG: Total Firm Assets: {latest['total_firm_assets']} (Type: {type(latest['total_firm_assets'])})")
        self.assertIsInstance(latest['total_firm_assets'], int)
        self.assertEqual(latest['total_firm_assets'], 20000)

        # Labor Share Calculation
        # Nominal GDP = Total Production (10.0) * Avg Price (100) = 1000.0
        # Labor Income (before fix) = 30.0
        # Labor Share (before fix) = 30.0 / 1000.0 = 0.03

        # Labor Income (after fix) = 3000
        # Labor Share (after fix) = 3000 / 1000.0 = 3.0 (Wait, 300%? No.)
        # If GDP is quantity * price (pennies) -> 10 * 100 = 1000 pennies.
        # Labor Income = 3000 pennies.
        # Share = 3000 / 1000 = 3.0.
        # This implies Labor Income > GDP, which is possible in toy example.

        # Let's verify calculation in tracker.
        # nominal_gdp = record["total_production"] * record["avg_goods_price"]
        # record["labor_share"] = total_labor_income / nominal_gdp

        # If I fix total_labor_income to pennies, then ratio is correct (Pennies / Pennies).
        # Before fix: Dollars / Pennies = (Pennies/100) / Pennies = 1/100th of correct value.

        print(f"DEBUG: Labor Share: {latest.get('labor_share', 'N/A')}")
        self.assertEqual(latest.get('labor_share'), 3.0)

        # Average Prices
        # Expectation: Int (Pennies)
        print(f"DEBUG: Avg Goods Price: {latest['avg_goods_price']} (Type: {type(latest['avg_goods_price'])})")
        self.assertIsInstance(latest['avg_goods_price'], int)

        print(f"DEBUG: Food Avg Price: {latest['food_avg_price']} (Type: {type(latest['food_avg_price'])})")
        self.assertIsInstance(latest['food_avg_price'], int)

        # Avg Wage (should be int, default 0 if not calc)
        print(f"DEBUG: Avg Wage: {latest.get('avg_wage')} (Type: {type(latest.get('avg_wage'))})")
        if 'avg_wage' in latest:
             self.assertIsInstance(latest['avg_wage'], int)
