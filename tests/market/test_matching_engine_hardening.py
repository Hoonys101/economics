import pytest
from unittest.mock import MagicMock
from simulation.markets.matching_engine import OrderBookMatchingEngine, StockMatchingEngine
from modules.market.api import CanonicalOrderDTO, OrderBookStateDTO, StockMarketStateDTO
from simulation.models import Transaction

class TestMatchingEngineHardening:

    def test_order_book_matching_integer_math(self):
        engine = OrderBookMatchingEngine()

        # Scenario: Buyer wants 0.1 units at $10.05 (1005 pennies)
        # Seller sells 0.1 units at $10.05 (1005 pennies)
        # Expected total pennies: 1005 * 0.1 = 100.5 -> 100 pennies (int cast)

        buy_order = CanonicalOrderDTO(
            agent_id="buyer_1",
            side="BUY",
            item_id="item_1",
            quantity=0.1,
            price_pennies=1005,
            price_limit=10.05,
            market_id="goods"
        )

        sell_order = CanonicalOrderDTO(
            agent_id="seller_1",
            side="SELL",
            item_id="item_1",
            quantity=0.1,
            price_pennies=1005, # Matching price
            price_limit=10.05,
            market_id="goods"
        )

        state = OrderBookStateDTO(
            buy_orders={"item_1": [buy_order]},
            sell_orders={"item_1": [sell_order]},
            market_id="goods"
        )

        result = engine.match(state, current_tick=1)

        assert len(result.transactions) == 1
        tx = result.transactions[0]

        # Verify total_pennies is calculated correctly as int(1005 * 0.1) = 100
        assert tx.total_pennies == 100
        assert tx.quantity == 0.1
        # Effective price should be derived from total_pennies: 100 / 0.1 / 100 = 10.0
        # Original price was 10.05. The effective price is slightly different due to integer rounding.
        assert tx.price == 10.0

    def test_stock_matching_mid_price_rounding(self):
        engine = StockMatchingEngine()

        # Scenario:
        # Buyer bids $10.01 (1001 pennies)
        # Seller asks $10.00 (1000 pennies)
        # Mid price: (1001 + 1000) // 2 = 2001 // 2 = 1000 pennies

        buy_order = CanonicalOrderDTO(
            agent_id=1,
            side="BUY",
            item_id="stock_1",
            quantity=1.0,
            price_pennies=1001,
            price_limit=10.01,
            market_id="stock"
        )

        sell_order = CanonicalOrderDTO(
            agent_id=2,
            side="SELL",
            item_id="stock_1",
            quantity=1.0,
            price_pennies=1000,
            price_limit=10.00,
            market_id="stock"
        )

        state = StockMarketStateDTO(
            buy_orders={1: [buy_order]},
            sell_orders={1: [sell_order]},
            market_id="stock"
        )

        result = engine.match(state, current_tick=1)

        assert len(result.transactions) == 1
        tx = result.transactions[0]

        # Trade price should be 1000 pennies
        # Total pennies: 1000 * 1 = 1000
        assert tx.total_pennies == 1000
        assert tx.price == 10.00

    def test_small_quantity_zero_pennies(self):
        engine = OrderBookMatchingEngine()

        # Scenario: Very small quantity resulting in 0 pennies
        # Price: 100 pennies ($1.00)
        # Quantity: 0.001
        # Total: 100 * 0.001 = 0.1 -> 0 pennies

        buy_order = CanonicalOrderDTO(
            agent_id="buyer_2",
            side="BUY",
            item_id="item_2",
            quantity=0.001,
            price_pennies=100,
            price_limit=1.00,
            market_id="goods"
        )

        sell_order = CanonicalOrderDTO(
            agent_id="seller_2",
            side="SELL",
            item_id="item_2",
            quantity=0.001,
            price_pennies=100,
            price_limit=1.00,
            market_id="goods"
        )

        state = OrderBookStateDTO(
            buy_orders={"item_2": [buy_order]},
            sell_orders={"item_2": [sell_order]},
            market_id="goods"
        )

        result = engine.match(state, current_tick=1)

        assert len(result.transactions) == 1
        tx = result.transactions[0]

        assert tx.total_pennies == 0
        assert tx.quantity == 0.001
        assert tx.price == 0.0
