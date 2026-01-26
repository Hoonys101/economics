import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import unittest
from unittest.mock import MagicMock
from simulation.core_agents import Household, Talent
from simulation.ai.api import Personality
from simulation.decisions.base_decision_engine import BaseDecisionEngine
import config

class TestStep1Foundation(unittest.TestCase):
    def setUp(self):
        self.mock_decision_engine = MagicMock(spec=BaseDecisionEngine)
        # Mocking config module with necessary attributes if they are dynamic,
        # but importing real config is safer for constant checking.

        self.agent = Household(
            id=1,
            talent=Talent(0.1, {}),
            goods_data=[],
            initial_assets=1000.0,
            initial_needs={},
            decision_engine=self.mock_decision_engine,
            value_orientation="wealth_and_needs",
            personality=Personality.CONSERVATIVE,
            config_module=config
        )

    def test_household_attributes(self):
        print(f"Testing Household Attributes...")
        print(f"Gender: {self.agent.gender}")
        self.assertIn(self.agent.gender, ["M", "F"])

        print(f"Spouse ID: {self.agent.spouse_id}")
        self.assertIsNone(self.agent.spouse_id) # Should be None initially

        print(f"Home Quality Score: {self.agent.home_quality_score}")
        self.assertEqual(self.agent.home_quality_score, 1.0)

        print("System2 Planner exists:", self.agent.system2_planner is not None)
        self.assertIsNotNone(self.agent.system2_planner)

    def test_system2_planner_execution(self):
        print("Testing System2 Planner Execution...")
        market_data = {
            "goods_market": {
                "basic_food_current_sell_price": 5.0
            }
        }
        # Run projection
        result = self.agent.system2_planner.project_future(100, market_data)

        print("Projection Result:", result)
        self.assertIn("npv_wealth", result)
        self.assertIn("bankruptcy_tick", result)
        self.assertIn("survival_prob", result)

        # Basic Logic Check: Wealth should change
        # If wealth=1000, daily_income=80, daily_cost=10, net=70.
        # NPV should be > 1000.
        self.assertGreater(result["npv_wealth"], 1000.0)

if __name__ == "__main__":
    unittest.main()
