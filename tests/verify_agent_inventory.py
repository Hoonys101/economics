import sys
import os
import unittest
from unittest.mock import MagicMock, Mock
from typing import Dict, Any

# Add module path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.base_agent import BaseAgent
from modules.simulation.api import IInventoryHandler

# Mock dependencies
class MockDecisionEngine:
    def __init__(self, *args, **kwargs): pass

class TestInventoryPurity(unittest.TestCase):
    def test_base_agent_protocol(self):
        class SimpleAgent(BaseAgent):
            def update_needs(self, t): pass
            def make_decision(self, dto): return [], None
            def clone(self, *args): return self
            def get_agent_data(self): return {}

        agent = SimpleAgent(1, 100.0, {}, MockDecisionEngine(), "neutral")

        # Test Inventory Property Removal
        try:
            _ = agent.inventory
            self.fail("BaseAgent.inventory property should have been removed")
        except AttributeError:
            pass # Expected

        # Test Protocol
        self.assertTrue(isinstance(agent, IInventoryHandler))
        self.assertEqual(agent.get_quantity("item_A"), 0.0)
        self.assertEqual(agent.get_quality("item_A"), 1.0)

        # Test Add
        agent.add_item("item_A", 10.0)
        self.assertEqual(agent.get_quantity("item_A"), 10.0)

        # Test Remove
        agent.remove_item("item_A", 5.0)
        self.assertEqual(agent.get_quantity("item_A"), 5.0)

        # Test Insufficient Remove
        result = agent.remove_item("item_A", 10.0)
        self.assertFalse(result)
        self.assertEqual(agent.get_quantity("item_A"), 5.0)

if __name__ == '__main__':
    unittest.main()
