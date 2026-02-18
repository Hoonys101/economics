import pytest
from simulation.models import Order
from simulation.markets.order_book_market import OrderBookMarket

def test_order_book_matching(simple_market):
    """Spec 1: OrderBookMarket 매칭 로직 검증"""
    buy_order = Order(agent_id=1, item_id='basic_food', price_pennies=int(10.0 * 100), price_limit=10.0, quantity=1.0, side='BUY', market_id='basic_food')
    sell_order = Order(agent_id=101, item_id='basic_food', price_pennies=int(9.0 * 100), price_limit=9.0, quantity=1.0, side='SELL', market_id='basic_food')
    simple_market.place_order(buy_order, current_time=1)
    simple_market.place_order(sell_order, current_time=1)
    transactions = simple_market.match_orders(current_time=1)
    assert len(transactions) == 1
    tx = transactions[0]
    assert tx.item_id == 'basic_food'
    assert tx.buyer_id == 1
    assert tx.seller_id == 101
    assert tx.quantity == 1.0
    assert tx.price == 9.5