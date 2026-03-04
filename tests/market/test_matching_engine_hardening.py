import pytest
from unittest.mock import MagicMock
from simulation.markets.matching_engine import OrderBookMatchingEngine, StockMatchingEngine
from modules.market.api import CanonicalOrderDTO, OrderBookStateDTO, StockMarketStateDTO
from simulation.models import Transaction


class TestMatchingEngineHardening:

    def test_order_book_matching_integer_math(self):
        engine = OrderBookMatchingEngine()
        buy_order = CanonicalOrderDTO(agent_id='buyer_1', side='BUY',
            item_id='item_1', quantity=0.1, price_pennies=1005, market_id=
            'goods')
        sell_order = CanonicalOrderDTO(agent_id='seller_1', side='SELL',
            item_id='item_1', quantity=0.1, price_pennies=1005, market_id=
            'goods')
        state = OrderBookStateDTO(buy_orders={'item_1': [buy_order]},
            sell_orders={'item_1': [sell_order]}, market_id='goods')
        result = engine.match(state, current_tick=1)
        assert len(result.transactions) == 1
        tx = result.transactions[0]
        assert tx.total_pennies == 100
        assert tx.quantity == 0.1
        assert tx.price == 10.0

    def test_stock_matching_mid_price_rounding(self):
        engine = StockMatchingEngine()
        buy_order = CanonicalOrderDTO(agent_id=1, side='BUY', item_id=
            'stock_1', quantity=1.0, price_pennies=1001, market_id='stock')
        sell_order = CanonicalOrderDTO(agent_id=2, side='SELL', item_id=
            'stock_1', quantity=1.0, price_pennies=1000, market_id='stock')
        state = StockMarketStateDTO(buy_orders={(1): [buy_order]},
            sell_orders={(1): [sell_order]}, market_id='stock')
        result = engine.match(state, current_tick=1)
        assert len(result.transactions) == 1
        tx = result.transactions[0]
        assert tx.total_pennies == 1000
        assert tx.price == 10.0

    def test_small_quantity_zero_pennies(self):
        engine = OrderBookMatchingEngine()
        buy_order = CanonicalOrderDTO(agent_id='buyer_2', side='BUY',
            item_id='item_2', quantity=0.001, price_pennies=100, market_id=
            'goods')
        sell_order = CanonicalOrderDTO(agent_id='seller_2', side='SELL',
            item_id='item_2', quantity=0.001, price_pennies=100, market_id=
            'goods')
        state = OrderBookStateDTO(buy_orders={'item_2': [buy_order]},
            sell_orders={'item_2': [sell_order]}, market_id='goods')
        result = engine.match(state, current_tick=1)
        assert len(result.transactions) == 1
        tx = result.transactions[0]
        assert tx.total_pennies == 0
        assert tx.quantity == 0.001
        assert tx.price == 0.0
