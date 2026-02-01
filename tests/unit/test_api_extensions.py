import pytest
from unittest.mock import MagicMock
from simulation.viewmodels.economic_indicators_viewmodel import EconomicIndicatorsViewModel
from simulation.core_markets import Market
from simulation.markets.order_book_market import OrderBookMarket
from simulation.models import Order

@pytest.fixture
def vm():
    repo = MagicMock()
    return EconomicIndicatorsViewModel(repo)

class TestEconomicIndicatorsViewModel:
    def test_get_wealth_distribution(self, vm, golden_households, golden_firms):
        # State Override Pattern: Use golden fixtures but override state
        # We need 3 households and 2 firms to match original test expectations

        # Ensure we have enough mocks. If not, create them (defensive).
        households = (golden_households[:3] if len(golden_households) >= 3
                      else [MagicMock() for _ in range(3)])
        firms = (golden_firms[:2] if len(golden_firms) >= 2
                 else [MagicMock() for _ in range(2)])

        # Override assets
        households[0]._assets = 10
        households[1]._assets = 20
        households[2]._assets = 100

        firms[0]._assets = 50
        firms[1]._assets = 10

        # Total assets: 10, 20, 100, 50, 10
        # Min: 10, Max: 100
        # Buckets should cover 10-100

        dist = vm.get_wealth_distribution(households, firms)
        assert "labels" in dist
        assert "data" in dist
        assert len(dist["data"]) == 10
        assert sum(dist["data"]) == 5 # 5 agents

    def test_get_needs_distribution(self, vm, golden_households, golden_firms):
        # Need 2 households and 1 firm
        h1 = golden_households[0] if golden_households else MagicMock()
        h2 = golden_households[1] if len(golden_households) > 1 else MagicMock()
        f1 = golden_firms[0] if golden_firms else MagicMock()

        # State Override
        h1.needs = {"food": 10, "shelter": 5}
        h2.needs = {"food": 20, "shelter": 15}
        f1.needs = {"liquidity_need": 100.0}

        households = [h1, h2]
        firms = [f1]

        dist = vm.get_needs_distribution(households, firms)
        assert dist["household"]["food"] == 15.0 # (10+20)/2
        assert dist["household"]["shelter"] == 10.0 # (5+15)/2
        assert dist["firm"]["liquidity_need"] == 100.0

    def test_get_sales_by_good(self, vm):
        txs = [
            {"item_id": "apple", "quantity": 10},
            {"item_id": "banana", "quantity": 5},
            {"item_id": "apple", "quantity": 5}
        ]
        sales = vm.get_sales_by_good(txs)
        assert sales["apple"] == 15
        assert sales["banana"] == 5

    def test_get_market_order_book(self, vm):
        market = OrderBookMarket("test_market")
        # Manually inject orders for testing
        market.buy_orders = {
            "apple": [Order(agent_id=1, side="BUY", market_id="test_market", item_id="apple", quantity=10, price_limit=5)]
        }
        market.sell_orders = {
            "apple": [Order(agent_id=2, side="SELL", market_id="test_market", item_id="apple", quantity=5, price_limit=6)]
        }

        markets = {"test_market": market}
        book = vm.get_market_order_book(markets)

        assert len(book) == 2
        # Check types
        types = [o["type"] for o in book]
        assert "BID" in types
        assert "ASK" in types
