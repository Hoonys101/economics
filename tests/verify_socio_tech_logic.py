import unittest
from unittest.mock import MagicMock
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.api import BaseAIEngine

# Mock Config
class MockConfig:
    HOUSEWORK_BASE_HOURS = 6.0
    FORMULA_TECH_LEVEL = 0.0

class TestHouseholdAI_TimeAllocation(unittest.TestCase):
    def setUp(self):
        self.ai = HouseholdAI("test_agent", None)
        # Mock the AI decision engine reference to return our config
        self.ai.ai_decision_engine = MagicMock()
        self.ai.ai_decision_engine.config_module = MockConfig()

    def test_single_male_no_infant(self):
        agent_data = {"gender": "M", "home_quality_score": 1.0}
        allocation = self.ai.decide_time_allocation(agent_data, config_module=MockConfig())

        # Expect full housework (6.0), no childcare
        self.assertEqual(allocation["housework"], 6.0)
        self.assertEqual(allocation["childcare"], 0.0)

    def test_couple_female_infant_no_tech(self):
        MockConfig.FORMULA_TECH_LEVEL = 0.0
        agent_data = {"gender": "F", "home_quality_score": 1.0}
        spouse_data = {"id": "spouse"}
        children_data = [{"age": 1}] # Infant

        allocation = self.ai.decide_time_allocation(
            agent_data, spouse_data, children_data, config_module=MockConfig()
        )

        # Housework shared (3.0), Childcare LOCKED to Female (8.0)
        self.assertEqual(allocation["housework"], 3.0)
        self.assertEqual(allocation["childcare"], 8.0)

    def test_couple_male_infant_no_tech(self):
        MockConfig.FORMULA_TECH_LEVEL = 0.0
        agent_data = {"gender": "M", "home_quality_score": 1.0}
        spouse_data = {"id": "spouse"}
        children_data = [{"age": 1}]

        allocation = self.ai.decide_time_allocation(
            agent_data, spouse_data, children_data, config_module=MockConfig()
        )

        # Housework shared (3.0), Childcare 0 (Lactation Lock)
        self.assertEqual(allocation["housework"], 3.0)
        self.assertEqual(allocation["childcare"], 0.0)

    def test_couple_female_infant_with_tech(self):
        MockConfig.FORMULA_TECH_LEVEL = 1.0
        agent_data = {"gender": "F", "home_quality_score": 1.0}
        spouse_data = {"id": "spouse"}
        children_data = [{"age": 1}]

        allocation = self.ai.decide_time_allocation(
            agent_data, spouse_data, children_data, config_module=MockConfig()
        )

        # Housework shared (3.0), Childcare SHARED (4.0)
        self.assertEqual(allocation["housework"], 3.0)
        self.assertEqual(allocation["childcare"], 4.0)

    def test_appliance_benefit(self):
        agent_data = {"gender": "F", "home_quality_score": 1.5} # High Quality -> Appliances

        allocation = self.ai.decide_time_allocation(agent_data, config_module=MockConfig())

        # Base 6.0 * 0.5 = 3.0
        self.assertEqual(allocation["housework"], 3.0)

if __name__ == "__main__":
    unittest.main()
