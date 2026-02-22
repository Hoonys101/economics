import unittest
from unittest.mock import MagicMock
from simulation.systems.system_effects_manager import SystemEffectsManager
from simulation.dtos.api import SimulationState

class TestSystemEffectsManagerMajorChoice(unittest.TestCase):
    def test_major_choice_on_education_upgrade(self):
        # Setup
        mock_config = MagicMock()
        # Mock labor_market.majors
        mock_config.LABOR_MARKET = {
            "majors": ["GENERAL", "AGRICULTURE", "MANUFACTURING", "SERVICES", "TECHNOLOGY"]
        }

        manager = SystemEffectsManager(mock_config)

        # Create Household
        household = MagicMock()
        household.id = 101
        household._econ_state.education_level = 0
        household._econ_state.major = "GENERAL" # Default

        # State
        state = MagicMock(spec=SimulationState)
        state.time = 100
        state.agents = {101: household}
        state.effects_queue = [
            {
                "triggers_effect": "EDUCATION_UPGRADE",
                "target_agent_id": 101
            }
        ]

        # Execute
        manager.process_effects(state)

        # Assert - NEW behavior
        print(f"Education Level: {household._econ_state.education_level}")
        print(f"Major: {household._econ_state.major}")

        self.assertEqual(household._econ_state.education_level, 1)
        self.assertNotEqual(household._econ_state.major, "GENERAL")
        self.assertIn(household._econ_state.major, ["AGRICULTURE", "MANUFACTURING", "SERVICES", "TECHNOLOGY"])

    def test_sunk_cost_major_choice(self):
        # Ensure major is NOT changed if already specialized
        mock_config = MagicMock()
        mock_config.LABOR_MARKET = {
            "majors": ["GENERAL", "AGRICULTURE", "MANUFACTURING", "SERVICES", "TECHNOLOGY"]
        }

        manager = SystemEffectsManager(mock_config)

        household = MagicMock()
        household.id = 102
        household._econ_state.education_level = 1
        household._econ_state.major = "TECHNOLOGY" # Already specialized

        state = MagicMock(spec=SimulationState)
        state.time = 200
        state.agents = {102: household}
        state.effects_queue = [
            {
                "triggers_effect": "EDUCATION_UPGRADE",
                "target_agent_id": 102
            }
        ]

        manager.process_effects(state)

        self.assertEqual(household._econ_state.education_level, 2)
        # Should remain TECHNOLOGY
        self.assertEqual(household._econ_state.major, "TECHNOLOGY")

if __name__ == "__main__":
    unittest.main()
