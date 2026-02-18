import pytest
from unittest.mock import MagicMock, patch
from simulation.markets.order_book_market import OrderBookMarket
from simulation.models import Order

@pytest.fixture(autouse=True)
def mock_logger():
    with patch('simulation.markets.order_book_market.logging.getLogger') as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance

@pytest.fixture
def goods_market_instance():
    return OrderBookMarket(market_id='goods_market')

@pytest.fixture
def labor_market_instance(mock_logger):
    return OrderBookMarket(market_id='labor_market', logger=mock_logger)

@pytest.fixture
def order_book_market_instance():
    return OrderBookMarket(market_id='test_market')

@pytest.fixture
def sample_buy_order():
    return Order(agent_id=1, side='BUY', item_id='food', quantity=10, price_pennies=int(100 * 100), price_limit=100, market_id='test_market')

@pytest.fixture
def sample_sell_order():
    return Order(agent_id=2, side='SELL', item_id='food', quantity=10, price_pennies=int(90 * 100), price_limit=90, market_id='test_market')

class TestOrderBookMarket:

    def test_initialization(self, order_book_market_instance):
        assert order_book_market_instance.id == 'test_market'
        assert order_book_market_instance.buy_orders == {}
        assert order_book_market_instance.sell_orders == {}

    def test_place_buy_order_adds_and_sorts(self, order_book_market_instance):
        order1 = Order(agent_id=1, side='BUY', item_id='food', quantity=10, price_pennies=int(100 * 100), price_limit=100, market_id='test_market')
        order2 = Order(agent_id=2, side='BUY', item_id='food', quantity=5, price_pennies=int(110 * 100), price_limit=110, market_id='test_market')
        order_book_market_instance.place_order(order1, 1)
        order_book_market_instance.place_order(order2, 1)
        buy_book = order_book_market_instance.buy_orders.get('food', [])
        assert len(buy_book) == 2
        assert buy_book[0].price == 110
        assert buy_book[1].price == 100

    def test_place_sell_order_adds_and_sorts(self, order_book_market_instance):
        order1 = Order(agent_id=1, side='SELL', item_id='food', quantity=10, price_pennies=int(100 * 100), price_limit=100, market_id='test_market')
        order2 = Order(agent_id=2, side='SELL', item_id='food', quantity=5, price_pennies=int(90 * 100), price_limit=90, market_id='test_market')
        order_book_market_instance.place_order(order1, 1)
        order_book_market_instance.place_order(order2, 1)
        sell_book = order_book_market_instance.sell_orders.get('food', [])
        assert len(sell_book) == 2
        assert sell_book[0].price == 90
        assert sell_book[1].price == 100

    def test_place_order_unknown_type_logs_warning(self, order_book_market_instance, mock_logger):
        order = Order(agent_id=1, side='UNKNOWN', item_id='food', quantity=10, price_pennies=int(100 * 100), price_limit=100, market_id='test_market')
        order_book_market_instance.place_order(order, 1)
        mock_logger.warning.assert_called_with('Unknown side for _add_order: UNKNOWN', extra={'tick': 1, 'market_id': 'test_market', 'agent_id': 1, 'item_id': 'food', 'side': 'UNKNOWN', 'price': 100, 'quantity': 10})
        assert mock_logger.warning.call_count == 1
        assert order_book_market_instance.buy_orders == {}
        assert order_book_market_instance.sell_orders == {}

    def test_match_orders_full_fill(self, goods_market_instance):
        buy_order = Order(agent_id=1, side='BUY', item_id='food', quantity=10, price_pennies=int(100 * 100), price_limit=100, market_id='goods_market')
        sell_order = Order(agent_id=2, side='SELL', item_id='food', quantity=10, price_pennies=int(90 * 100), price_limit=90, market_id='goods_market')
        goods_market_instance.place_order(buy_order, 1)
        goods_market_instance.place_order(sell_order, 1)
        transactions = goods_market_instance.match_orders(1)
        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.buyer_id == 1
        assert tx.seller_id == 2
        assert tx.item_id == 'food'
        assert tx.quantity == 10
        assert tx.price == 95.0
        assert tx.transaction_type == 'goods'
        assert tx.time == 1
        assert not goods_market_instance.buy_orders.get('food')
        assert not goods_market_instance.sell_orders.get('food')

    def test_match_orders_partial_fill_buy_order(self, goods_market_instance):
        buy_order = Order(agent_id=1, side='BUY', item_id='food', quantity=15, price_pennies=int(100 * 100), price_limit=100, market_id='goods_market')
        sell_order = Order(agent_id=2, side='SELL', item_id='food', quantity=10, price_pennies=int(90 * 100), price_limit=90, market_id='goods_market')
        goods_market_instance.place_order(buy_order, 1)
        goods_market_instance.place_order(sell_order, 1)
        transactions = goods_market_instance.match_orders(1)
        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.quantity == 10
        buy_book = goods_market_instance.buy_orders.get('food', [])
        assert len(buy_book) == 1
        assert buy_book[0].quantity == 5
        assert not goods_market_instance.sell_orders.get('food', [])

    def test_match_orders_partial_fill_sell_order(self, goods_market_instance):
        buy_order = Order(agent_id=1, side='BUY', item_id='food', quantity=10, price_pennies=int(100 * 100), price_limit=100, market_id='goods_market')
        sell_order = Order(agent_id=2, side='SELL', item_id='food', quantity=15, price_pennies=int(90 * 100), price_limit=90, market_id='goods_market')
        goods_market_instance.place_order(buy_order, 1)
        goods_market_instance.place_order(sell_order, 1)
        transactions = goods_market_instance.match_orders(1)
        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.quantity == 10
        sell_book = goods_market_instance.sell_orders.get('food', [])
        assert len(sell_book) == 1
        assert sell_book[0].quantity == 5
        assert not goods_market_instance.buy_orders.get('food', [])

    def test_match_orders_no_match_price(self, goods_market_instance):
        buy_order = Order(agent_id=1, side='BUY', item_id='food', quantity=10, price_pennies=int(80 * 100), price_limit=80, market_id='goods_market')
        sell_order = Order(agent_id=2, side='SELL', item_id='food', quantity=10, price_pennies=int(90 * 100), price_limit=90, market_id='goods_market')
        goods_market_instance.place_order(buy_order, 1)
        goods_market_instance.place_order(sell_order, 1)
        transactions = goods_market_instance.match_orders(1)
        assert not transactions
        assert len(goods_market_instance.buy_orders.get('food', [])) == 1
        assert len(goods_market_instance.sell_orders.get('food', [])) == 1

    def test_match_orders_multiple_matches(self, goods_market_instance):
        buy_order = Order(agent_id=1, side='BUY', item_id='food', quantity=20, price_pennies=int(100 * 100), price_limit=100, market_id='goods_market')
        sell_order1 = Order(agent_id=2, side='SELL', item_id='food', quantity=5, price_pennies=int(90 * 100), price_limit=90, market_id='goods_market')
        sell_order2 = Order(agent_id=3, side='SELL', item_id='food', quantity=8, price_pennies=int(95 * 100), price_limit=95, market_id='goods_market')
        goods_market_instance.place_order(buy_order, 1)
        goods_market_instance.place_order(sell_order1, 1)
        goods_market_instance.place_order(sell_order2, 1)
        transactions = goods_market_instance.match_orders(1)
        assert len(transactions) == 2
        assert transactions[0].quantity == 5
        assert transactions[1].quantity == 8
        remaining_orders = goods_market_instance.buy_orders.get('food', [])
        assert len(remaining_orders) == 1
        assert remaining_orders[0].quantity == 7
        assert remaining_orders[0].agent_id == 1
        assert not goods_market_instance.sell_orders.get('food', [])

    def test_match_orders_different_items(self, goods_market_instance):
        buy_order_food = Order(agent_id=1, side='BUY', item_id='food', quantity=10, price_pennies=int(100 * 100), price_limit=100, market_id='goods_market')
        sell_order_food = Order(agent_id=2, side='SELL', item_id='food', quantity=10, price_pennies=int(90 * 100), price_limit=90, market_id='goods_market')
        buy_order_water = Order(agent_id=3, side='BUY', item_id='water', quantity=5, price_pennies=int(50 * 100), price_limit=50, market_id='goods_market')
        sell_order_water = Order(agent_id=4, side='SELL', item_id='water', quantity=5, price_pennies=int(40 * 100), price_limit=40, market_id='goods_market')
        goods_market_instance.place_order(buy_order_food, 1)
        goods_market_instance.place_order(sell_order_food, 1)
        goods_market_instance.place_order(buy_order_water, 1)
        goods_market_instance.place_order(sell_order_water, 1)
        transactions = goods_market_instance.match_orders(1)
        assert len(transactions) == 2
        food_tx = next((tx for tx in transactions if tx.item_id == 'food'), None)
        water_tx = next((tx for tx in transactions if tx.item_id == 'water'), None)
        assert food_tx is not None
        assert water_tx is not None

    def test_match_orders_empty_books(self, order_book_market_instance):
        transactions = order_book_market_instance.match_orders(1)
        assert not transactions
        assert not order_book_market_instance.buy_orders.get('food', [])
        assert not order_book_market_instance.sell_orders.get('food', [])

    def test_match_orders_transaction_type_goods(self, goods_market_instance):
        buy_order = Order(agent_id=1, side='BUY', item_id='food', quantity=10, price_pennies=int(100 * 100), price_limit=100, market_id='goods_market')
        sell_order = Order(agent_id=2, side='SELL', item_id='food', quantity=10, price_pennies=int(90 * 100), price_limit=90, market_id='goods_market')
        goods_market_instance.place_order(buy_order, 1)
        goods_market_instance.place_order(sell_order, 1)
        transactions = goods_market_instance.match_orders(1)
        assert transactions[0].transaction_type == 'goods'

    def test_match_orders_transaction_type_labor(self, labor_market_instance, mock_logger):
        buy_order = Order(agent_id=1, side='BUY', item_id='labor', quantity=1, price_pennies=int(20 * 100), price_limit=20, market_id='labor_market')
        sell_order = Order(agent_id=2, side='SELL', item_id='labor', quantity=1, price_pennies=int(15 * 100), price_limit=15, market_id='labor_market')
        labor_market_instance.place_order(buy_order, 1)
        labor_market_instance.place_order(sell_order, 1)
        transactions = labor_market_instance.match_orders(1)
        assert transactions[0].transaction_type == 'labor'

    def test_get_best_ask_empty(self, order_book_market_instance):
        assert order_book_market_instance.get_best_ask('food') is None

    def test_get_best_ask_non_empty(self, order_book_market_instance):
        order_book_market_instance.place_order(Order(1, 'SELL', 'food', 10, int(100 * 100), 100, 'test_market'), 1)
        order_book_market_instance.place_order(Order(2, 'SELL', 'food', 5, int(90 * 100), 90, 'test_market'), 1)
        assert order_book_market_instance.get_best_ask('food') == 90

    def test_get_best_bid_empty(self, order_book_market_instance):
        assert order_book_market_instance.get_best_bid('food') is None

    def test_get_best_bid_non_empty(self, order_book_market_instance):
        order_book_market_instance.place_order(Order(1, 'BUY', 'food', 10, int(100 * 100), 100, 'test_market'), 1)
        order_book_market_instance.place_order(Order(2, 'BUY', 'food', 5, int(110 * 100), 110, 'test_market'), 1)
        assert order_book_market_instance.get_best_bid('food') == 110

    def test_get_order_book_status_empty(self, order_book_market_instance):
        status = order_book_market_instance.get_order_book_status('food')
        assert status['buy_orders'] == []
        assert status['sell_orders'] == []

    def test_get_order_book_status_non_empty(self, order_book_market_instance):
        order_book_market_instance.place_order(Order(1, 'BUY', 'food', 10, int(90 * 100), 90, 'test_market'), 1)
        order_book_market_instance.place_order(Order(2, 'SELL', 'food', 5, int(100 * 100), 100, 'test_market'), 1)
        status = order_book_market_instance.get_order_book_status('food')
        assert len(status['buy_orders']) == 1
        assert status['buy_orders'][0]['price'] == 90
        assert len(status['sell_orders']) == 1
        assert status['sell_orders'][0]['price'] == 100