
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import unittest
from unittest.mock import MagicMock
from simulation.agents.central_bank import CentralBank

class MockTracker:
    def __init__(self):
        self.metrics = {"avg_goods_price": [], "total_production": []}

    def get_latest_indicators(self):
        return {
            "avg_goods_price": self.metrics["avg_goods_price"][-1] if self.metrics["avg_goods_price"] else 0,
            "total_production": self.metrics["total_production"][-1] if self.metrics["total_production"] else 0
        }

class MockConfig:
    INITIAL_BASE_ANNUAL_RATE = 0.05
    CB_UPDATE_INTERVAL = 5
    CB_INFLATION_TARGET = 0.02
    CB_TAYLOR_ALPHA = 1.5
    CB_TAYLOR_BETA = 0.5
    TICKS_PER_YEAR = 100

class TestCentralBank(unittest.TestCase):
    def setUp(self):
        self.tracker = MockTracker()
        self.config = MockConfig()
        self.cb = CentralBank(self.tracker, self.config)

    def test_initialization(self):
        self.assertEqual(self.cb.base_rate, 0.05)
        self.assertEqual(self.cb.update_interval, 5)

    def test_gdp_potential_tracking(self):
        # Tick 1: GDP 100. Potential should become 100.
        self.tracker.metrics["total_production"].append(100)
        self.cb.step(1)
        self.assertEqual(self.cb.potential_gdp, 100)

        # Tick 2: GDP 110. Potential should update slowly.
        # Alpha is 0.05. New Pot = 0.05 * 110 + 0.95 * 100 = 5.5 + 95 = 100.5
        self.tracker.metrics["total_production"].append(110)
        self.cb.step(2)
        self.assertAlmostEqual(self.cb.potential_gdp, 100.5)

    def test_inflation_hike(self):
        # Scenario: High Inflation
        # Base Rate: 0.05
        # Target Infl: 0.02
        # Neutral Rate: 0.02

        # Setup history for inflation calc
        # Update interval is 5.
        # Tick 0: Price 100.
        # Tick 5: Price 105. (5% increase in 5 ticks -> 100% annual inflation!)
        # Inflation Rate (Annual) = (105-100)/100 * (100/5) = 0.05 * 20 = 1.0 (100%)

        # We need a milder inflation for test.
        # Target 2% annual.
        # Let's say Price 100 at tick 0.
        # Price 100.2 at tick 5.
        # Period Infl = 0.002. Annual = 0.002 * 20 = 0.04 (4%).

        self.tracker.metrics["avg_goods_price"] = [100.0] * 5
        self.tracker.metrics["avg_goods_price"].append(100.2)

        self.tracker.metrics["total_production"] = [100.0] * 6
        self.cb.potential_gdp = 100.0 # No output gap

        # Expected Taylor Rate:
        # i = 0.02 (neutral) + 0.04 (infl) + 1.5 * (0.04 - 0.02) + 0.5 * 0
        # i = 0.06 + 1.5 * 0.02 = 0.06 + 0.03 = 0.09 (9%)

        # But we have smoothing. Max change 0.25% (0.0025).
        # Old rate 0.05. New target 0.09. Delta 0.04.
        # Actual New Rate should be 0.05 + 0.0025 = 0.0525.

        self.cb.step(5)
        self.assertAlmostEqual(self.cb.base_rate, 0.0525)

    def test_recession_cut(self):
        # Scenario: Recession (Low GDP Gap)
        # GDP 90 vs Potential 100 -> Gap -0.1 (-10%)
        # Inflation 2% (Target).

        # Price stable (2% annual growth)
        # 100 -> 100.1 (Period 0.1% -> Annual 2%)
        self.tracker.metrics["avg_goods_price"] = [100.0] * 5
        self.tracker.metrics["avg_goods_price"].append(100.1)

        self.tracker.metrics["total_production"] = [100.0] * 5
        self.tracker.metrics["total_production"].append(90.0)
        self.cb.potential_gdp = 100.0

        # Expected Taylor Rate:
        # i = 0.02 + 0.02 + 1.5*(0) + 0.5*(-0.1)
        # i = 0.04 - 0.05 = -0.01 (-1%)

        # ZLB -> 0.0.
        # Smoothing: 0.05 -> 0.0. Delta -0.05. Max change 0.0025.
        # New Rate: 0.05 - 0.0025 = 0.0475

        self.cb.step(5)
        self.assertAlmostEqual(self.cb.base_rate, 0.0475)

    def test_zlb_enforcement(self):
        # Set rate to very low manually to test floor
        self.cb.base_rate = 0.001

        # Force massive deflation/recession
        # Price drops: 100 -> 90 (-10% period -> -200% annual)
        self.tracker.metrics["avg_goods_price"] = [100.0] * 5
        self.tracker.metrics["avg_goods_price"].append(90.0)

        self.tracker.metrics["total_production"] = [100.0] * 6
        self.cb.potential_gdp = 100.0

        # Target rate will be very negative.
        # Should hit 0.

        self.cb.step(5)
        # With smoothing, it will go down by 0.0025.
        # 0.001 - 0.0025 = -0.0015.
        # Wait, smoothing logic: target = current + max_change * sign.
        # Logic in code: target_rate calculated first (with ZLB).
        # taylor_rate = negative. target_rate = 0.0.
        # delta = 0.0 - 0.001 = -0.001.
        # abs(delta) = 0.001. Max change 0.0025.
        # abs(delta) < max_change? Yes.
        # So we take target_rate (0.0).

        self.assertEqual(self.cb.base_rate, 0.0)

if __name__ == '__main__':
    unittest.main()
