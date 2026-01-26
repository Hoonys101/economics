import unittest
import sys
from pathlib import Path
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from app import app, create_simulation
from simulation.ai.api import Personality
import config

class TestNeedsFluctuation(unittest.TestCase):
    def setUp(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO)

        # Initialize app context
        self.app = app
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Initialize simulation
        create_simulation()
        from app import simulation_instance
        self.simulation = simulation_instance

        # Force a household to have specific personality and state
        self.household = self.simulation.households[0]
        # Use a valid personality
        self.household.personality = Personality.MISER
        self.household.needs['survival'] = 50.0
        self.household.inventory['basic_food'] = 5.0 # Give food so they can consume

        # Ensure utility effects are loaded (relying on my app.py fix)
        # We can check this
        if 'utility_effects' not in self.household.goods_info_map.get('basic_food', {}):
             print("WARNING: utility_effects missing in goods_info_map!")

    def tearDown(self):
        self.ctx.pop()

    def test_needs_increase_over_time(self):
        """Verify that needs increase over time (base growth) when not consuming."""
        initial_survival = self.household.needs['survival']

        # Run 1 tick without consumption (force empty inventory to test growth only?
        # But I gave inventory above. Let's remove it for this test)
        self.household.inventory['basic_food'] = 0.0

        self.simulation.run_tick()

        new_survival = self.household.needs['survival']
        # Expect increase: base_growth (1.0)
        expected_increase = config.BASE_DESIRE_GROWTH

        print(f"Initial Survival: {initial_survival}, New Survival: {new_survival}")
        self.assertTrue(new_survival > initial_survival, "Survival need should increase")
        self.assertAlmostEqual(new_survival, initial_survival + expected_increase, delta=0.1)

    def test_consumption_reduces_needs(self):
        """Verify that consumption reduces needs."""
        # Set high need to trigger consumption
        self.household.needs['survival'] = 80.0
        self.household.inventory['basic_food'] = 5.0

        initial_survival = self.household.needs['survival']

        self.simulation.run_tick()

        new_survival = self.household.needs['survival']
        print(f"Initial Survival: {initial_survival}, New Survival: {new_survival}")

        # Utility of basic_food is 10 (survival). Base growth is 1.
        # Expected: 80 - 10 + 1 = 71.
        # Check if it decreased
        self.assertTrue(new_survival < initial_survival, "Survival need should decrease after consumption")

if __name__ == '__main__':
    unittest.main()
