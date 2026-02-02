import unittest
from unittest.mock import MagicMock, PropertyMock
import logging
from simulation.core_agents import Household, Talent
from simulation.ai.system2_planner import System2Planner
from simulation.ai.api import Personality
import config
from tests.utils.factories import create_household_config_dto

class TestPhase20Scaffolding(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test")
        self.mock_decision_engine = MagicMock()
        self.mock_loan_market = MagicMock()

        # Talent mock
        self.talent = Talent(base_learning_rate=0.1, max_potential={})

        # Household init args
        self.household_args = {
            "id": 1,
            "talent": self.talent,
            "goods_data": [],
            "initial_assets": 1000.0,
            "initial_needs": {},
            "decision_engine": self.mock_decision_engine,
            "value_orientation": "wealth_and_needs",
            "personality": Personality.CONSERVATIVE,
            "config_dto": create_household_config_dto(),
            "loan_market": self.mock_loan_market,
            "logger": self.logger
        }

    def test_household_attributes_initialization(self):
        """Verify gender and home_quality_score initialization."""
        h1 = Household(**self.household_args)

        # Check gender
        self.assertIn(h1.gender, ["M", "F"])

        # Check home_quality_score
        self.assertEqual(h1.home_quality_score, 1.0)

        # Check System2Planner existence
        # self.assertIsInstance(h1.system2_planner, System2Planner)

        # Check get_agent_data includes gender
        data = h1.get_agent_data()
        self.assertIn("gender", data)
        self.assertEqual(data["gender"], h1.gender)
        self.assertEqual(h1._bio_state.generation, 0)

    def test_gender_distribution(self):
        """Verify roughly 50:50 distribution (probabilistic)."""
        m_count = 0
        f_count = 0
        for i in range(100):
            h = Household(**{**self.household_args, "id": i})
            if h._bio_state.gender == "M":
                m_count += 1
            else:
                f_count += 1

        # It's random, but should not be 0 or 100 usually.
        self.assertGreater(m_count, 0)
        self.assertGreater(f_count, 0)
        print(f"Gender Distribution (N=100): M={m_count}, F={f_count}")

    def test_system2_planner_projection_positive(self):
        """Verify System2Planner positive projection logic."""
        # Create a mock agent for the planner
        mock_agent = MagicMock()
        type(mock_agent).assets = PropertyMock(return_value=1000.0)
        mock_agent._assets = 1000.0
        mock_agent.expected_wage = 10.0
        mock_agent.children_ids = []
        mock_agent.spouse_id = None
        mock_agent.decision_engine = MagicMock()
        mock_agent.decision_engine.ai_engine = None
        mock_agent.get_agent_data.return_value = {"assets": 1000.0, "gender": "M", "children_count": 0}

        planner = System2Planner(mock_agent, config)

        market_data = {
            "goods_market": {
                "basic_food_current_sell_price": 5.0
            },
            "housing_market": {
                "avg_rent_price": 0.0 # Disable rent for this test
            }
        }

        # Config check
        # HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 2.0 (from config)
        # Wage = 10.0, Hours = 8.0 -> Income = 80.0
        # Food Price = 5.0, Qty = 2.0 -> Expense = 10.0
        # Net Flow = +70.0

        result = planner.project_future(0, market_data)
        npv = result["npv_wealth"]
        bankruptcy_tick = result["bankruptcy_tick"]

        self.assertIsNone(bankruptcy_tick, "Should not go bankrupt with positive flow")
        self.assertGreater(npv, 1000.0, "NPV should be greater than initial assets with positive flow")

    def test_system2_planner_projection_bankruptcy(self):
        """Verify System2Planner bankruptcy detection."""
        # Create a mock agent for the planner
        mock_agent = MagicMock()
        type(mock_agent).assets = PropertyMock(return_value=100.0)
        mock_agent._assets = 100.0
        mock_agent.expected_wage = 0.0 # No income
        mock_agent.children_ids = []
        mock_agent.spouse_id = None
        mock_agent.decision_engine = MagicMock()
        mock_agent.decision_engine.ai_engine = None
        mock_agent.get_agent_data.return_value = {"assets": 100.0, "gender": "M", "children_count": 0}

        planner = System2Planner(mock_agent, config)

        market_data = {
            "goods_market": {
                "basic_food_current_sell_price": 10.0
            },
            "housing_market": {
                "avg_rent_price": 0.0 # Disable rent for this test
            }
        }

        # Expense = 10.0 * 2.0 = 20.0 per tick
        # Assets = 100.0
        # Should survive 5 ticks
        # T=1: 100 - 20 = 80
        # T=2: 60
        # T=3: 40
        # T=4: 20
        # T=5: 0
        # T=6: -20 (Bankrupt)

        result = planner.project_future(0, market_data)
        bankruptcy_tick = result["bankruptcy_tick"]

        self.assertEqual(bankruptcy_tick, 6)

if __name__ == '__main__':
    unittest.main()
