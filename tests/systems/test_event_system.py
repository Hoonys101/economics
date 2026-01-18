import unittest
from unittest.mock import MagicMock
from simulation.systems.event_system import EventSystem

class TestEventSystem(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.system = EventSystem(self.config)

    def test_inflation_shock(self):
        market = MagicMock()
        market.current_price = 10.0
        market.avg_price = 10.0

        context = {
            "markets": {"goods": market},
            "households": [],
            "firms": []
        }

        self.system.execute_scheduled_events(200, context)

        self.assertEqual(market.current_price, 15.0)
        self.assertEqual(market.avg_price, 15.0)

    def test_recession_shock(self):
        household = MagicMock()
        household.assets = 1000.0

        context = {
            "markets": {},
            "households": [household],
            "firms": []
        }

        self.system.execute_scheduled_events(600, context)

        self.assertEqual(household.assets, 500.0)

if __name__ == '__main__':
    unittest.main()
