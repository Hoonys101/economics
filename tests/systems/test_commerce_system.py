import unittest
from unittest.mock import MagicMock
from simulation.systems.commerce_system import CommerceSystem
from simulation.core_agents import Household
from simulation.dtos import LeisureEffectDTO

class TestCommerceSystem(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.FOOD_CONSUMPTION_QUANTITY = 1.0 # Fix: Set config value to avoid MagicMock return

        self.reflux_system = MagicMock()
        self.system = CommerceSystem(self.config, self.reflux_system)
        self.breeding_planner = MagicMock()
        self.households = [MagicMock(spec=Household), MagicMock(spec=Household)]

        # Setup Households
        for i, h in enumerate(self.households):
            h.id = i
            h.is_active = True
            h.inventory = {}
            h.assets = 1000.0
            # Mock methods
            h.apply_leisure_effect.return_value = LeisureEffectDTO(
                leisure_type="REST", utility_gained=5.0, xp_gained=0.0, leisure_hours=8.0
            )

    def test_execute_consumption_and_leisure(self):
        # Mock Vectorized Planner Output
        self.breeding_planner.decide_consumption_batch.return_value = {
            'consume': [1.0, 0.0], # H0 consumes
            'buy': [0.0, 1.0],     # H1 buys
            'price': 10.0
        }

        context = {
            "households": self.households,
            "breeding_planner": self.breeding_planner,
            "household_time_allocation": {0: 8.0, 1: 8.0},
            "market_data": {},
            "time": 1,
            "reflux_system": self.reflux_system
        }

        self.system.execute_consumption_and_leisure(context)

        # Verify H0 Consumed
        self.households[0].consume.assert_called_with("basic_food", 1.0, 1)

        # Verify H1 Bought (Asset reduced, Inventory increased, Reflux capture)
        self.assertEqual(self.households[1].assets, 990.0) # 1000 - 10
        self.assertEqual(self.households[1].inventory["basic_food"], 1.0)
        self.reflux_system.capture.assert_called()

        # Verify Lifecycle Called
        self.households[0].update_needs.assert_called()
        self.households[1].update_needs.assert_called()

if __name__ == '__main__':
    unittest.main()
