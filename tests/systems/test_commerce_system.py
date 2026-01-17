import unittest
from unittest.mock import MagicMock
from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.api import CommerceContext

class TestCommerceSystem(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.reflux_system = MagicMock()
        self.system = CommerceSystem(self.config, self.reflux_system)

    def test_execute_consumption_and_leisure(self):
        # Mock households
        h1 = MagicMock()
        h1.id = 1
        h1.is_active = True
        h1.assets = 100.0
        h1.inventory = {}
        h1.children_ids = []
        h1.lifecycle_component = MagicMock() # Mock the component

        households = [h1]

        # Mock breeding planner (VectorizedHouseholdPlanner)
        breeding_planner = MagicMock()
        breeding_planner.decide_consumption_batch.return_value = {
            'consume': [5.0],
            'buy': [2.0],
            'price': 10.0
        }

        # Mock household time allocation
        household_time_allocation = {1: 4.0}

        # Mock market data
        market_data = {}

        context: CommerceContext = {
            'households': households,
            'breeding_planner': breeding_planner,
            'household_time_allocation': household_time_allocation,
            'reflux_system': self.reflux_system,
            'market_data': market_data,
            'config': self.config,
            'time': 10
        }

        # Mock apply_leisure_effect return
        effect_dto = MagicMock()
        effect_dto.utility_gained = 50.0
        effect_dto.leisure_type = "IDLE"
        effect_dto.xp_gained = 0.0
        h1.apply_leisure_effect.return_value = effect_dto

        self.system.execute_consumption_and_leisure(context)

        # Verify Consumption
        h1.consume.assert_any_call("basic_food", 5.0, 10)

        # Verify Purchase (Fast Track)
        self.assertEqual(h1.assets, 80.0)
        self.assertEqual(h1.inventory["basic_food"], 2.0)
        self.reflux_system.capture.assert_called_with(20.0, source="Household_1", category="emergency_food")

        # Verify Leisure
        h1.apply_leisure_effect.assert_called_with(4.0, {'basic_food': 5.0})

        # Verify Lifecycle Update - NOW CALLS COMPONENT DIRECTLY
        # h1.update_needs.assert_called_with(10, market_data) # Removed
        h1.lifecycle_component.run_tick.assert_called()

        # Verify context passed to run_tick
        args, _ = h1.lifecycle_component.run_tick.call_args
        lifecycle_context = args[0]
        self.assertEqual(lifecycle_context['household'], h1)
        self.assertEqual(lifecycle_context['time'], 10)

        # Verify Transient Utility Attached
        self.assertEqual(h1.last_leisure_utility, 50.0)
