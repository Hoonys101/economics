
import unittest
from unittest.mock import MagicMock
from simulation.systems.demographic_manager import DemographicManager
from simulation.core_agents import Household
from simulation.ai.api import Personality
import config  # Import actual config to use defaults where possible

class TestDemographicManagerNewborn(unittest.TestCase):
    def setUp(self):
        # Reset Singleton to ensure clean state
        DemographicManager._instance = None

        # Create a mock config module that mimics actual config structure
        self.config_module = MagicMock()

        # Populate other required config values from the actual config.py to avoid brittleness
        # We iterate over dir(config) to copy over constants
        for key in dir(config):
            if key.isupper():
                setattr(self.config_module, key, getattr(config, key))

        # Define the specific config values we care about for this test
        # Override after copying defaults to ensure this specific value is used
        self.config_module.NEWBORN_INITIAL_NEEDS = {
            "survival": 70.0, # Different from default to verify config usage
            "social": 20.0,
            "improvement": 10.0,
            "asset": 10.0,
            "imitation_need": 15.0,
            "labor_need": 0.0,
            "liquidity_need": 50.0
        }

        # Explicitly ensure MITOSIS_MUTATION_PROBABILITY is set (it should be in config.py, but just in case)
        if not hasattr(self.config_module, "MITOSIS_MUTATION_PROBABILITY"):
             self.config_module.MITOSIS_MUTATION_PROBABILITY = 0.1

        self.manager = DemographicManager(config_module=self.config_module)

        self.simulation = MagicMock()
        self.simulation.next_agent_id = 100
        self.simulation.goods_data = [{"id": "food", "price": 10}]
        self.simulation.markets = {"loan_market": MagicMock()}
        self.simulation.time = 1

        self.simulation.ai_trainer = MagicMock()
        self.simulation.ai_trainer.get_engine.return_value = MagicMock()

    def test_newborn_has_initial_needs_from_config(self):
        parent = MagicMock(spec=Household)
        parent.id = 1
        parent.age = 30
        parent.assets = 1000
        parent.talent = MagicMock()
        parent.personality = MagicMock()
        parent.personality.name = "Conscientious"
        parent.value_orientation = "wealth_and_needs"
        parent.risk_aversion = 0.5
        parent.generation = 1
        parent.children_ids = []
        parent._sub_assets = MagicMock()

        birth_requests = [parent]
        new_children = self.manager.process_births(self.simulation, birth_requests)

        self.assertEqual(len(new_children), 1)
        child = new_children[0]

        # Verify needs match the configured values (specifically "survival": 70.0)
        expected_needs = self.config_module.NEWBORN_INITIAL_NEEDS

        self.assertEqual(child.needs, expected_needs)
        self.assertEqual(child.needs["survival"], 70.0)

if __name__ == '__main__':
    unittest.main()
