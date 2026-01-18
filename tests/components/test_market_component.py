import unittest
from unittest.mock import MagicMock
from simulation.components.market_component import MarketComponent
from simulation.core_agents import Household

class TestMarketComponent(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        # Fix: explicitly set config values to avoid MagicMock comparison issues
        self.config.BRAND_SENSITIVITY_BETA = 0.5

        self.owner = MagicMock(spec=Household)
        self.owner.quality_preference = 0.5
        self.owner.brand_loyalty = {}
        self.component = MarketComponent(self.owner, self.config)

    def test_choose_best_seller(self):
        market = MagicMock()
        # Create Mock Orders
        order1 = MagicMock()
        order1.agent_id = 101
        order1.price = 10.0
        order1.brand_info = {"perceived_quality": 1.0, "brand_awareness": 0.0}

        order2 = MagicMock()
        order2.agent_id = 102
        order2.price = 20.0 # Expensive
        order2.brand_info = {"perceived_quality": 2.0, "brand_awareness": 0.1}

        market.get_all_asks.return_value = [order1, order2]

        context = {"markets": {"apple": market}}

        # Without loyalty, cheaper might win depending on utility function
        # U = (Q^0.5 * 1) / P
        # O1: 1^0.5 / 10 = 0.1
        # O2: 2^0.5 / 20 = 1.414 / 20 = 0.07
        # O1 wins

        seller_id, price = self.component.choose_best_seller("apple", context)
        self.assertEqual(seller_id, 101)
        self.assertEqual(price, 10.0)

if __name__ == '__main__':
    unittest.main()
