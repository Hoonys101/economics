import unittest
from unittest.mock import MagicMock
from simulation.viewmodels.economic_indicators_viewmodel import EconomicIndicatorsViewModel
from simulation.core_markets import Market
from simulation.markets.order_book_market import OrderBookMarket
from simulation.models import Order

class TestEconomicIndicatorsViewModel(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.vm = EconomicIndicatorsViewModel(self.repo)

    def test_get_wealth_distribution(self):
        households = [MagicMock(assets=10), MagicMock(assets=20), MagicMock(assets=100)]
        firms = [MagicMock(assets=50), MagicMock(assets=10)]

        # Total assets: 10, 20, 100, 50, 10
        # Min: 10, Max: 100
        # Buckets should cover 10-100

        dist = self.vm.get_wealth_distribution(households, firms)
        self.assertIn("labels", dist)
        self.assertIn("data", dist)
        self.assertEqual(len(dist["data"]), 10)
        self.assertEqual(sum(dist["data"]), 5) # 5 agents

    def test_get_needs_distribution(self):
        h1 = MagicMock()
        h1.needs = {"food": 10, "shelter": 5}
        h2 = MagicMock()
        h2.needs = {"food": 20, "shelter": 15}
        households = [h1, h2]

        # Updated Firm Mock to have 'needs' dict
        f1 = MagicMock()
        f1.needs = {"liquidity_need": 100.0}
        firms = [f1]

        dist = self.vm.get_needs_distribution(households, firms)
        self.assertEqual(dist["household"]["food"], 15.0) # (10+20)/2
        self.assertEqual(dist["household"]["shelter"], 10.0) # (5+15)/2
        self.assertEqual(dist["firm"]["liquidity_need"], 100.0)

    def test_get_sales_by_good(self):
        txs = [
            {"item_id": "apple", "quantity": 10},
            {"item_id": "banana", "quantity": 5},
            {"item_id": "apple", "quantity": 5}
        ]
        sales = self.vm.get_sales_by_good(txs)
        self.assertEqual(sales["apple"], 15)
        self.assertEqual(sales["banana"], 5)

    def test_get_market_order_book(self):
        market = OrderBookMarket("test_market")
        # Manually inject orders for testing since we might not want to depend on exact OrderBookMarket implementation logic here if complex
        # But we used buy_orders dict in vm. Let's mock it.

        market.buy_orders = {
            "apple": [Order(agent_id=1, order_type="BUY", market_id="test_market", item_id="apple", quantity=10, price=5)]
        }
        market.sell_orders = {
            "apple": [Order(agent_id=2, order_type="SELL", market_id="test_market", item_id="apple", quantity=5, price=6)]
        }

        markets = {"test_market": market}
        book = self.vm.get_market_order_book(markets)

        self.assertEqual(len(book), 2)
        # Check types
        types = [o["type"] for o in book]
        self.assertIn("BID", types)
        self.assertIn("ASK", types)

if __name__ == '__main__':
    unittest.main()
