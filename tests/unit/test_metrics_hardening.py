import unittest
from unittest.mock import MagicMock, PropertyMock
from typing import Dict, Any
from collections import deque

from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.metrics.stock_tracker import StockMarketTracker, PersonalityStatisticsTracker
from simulation.metrics.inequality_tracker import InequalityTracker
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.core_markets import Market
from simulation.markets.stock_market import StockMarket
from modules.system.api import DEFAULT_CURRENCY

class TestMetricsHardening(unittest.TestCase):

    def setUp(self):
        self.config_module = MagicMock()

    def test_economic_tracker_track(self):
        tracker = EconomicIndicatorTracker(self.config_module)

        # Mock Households
        h1 = MagicMock()
        h1.__class__ = Household
        h1._bio_state.is_active = True
        h1._econ_state.assets = {DEFAULT_CURRENCY: 1000} # pennies
        h1._econ_state.is_employed = True
        h1._econ_state.consumption_expenditure_this_tick_pennies = 500
        h1._econ_state.food_expenditure_this_tick_pennies = 200
        h1._econ_state.labor_income_this_tick_pennies = 1000
        h1._econ_state.education_level = 1
        h1._econ_state.aptitude = 0.5
        h1._social_state.trust_score = 0.5

        h2 = MagicMock()
        h2.__class__ = Household
        h2._bio_state.is_active = True
        h2._econ_state.assets = {DEFAULT_CURRENCY: 2000}
        h2._econ_state.is_employed = False
        h2._econ_state.consumption_expenditure_this_tick_pennies = 100
        h2._econ_state.food_expenditure_this_tick_pennies = 50
        h2._econ_state.labor_income_this_tick_pennies = 0
        h2._econ_state.education_level = 2
        h2._econ_state.aptitude = 0.9
        h2._social_state.trust_score = 0.6

        # Mock Firms
        f1 = MagicMock()
        f1.__class__ = Firm
        f1.is_active = True
        f1.current_production = 10.0
        f1.sales_volume_this_tick = 5.0
        f1.get_all_balances.return_value = {DEFAULT_CURRENCY: 10000}
        f1.get_balance.return_value = 10000
        f1.get_financial_snapshot.return_value = {"total_assets": 10000.0}

        # Mock get_all_items for inventory
        f1.get_all_items.return_value = {"widget": 50.0}

        # Mock Markets
        m1 = MagicMock(spec=Market)
        m1.get_daily_avg_price.return_value = 10.0
        m1.get_daily_volume.return_value = 100.0

        markets = {"goods_market": m1, "stock_market": MagicMock(spec=StockMarket)}

        # Execute track
        tracker.track(
            time=1,
            households=[h1, h2],
            firms=[f1],
            markets=markets,
            money_supply=100000.0,
            m2_leak=0.0,
            monetary_base=50000.0
        )

        # Verify Metrics
        latest = tracker.get_latest_indicators()
        # Time is not stored in metrics
        self.assertAlmostEqual(latest["total_household_assets"], 3000.0)
        # 10000 firm assets
        self.assertAlmostEqual(latest["total_firm_assets"], 10000.0)
        self.assertAlmostEqual(latest["unemployment_rate"], 50.0)
        self.assertEqual(latest["total_consumption"], 600.0)
        self.assertEqual(latest["total_inventory"], 50.0)

    def test_stock_tracker_arithmetic(self):
        tracker = PersonalityStatisticsTracker(self.config_module)

        # Mock Households
        h1 = MagicMock()
        h1.__class__ = Household
        h1.id = 1
        h1._bio_state.is_active = True
        h1._social_state.personality.name = "MISER"
        h1._econ_state.is_employed = True
        type(h1).total_wealth = PropertyMock(return_value=1000)
        h1._econ_state.assets = {DEFAULT_CURRENCY: 1000}
        h1._econ_state.portfolio.holdings = {}
        # Explicitly set numeric values for income to avoid Mocks
        h1._econ_state.labor_income_this_tick = 100.0
        h1._econ_state.capital_income_this_tick = 10.0

        h2 = MagicMock()
        h2.__class__ = Household
        h2.id = 2
        h2._bio_state.is_active = True
        h2._social_state.personality.name = "MISER"
        h2._econ_state.is_employed = False
        type(h2).total_wealth = PropertyMock(return_value=2000)
        h2._econ_state.assets = {DEFAULT_CURRENCY: 2000}
        h2._econ_state.portfolio.holdings = {}
        h2._econ_state.labor_income_this_tick = 0.0
        h2._econ_state.capital_income_this_tick = 20.0

        # Test calculation
        stats = tracker.calculate_personality_statistics([h1, h2], stock_market=None)

        miser_stats = next(s for s in stats if s["personality_type"] == "MISER")

        # Avg assets: (1000 + 2000) / 2 = 1500
        self.assertEqual(miser_stats["avg_assets"], 1500.0)
        self.assertEqual(miser_stats["employment_rate"], 0.5)

    def test_inequality_tracker_quintiles(self):
        tracker = InequalityTracker(self.config_module)

        households = []
        for i in range(5):
            h = MagicMock()
            h.__class__ = Household
            h.id = i
            wealth = (i + 1) * 1000
            type(h).total_wealth = PropertyMock(return_value=wealth)
            h._econ_state.assets = {DEFAULT_CURRENCY: wealth}
            households.append(h)

        tracker.initialize_cohort(households)

        self.assertEqual(tracker.initial_quintiles[0], 1)
        self.assertEqual(tracker.initial_quintiles[4], 5)

        dist = tracker.calculate_quintile_distribution(households)

        self.assertEqual(dist["quintile_1_avg_assets"], 1000.0)
        self.assertEqual(dist["quintile_5_avg_assets"], 5000.0)

        wealth_dist = tracker.calculate_wealth_distribution(households)
        self.assertAlmostEqual(wealth_dist["mean_household_assets"], 3000.0)
        self.assertIsInstance(wealth_dist["gini_total_assets"], float)

if __name__ == '__main__':
    unittest.main()
