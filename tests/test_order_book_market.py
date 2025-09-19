import pytest
from unittest.mock import MagicMock, patch

from simulation.markets.order_book_market import OrderBookMarket
from simulation.models import Order, Transaction

# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('simulation.markets.order_book_market.logging.getLogger') as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance

@pytest.fixture
def goods_market_instance():
    return OrderBookMarket(market_id="goods_market")

@pytest.fixture
def labor_market_instance(mock_logger):
    return OrderBookMarket(market_id="labor_market", logger=mock_logger)

@pytest.fixture
def order_book_market_instance(): # Keep this for general tests
    return OrderBookMarket(market_id="test_market")

@pytest.fixture
def sample_buy_order():
    return Order(agent_id=1, order_type='BUY', item_id='food', quantity=10, price=100, market_id='test_market')

@pytest.fixture
def sample_sell_order():
    return Order(agent_id=2, order_type='SELL', item_id='food', quantity=10, price=90, market_id='test_market')

class TestOrderBookMarket:
    def test_initialization(self, order_book_market_instance):
        assert order_book_market_instance.market_id == "test_market"
        assert order_book_market_instance.buy_orders == {}
        assert order_book_market_instance.sell_orders == {}
        assert order_book_market_instance.transactions == []

    def test_place_buy_order_adds_and_sorts(self, order_book_market_instance):
        order1 = Order(agent_id=1, order_type='BUY', item_id='food', quantity=10, price=100, market_id='test_market')
        order2 = Order(agent_id=2, order_type='BUY', item_id='food', quantity=5, price=110, market_id='test_market')
        order_book_market_instance.place_order(order1, 1)
        order_book_market_instance.place_order(order2, 1)
        
        buy_book = order_book_market_instance.buy_orders.get('food', [])
        assert len(buy_book) == 2
        assert buy_book[0].price == 110 # Sorted descending
        assert buy_book[1].price == 100

    def test_place_sell_order_adds_and_sorts(self, order_book_market_instance):
        order1 = Order(agent_id=1, order_type='SELL', item_id='food', quantity=10, price=100, market_id='test_market')
        order2 = Order(agent_id=2, order_type='SELL', item_id='food', quantity=5, price=90, market_id='test_market')
        order_book_market_instance.place_order(order1, 1)
        order_book_market_instance.place_order(order2, 1)
        
        sell_book = order_book_market_instance.sell_orders.get('food', [])
        assert len(sell_book) == 2
        assert sell_book[0].price == 90 # Sorted ascending
        assert sell_book[1].price == 100

    def test_place_order_unknown_type_logs_warning(self, order_book_market_instance, mock_logger):
        order = Order(agent_id=1, order_type='UNKNOWN', item_id='food', quantity=10, price=100, market_id='test_market')
        order_book_market_instance.place_order(order, 1)
        
        mock_logger.warning.assert_called_with("Unknown order type: UNKNOWN", extra={'tick': 1, 'market_id': 'test_market', 'agent_id': 1, 'item_id': 'food', 'order_type': 'UNKNOWN'})
        assert mock_logger.warning.call_count == 2 # Expect two calls
        assert order_book_market_instance.buy_orders == {}
        assert order_book_market_instance.sell_orders == {}

    def test_place_order_clears_transactions(self, order_book_market_instance):
        # Simulate a previous transaction
        order_book_market_instance.transactions.append(Transaction(buyer_id=1, seller_id=2, item_id="food", quantity=1, price=1, transaction_type="goods", time=0, market_id="test_market"))
        
        order = Order(agent_id=1, order_type='BUY', item_id='food', quantity=10, price=100, market_id='test_market')
        order_book_market_instance.place_order(order, 1)
        
        # Verify transactions list is cleared at the beginning of place_order
        assert order_book_market_instance.transactions == []

    def test_match_orders_full_fill(self, goods_market_instance):
        buy_order = Order(agent_id=1, order_type='BUY', item_id='food', quantity=10, price=100, market_id='goods_market')
        sell_order = Order(agent_id=2, order_type='SELL', item_id='food', quantity=10, price=90, market_id='goods_market')
        goods_market_instance.buy_orders['food'] = [buy_order]
        goods_market_instance.sell_orders['food'] = [sell_order]

        goods_market_instance._match_orders('food', 1)

        assert len(goods_market_instance.transactions) == 1
        tx = goods_market_instance.transactions[0]
        assert tx.buyer_id == 1
        assert tx.seller_id == 2
        assert tx.item_id == "food"
        assert tx.quantity == 10
        assert tx.price == 95.0 # (100+90)/2
        assert tx.transaction_type == "goods"
        assert tx.time == 1

        assert not goods_market_instance.buy_orders.get('food')
        assert not goods_market_instance.sell_orders.get('food')

    def test_match_orders_partial_fill_buy_order(self, goods_market_instance):
        buy_order = Order(agent_id=1, order_type='BUY', item_id='food', quantity=15, price=100, market_id='goods_market')
        sell_order = Order(agent_id=2, order_type='SELL', item_id='food', quantity=10, price=90, market_id='goods_market')
        goods_market_instance.buy_orders['food'] = [buy_order]
        goods_market_instance.sell_orders['food'] = [sell_order]

        goods_market_instance._match_orders('food', 1)

        assert len(goods_market_instance.transactions) == 1
        tx = goods_market_instance.transactions[0]
        assert tx.quantity == 10

        buy_book = goods_market_instance.buy_orders.get('food')
        assert len(buy_book) == 1
        assert buy_book[0].quantity == 5
        assert not goods_market_instance.sell_orders.get('food')

    def test_match_orders_partial_fill_sell_order(self, goods_market_instance):
        buy_order = Order(agent_id=1, order_type='BUY', item_id='food', quantity=10, price=100, market_id='goods_market')
        sell_order = Order(agent_id=2, order_type='SELL', item_id='food', quantity=15, price=90, market_id='goods_market')
        goods_market_instance.buy_orders['food'] = [buy_order]
        goods_market_instance.sell_orders['food'] = [sell_order]

        goods_market_instance._match_orders('food', 1)

        assert len(goods_market_instance.transactions) == 1
        tx = goods_market_instance.transactions[0]
        assert tx.quantity == 10

        sell_book = goods_market_instance.sell_orders.get('food')
        assert len(sell_book) == 1
        assert sell_book[0].quantity == 5
        assert not goods_market_instance.buy_orders.get('food')

    def test_match_orders_no_match_price(self, goods_market_instance):
        buy_order = Order(agent_id=1, order_type='BUY', item_id='food', quantity=10, price=80, market_id='goods_market')
        sell_order = Order(agent_id=2, order_type='SELL', item_id='food', quantity=10, price=90, market_id='goods_market')
        goods_market_instance.buy_orders['food'] = [buy_order]
        goods_market_instance.sell_orders['food'] = [sell_order]

        goods_market_instance._match_orders('food', 1)

        assert not goods_market_instance.transactions
        assert len(goods_market_instance.buy_orders.get('food')) == 1
        assert len(goods_market_instance.sell_orders.get('food')) == 1

    def test_match_orders_multiple_matches(self, goods_market_instance):
        buy_order = Order(agent_id=1, order_type='BUY', item_id='food', quantity=20, price=100, market_id='goods_market')
        sell_order1 = Order(agent_id=2, order_type='SELL', item_id='food', quantity=5, price=90, market_id='goods_market')
        sell_order2 = Order(agent_id=3, order_type='SELL', item_id='food', quantity=8, price=95, market_id='goods_market')
        goods_market_instance.buy_orders['food'] = [buy_order]
        goods_market_instance.sell_orders['food'] = [sell_order1, sell_order2]

        goods_market_instance._match_orders('food', 1)

        assert len(goods_market_instance.transactions) == 2
        assert goods_market_instance.transactions[0].quantity == 5
        assert goods_market_instance.transactions[1].quantity == 8
        assert buy_order.quantity == 7 # 20 - 5 - 8
        assert not goods_market_instance.sell_orders.get('food')

    def test_match_orders_different_items(self, goods_market_instance):
        buy_order_food = Order(agent_id=1, order_type='BUY', item_id='food', quantity=10, price=100, market_id='goods_market')
        sell_order_food = Order(agent_id=2, order_type='SELL', item_id='food', quantity=10, price=90, market_id='goods_market')
        buy_order_water = Order(agent_id=3, order_type='BUY', item_id='water', quantity=5, price=50, market_id='goods_market')
        sell_order_water = Order(agent_id=4, order_type='SELL', item_id='water', quantity=5, price=40, market_id='goods_market')

        goods_market_instance.buy_orders['food'] = [buy_order_food]
        goods_market_instance.sell_orders['food'] = [sell_order_food]
        goods_market_instance.buy_orders['water'] = [buy_order_water]
        goods_market_instance.sell_orders['water'] = [sell_order_water]

        goods_market_instance._match_orders('food', 1)
        goods_market_instance._match_orders('water', 1)

        assert len(goods_market_instance.transactions) == 2
        assert goods_market_instance.transactions[0].item_id == 'food'
        assert goods_market_instance.transactions[1].item_id == 'water'

    def test_match_orders_empty_books(self, order_book_market_instance):
        order_book_market_instance._match_orders('food', 1)
        assert not order_book_market_instance.transactions
        assert not order_book_market_instance.buy_orders.get('food')
        assert not order_book_market_instance.sell_orders.get('food')

    def test_match_orders_transaction_type_goods(self, goods_market_instance):
        buy_order = Order(agent_id=1, order_type='BUY', item_id='food', quantity=10, price=100, market_id='goods_market')
        sell_order = Order(agent_id=2, order_type='SELL', item_id='food', quantity=10, price=90, market_id='goods_market')
        goods_market_instance.buy_orders['food'] = [buy_order]
        goods_market_instance.sell_orders['food'] = [sell_order]

        goods_market_instance._match_orders('food', 1)
        assert goods_market_instance.transactions[0].transaction_type == "goods"

    def test_match_orders_transaction_type_labor(self, labor_market_instance, mock_logger):
        buy_order = Order(agent_id=1, order_type='BUY', item_id='labor', quantity=1, price=20, market_id='labor_market')
        sell_order = Order(agent_id=2, order_type='SELL', item_id='labor', quantity=1, price=15, market_id='labor_market')
        labor_market_instance.buy_orders['labor'] = [buy_order]
        labor_market_instance.sell_orders['labor'] = [sell_order]

        labor_market_instance._match_orders('labor', 1)
        assert labor_market_instance.transactions[0].transaction_type == "labor"

    def test_get_best_ask_empty(self, order_book_market_instance):
        assert order_book_market_instance.get_best_ask('food') is None

    def test_get_best_ask_non_empty(self, order_book_market_instance):
        order_book_market_instance.place_order(Order(1, 'SELL', 'food', 10, 100, 'test_market'), 1)
        order_book_market_instance.place_order(Order(2, 'SELL', 'food', 5, 90, 'test_market'), 1)
        assert order_book_market_instance.get_best_ask('food') == 90

    def test_get_best_bid_empty(self, order_book_market_instance):
        assert order_book_market_instance.get_best_bid('food') is None

    def test_get_best_bid_non_empty(self, order_book_market_instance):
        order_book_market_instance.place_order(Order(1, 'BUY', 'food', 10, 100, 'test_market'), 1)
        order_book_market_instance.place_order(Order(2, 'BUY', 'food', 5, 110, 'test_market'), 1)
        assert order_book_market_instance.get_best_bid('food') == 110

    def test_get_order_book_status_empty(self, order_book_market_instance):
        status = order_book_market_instance.get_order_book_status('food')
        assert status['buy_orders'] == []
        assert status['sell_orders'] == []

    def test_get_order_book_status_non_empty(self, order_book_market_instance):
        order_book_market_instance.place_order(Order(1, 'BUY', 'food', 10, 90, 'test_market'), 1) # Max buy price 90
        order_book_market_instance.place_order(Order(2, 'SELL', 'food', 5, 100, 'test_market'), 1) # Min sell price 100
        status = order_book_market_instance.get_order_book_status('food')
        assert len(status['buy_orders']) == 1
        assert status['buy_orders'][0]['price'] == 90
        assert len(status['sell_orders']) == 1
        assert status['sell_orders'][0]['price'] == 100

