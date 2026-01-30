import unittest
from unittest.mock import MagicMock
from simulation.ai.household_system2 import HouseholdSystem2Planner, HousingDecisionInputs
from simulation.core_agents import Household
from simulation.ai.api import Personality
from collections import deque
from tests.utils.factories import create_household_config_dto

class TestHouseholdSystem2(unittest.TestCase):
    def setUp(self):
        self.mock_agent = MagicMock()
        self.mock_config = MagicMock()
        self.mock_config.HOUSING_EXPECTATION_CAP = 0.05
        # Fix mock config list issue
        self.mock_config.EDUCATION_LEVEL_DISTRIBUTION = [1.0]
        self.planner = HouseholdSystem2Planner(self.mock_agent, self.mock_config)

    def test_npv_buy_calculation(self):
        # Scenario: Low Price, Low Rent, High Income -> Likely Buy
        inputs = HousingDecisionInputs(
            current_wealth=100000.0,
            annual_income=60000.0,
            market_rent_monthly=1000.0,
            market_price=200000.0,
            risk_free_rate=0.03,
            price_growth_expectation=0.04
        )

        result = self.planner.calculate_housing_npv(inputs)

        # Verify Formulas
        self.assertIn("npv_buy", result)
        self.assertIn("npv_rent", result)
        self.assertIsInstance(result["npv_buy"], float)
        self.assertIsInstance(result["npv_rent"], float)

    def test_dti_guardrail(self):
        # Scenario: Income too low for price
        inputs = HousingDecisionInputs(
            current_wealth=100000.0,
            annual_income=10000.0, # Very low income
            market_rent_monthly=500.0,
            market_price=500000.0, # Very high price
            risk_free_rate=0.05,
            price_growth_expectation=0.04
        )

        # Should return RENT
        decision = self.planner.decide(inputs)
        self.assertEqual(decision, "RENT")

    def test_rational_choice_buy(self):
         # Scenario: Buy is clearly better (Low Interest, High Growth)
         inputs = HousingDecisionInputs(
            current_wealth=500000.0,
            annual_income=100000.0,
            market_rent_monthly=2000.0, # High rent makes renting expensive
            market_price=300000.0, # Cheap house
            risk_free_rate=0.02, # Low interest
            price_growth_expectation=0.05 # High growth cap
        )
         decision = self.planner.decide(inputs)
         self.assertEqual(decision, "BUY")

    def test_household_integration(self):
        # Create real household (mocked config/decision engine)
        mock_decision_engine = MagicMock()
        mock_decision_engine.ai_engine = MagicMock() # Mock nested ai_engine

        # Configure Config Mock for Household Init
        self.mock_config.EDUCATION_LEVEL_DISTRIBUTION = [1.0]
        self.mock_config.VALUE_ORIENTATION_MAPPING = {
            "wealth_and_needs": {"preference_asset": 1.0, "preference_social": 1.0, "preference_growth": 1.0}
        }
        self.mock_config.CONFORMITY_RANGES = {}
        self.mock_config.INFLATION_MEMORY_WINDOW = 10
        self.mock_config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 10000.0
        self.mock_config.TICKS_PER_YEAR = 100

        household = Household(
            id=1,
            talent=MagicMock(),
            goods_data=[],
            initial_assets=50000.0,
            initial_needs={},
            decision_engine=mock_decision_engine,
            value_orientation="wealth_and_needs",
            personality=Personality.CONSERVATIVE,
            config_dto=create_household_config_dto()
        )

        # Override planner with mock to verify call
        household.housing_planner = MagicMock()
        household.housing_planner.decide.return_value = "BUY" # Force BUY decision

        # Trigger Condition: tick 30
        market_data = {
            "housing_market": {"avg_rent_price": 100.0, "avg_sale_price": 20000.0},
            "loan_market": {"interest_rate": 0.05}
        }

        # 1. Verify Trigger
        household.decide_housing(market_data, 30)
        household.housing_planner.decide.assert_called_once()
        self.assertEqual(household.housing_target_mode, "BUY")
        self.assertEqual(len(household.housing_price_history), 1)

        # 2. Verify Execution (BUY -> Order)
        # Mock decision engine to return empty list
        mock_decision_engine.make_decisions.return_value = ([], (MagicMock(), MagicMock()))

        # Set up a fake housing market with a sell order
        mock_market = MagicMock()
        mock_order = MagicMock()
        mock_order.price = 10000.0
        mock_market.sell_orders = {"unit_1": [mock_order]}
        markets = {"housing": mock_market}

        household.is_homeless = True # Trigger Execution logic
        orders, _ = household.make_decision(markets, [], market_data, 30, None)

        # Check if BUY order was appended
        found_housing_buy = any(o.market_id == "housing" and o.order_type == "BUY" and o.item_id == "unit_1" for o in orders)
        self.assertTrue(found_housing_buy, "Should generate BUY order for housing when mode is BUY and homeless")

if __name__ == '__main__':
    unittest.main()
