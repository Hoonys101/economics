import pytest
from unittest.mock import MagicMock
from simulation.markets.order_book_market import OrderBookMarket
from modules.market.api import CanonicalOrderDTO, IIndexCircuitBreaker

class TestOrderBookMarketCancellation:

    @pytest.fixture
    def market(self):
        mock_breaker = MagicMock(spec=IIndexCircuitBreaker)
        mock_breaker.check_market_health.return_value = True
        mock_breaker.is_active.return_value = False
        return OrderBookMarket(market_id="test_market", logger=MagicMock(), circuit_breaker=mock_breaker)

    def test_cancel_orders_removes_agent_orders(self, market):
        # Setup orders
        order1 = CanonicalOrderDTO(
            agent_id="agent1", side="BUY", item_id="item1", quantity=10,
            price_pennies=1000, price_limit=10.0, market_id="test_market"
        )
        order2 = CanonicalOrderDTO(
            agent_id="agent2", side="BUY", item_id="item1", quantity=5,
            price_pennies=1100, price_limit=11.0, market_id="test_market"
        )
        order3 = CanonicalOrderDTO(
            agent_id="agent1", side="SELL", item_id="item1", quantity=5,
            price_pennies=2000, price_limit=20.0, market_id="test_market"
        )

        market.place_order(order1, 1)
        market.place_order(order2, 1)
        market.place_order(order3, 1)

        assert len(market._buy_orders["item1"]) == 2
        assert len(market._sell_orders["item1"]) == 1

        # Cancel agent1 orders
        market.cancel_orders("agent1")

        assert len(market._buy_orders["item1"]) == 1
        assert market._buy_orders["item1"][0].agent_id == "agent2"
        assert len(market._sell_orders["item1"]) == 0

    def test_cancel_orders_no_effect_if_no_orders(self, market):
         # Setup orders for agent2 only
        order2 = CanonicalOrderDTO(
            agent_id="agent2", side="BUY", item_id="item1", quantity=5,
            price_pennies=1100, price_limit=11.0, market_id="test_market"
        )
        market.place_order(order2, 1)

        market.cancel_orders("agent1")

        assert len(market._buy_orders["item1"]) == 1
        assert market._buy_orders["item1"][0].agent_id == "agent2"
