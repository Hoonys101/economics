
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add repository root to path
sys.path.append(os.getcwd())

from simulation.systems.demographic_manager import DemographicManager
from simulation.core_agents import Household

class TestBirthLeak(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock()
        self.mock_config.REPRODUCTION_AGE_START = 20
        self.mock_config.REPRODUCTION_AGE_END = 45
        self.mock_config.NEWBORN_ENGINE_TYPE = "AIDriven"
        self.mock_config.MITOSIS_MUTATION_PROBABILITY = 0.1
        self.mock_config.NEWBORN_INITIAL_NEEDS = {"survival": 10.0}

        self.mock_sim = MagicMock()
        self.mock_sim.next_agent_id = 100
        self.mock_sim.time = 1
        self.mock_sim.markets = {"loan_market": MagicMock()}
        self.mock_sim.goods_data = []
        self.mock_sim.ai_trainer.get_engine.return_value = MagicMock()
        self.mock_sim.ai_training_manager = MagicMock()

        self.manager = DemographicManager(config_module=self.mock_config)

    def test_atomic_rollback_on_failure(self):
        """
        Verify that if child creation fails, parent assets are restored (Leak = 0).
        """
        print("\n[Test] Atomic Rollback on Failure")

        # Parent with 1000 assets
        parent = MagicMock(spec=Household)
        parent.id = 1
        parent.age = 30
        parent.assets = 1000.0
        parent.talent = MagicMock()
        parent.personality = "MOCK_PERSONALITY"
        parent.value_orientation = "TRADITIONAL"
        parent.risk_aversion = 0.5
        parent.generation = 1
        parent.children_ids = []

        # Mock _sub_assets to actually decrease mocked assets
        def sub_assets(amount):
            parent.assets -= amount
        parent._sub_assets.side_effect = sub_assets

        # Mock _add_assets to actually increase mocked assets (for rollback)
        def add_assets(amount):
            parent.assets += amount
        parent._add_assets.side_effect = add_assets

        # Patch Household to raise Exception
        with patch("simulation.systems.demographic_manager.Household", side_effect=Exception("Simulated Creation Failure")):

            # Run process_births
            # Expectation: Exception caught (or not?), assets restored.
            # Current code: Exception propagates or (if I fix it) caught and refunded.
            # Since current code does NOT catch, this test might crash or show leak if I catch it externally.

            try:
                self.manager.process_births(self.mock_sim, [parent])
            except Exception as e:
                print(f"Caught expected exception: {e}")

            # Verify Assets
            print(f"Parent Assets after failure: {parent.assets}")

            # If leak exists (current behavior):
            # parent.assets = 1000 - 100 = 900. (Money destroyed).
            # If fixed:
            # parent.assets = 1000.

            if parent.assets == 1000.0:
                print("SUCCESS: No leak detected (Rollback worked).")
            else:
                print(f"FAILURE: Leak detected! Assets missing: {1000.0 - parent.assets}")

            self.assertEqual(parent.assets, 1000.0, f"Leak detected! Parent has {parent.assets}, expected 1000.0")

    def test_insufficient_funds_adjustment(self):
        """
        Verify that if parent has low funds, gift is adjusted (prevent negative).
        Though 10% is always feasible, we test boundary logic.
        """
        print("\n[Test] Insufficient Funds Adjustment")

        parent = MagicMock(spec=Household)
        parent.id = 2
        parent.age = 30
        parent.assets = 5.0 # Low assets
        parent.talent = MagicMock()
        parent.personality = "MOCK_PERSONALITY"
        parent.value_orientation = "TRADITIONAL"
        parent.risk_aversion = 0.5
        parent.children_ids = []
        parent.generation = 1

        # Mock assets
        def sub_assets(amount):
            parent.assets -= amount
        parent._sub_assets.side_effect = sub_assets

        # We need successful creation here
        with patch("simulation.systems.demographic_manager.Household") as MockChild:
            mock_child_instance = MagicMock()
            MockChild.return_value = mock_child_instance

            # Capture initial_assets passed to child

            self.manager.process_births(self.mock_sim, [parent])

            # Verify child received 10% (0.5)
            # Or if we implement "adjust", maybe different.
            # Currently 0.5 is fine.

            args, kwargs = MockChild.call_args
            initial_assets = kwargs.get('initial_assets')
            print(f"Parent Assets: 5.0 -> Child Init Assets: {initial_assets}")

            # Verify conservation
            # Parent should have 4.5
            self.assertAlmostEqual(parent.assets, 4.5)
            self.assertAlmostEqual(initial_assets, 0.5)
            print("SUCCESS: Assets conserved (Standard case).")

if __name__ == "__main__":
    unittest.main()
