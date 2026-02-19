import pytest
from unittest.mock import MagicMock
from simulation.markets.stock_market import StockMarket
from modules.market.api import CanonicalOrderDTO

class TestStockMarketCancellation:

    @pytest.fixture
    def market(self):
        shareholder_registry = MagicMock()
        config = MagicMock()
        config.STOCK_PRICE_LIMIT_RATE = 0.1
        config.STOCK_BOOK_VALUE_MULTIPLIER = 1.0
        return StockMarket(config_module=config, shareholder_registry=shareholder_registry, logger=MagicMock())

    def test_cancel_orders_removes_agent_orders(self, market):
        # Setup orders
        # Stock market uses firm_id as item_id roughly (stock_100)
        market.reference_prices[100] = 10.0

        order1 = CanonicalOrderDTO(
            agent_id="agent1", side="BUY", item_id="stock_100", quantity=10,
            price_pennies=1000, price_limit=10.0, market_id="stock_market"
        )
        order2 = CanonicalOrderDTO(
            agent_id="agent2", side="BUY", item_id="stock_100", quantity=5,
            price_pennies=1100, price_limit=11.0, market_id="stock_market"
        )
        order3 = CanonicalOrderDTO(
            agent_id="agent1", side="SELL", item_id="stock_100", quantity=5,
            price_pennies=2000, price_limit=20.0, market_id="stock_market"
        )

        market.place_order(order1, 1)
        market.place_order(order2, 1)
        market.place_order(order3, 1)

        assert len(market.buy_orders[100]) == 2
        assert len(market.sell_orders[100]) == 1

        # Cancel agent1 orders
        market.cancel_orders("agent1")

        assert len(market.buy_orders[100]) == 1
        assert market.buy_orders[100][0].order.agent_id == "agent2"
        assert len(market.sell_orders[100]) == 0

    def test_cancel_orders_mixed_int_str_id(self, market):
        # Stock market handles mixed ID types in cancel logic?
        market.reference_prices[100] = 10.0

        order1 = CanonicalOrderDTO(
            agent_id=123, side="BUY", item_id="stock_100", quantity=10,
            price_pennies=1000, price_limit=10.0, market_id="stock_market"
        )
        market.place_order(order1, 1)

        assert len(market.buy_orders[100]) == 1

        # Cancel using string "123"
        market.cancel_orders("123")

        assert len(market.buy_orders[100]) == 0
