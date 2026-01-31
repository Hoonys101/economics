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

if __name__ == '__main__':
    unittest.main()
