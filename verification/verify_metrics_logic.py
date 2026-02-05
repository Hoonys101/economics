import unittest
from unittest.mock import MagicMock
from typing import Dict, Any

from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from modules.system.api import DEFAULT_CURRENCY

# Mocks
class MockWallet:
    def __init__(self, balances):
        self.balances = balances
    def get_all_balances(self):
        return self.balances

class MockHolding:
    def __init__(self, quantity):
        self.quantity = quantity

class MockPortfolio:
    def __init__(self, holdings):
        self.holdings = holdings

class MockEconState:
    def __init__(self, assets_val, stock_qty=0):
        self.assets = {DEFAULT_CURRENCY: assets_val}
        self.wallet = MockWallet(self.assets)
        self.labor_income_this_tick = 100.0
        self.current_consumption = 50.0
        self.current_food_consumption = 10.0
        self.education_level = 1
        self.aptitude = 0.5
        self.is_employed = True
        self.portfolio = MockPortfolio({1: MockHolding(stock_qty)})

class MockSocialState:
    def __init__(self, trust):
        self.trust_score = trust

class MockBioState:
    def __init__(self, active=True):
        self.is_active = active
        self.needs = {"survival": 0.5}

class MockHousehold:
    def __init__(self, assets, trust, active=True):
        self._econ_state = MockEconState(assets)
        self._social_state = MockSocialState(trust)
        self._bio_state = MockBioState(active)

class MockStockMarket:
    def get_stock_price(self, firm_id):
        return 10.0 # Fixed price 10.0

class VerifyMetrics(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.tracker = EconomicIndicatorTracker(self.mock_config)
        self.tracker.exchange_engine.convert = lambda amt, f, t: amt
        self.tracker.exchange_engine.get_all_rates = lambda: {}

        self.stock_market = MockStockMarket()
        self.markets = {"stock_market": self.stock_market}

    def test_gini(self):
        self.assertAlmostEqual(self.tracker.calculate_gini_coefficient([10, 10, 10]), 0.0)
        self.assertAlmostEqual(self.tracker.calculate_gini_coefficient([0, 10]), 0.5)

    def test_cohesion(self):
        h1 = MockHousehold(10, 0.8)
        h2 = MockHousehold(20, 0.4)
        cohesion = self.tracker.calculate_social_cohesion([h1, h2])
        self.assertAlmostEqual(cohesion, 0.6)

    def test_population_metrics(self):
        # 5 households
        households = [
            MockHousehold(10, 0.5),
            MockHousehold(20, 0.5),
            MockHousehold(30, 0.5),
            MockHousehold(40, 0.5),
            MockHousehold(50, 0.5)
        ]
        metrics = self.tracker.calculate_population_metrics(households, self.markets)
        self.assertEqual(metrics["active_count"], 5)
        dist = metrics["distribution"]
        # Stock qty is 0 by default in MockHousehold init (unless customized)
        # MockEconState default stock_qty=0
        self.assertEqual(dist["q1"], 10.0)
        self.assertEqual(dist["q5"], 50.0)

    def test_wealth_with_stocks(self):
        # Cash 100, Stock 10 * 10.0 = 200 Total
        h = MockHousehold(100, 0.5)
        # Manually set econ state with stocks
        h._econ_state = MockEconState(100, 10) # 10 shares

        metrics = self.tracker.calculate_population_metrics([h], self.markets)
        self.assertEqual(metrics["all_assets"][0], 200.0)

    def test_track(self):
        # Household with 100 cash, 10 shares (worth 100) -> 200 total
        h = MockHousehold(100, 0.9)
        h._econ_state = MockEconState(100, 10)
        households = [h]
        firms = []

        self.tracker.track(1, households, firms, self.markets)

        latest = self.tracker.get_latest_indicators()
        self.assertAlmostEqual(latest["social_cohesion"], 0.9)
        self.assertAlmostEqual(latest["gini"], 0.0)
        self.assertEqual(latest["active_population"], 1)
        self.assertEqual(latest["quintile_1_avg_assets"], 200.0)

if __name__ == '__main__':
    unittest.main()
