import pytest
from simulation.markets.matching_engine import OrderBookMatchingEngine
from modules.market.api import OrderBookStateDTO, CanonicalOrderDTO
from simulation.models import Transaction

def test_market_zero_sum_integer():
    engine = OrderBookMatchingEngine()
    buy_order = CanonicalOrderDTO(agent_id='buyer', side='BUY', item_id='item1', quantity=1.0, price_pennies=100, market_id='test')
    sell_order = CanonicalOrderDTO(agent_id='seller', side='SELL', item_id='item1', quantity=1.0, price_pennies=99, market_id='test')
    state = OrderBookStateDTO(buy_orders={'item1': [buy_order]}, sell_orders={'item1': [sell_order]}, market_id='test')
    result = engine.match(state, current_tick=1)
    assert len(result.transactions) == 1
    tx = result.transactions[0]
    assert tx.total_pennies == 99
    assert tx.price == 0.99

def test_market_fractional_qty_rounding():
    engine = OrderBookMatchingEngine()
    buy_order = CanonicalOrderDTO(agent_id='buyer', side='BUY', item_id='item1', quantity=0.33, price_pennies=10, market_id='test')
    sell_order = CanonicalOrderDTO(agent_id='seller', side='SELL', item_id='item1', quantity=0.33, price_pennies=10, market_id='test')
    state = OrderBookStateDTO(buy_orders={'item1': [buy_order]}, sell_orders={'item1': [sell_order]}, market_id='test')
    result = engine.match(state, current_tick=1)
    tx = result.transactions[0]
    assert tx.total_pennies == 3
    assert tx.price == pytest.approx((3 / 0.33) / 100.0, abs=1e-5)

def test_labor_market_pricing():
    engine = OrderBookMatchingEngine()
    buy_order = CanonicalOrderDTO(agent_id='buyer', side='BUY', item_id='labor_1', quantity=1.0, price_pennies=1000, market_id='labor')
    sell_order = CanonicalOrderDTO(agent_id='seller', side='SELL', item_id='labor_1', quantity=1.0, price_pennies=900, market_id='labor')
    state = OrderBookStateDTO(buy_orders={'labor_1': [buy_order]}, sell_orders={'labor_1': [sell_order]}, market_id='labor')
    result = engine.match(state, current_tick=1)
    tx = result.transactions[0]
    assert tx.total_pennies == 1000
