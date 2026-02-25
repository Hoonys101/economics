"""
Stock Market Unit Tests (Refactored for Immutable OrderDTO)

Testing Strategy:
- Black-box testing via public API (place_order, match_orders, get_market_summary).
- Verification of state changes rather than internal object mutation.
- Use of OrderDTO for all interactions.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from simulation.markets.stock_market import StockMarket
from modules.market.api import OrderDTO, IIndexCircuitBreaker
from simulation.models import Transaction

@pytest.fixture
def mock_config(golden_config):
    config = golden_config if golden_config is not None else Mock()
    config.STOCK_MARKET_ENABLED = True
    config.STOCK_PRICE_LIMIT_RATE = 0.15
    config.STOCK_BOOK_VALUE_MULTIPLIER = 1.0
    config.STOCK_MIN_ORDER_QUANTITY = 1.0
    config.STOCK_ORDER_EXPIRY_TICKS = 5
    config.STOCK_TRANSACTION_FEE_RATE = 0.001
    return config

@pytest.fixture
def stock_market(mock_config):
    registry = MagicMock()
    mock_breaker = MagicMock(spec=IIndexCircuitBreaker)
    mock_breaker.check_market_health.return_value = True
    mock_breaker.is_active.return_value = False
    return StockMarket(config_module=mock_config, shareholder_registry=registry, index_circuit_breaker=mock_breaker)

@pytest.fixture
def sample_buy_order_dto():
    return OrderDTO(agent_id=1, side='BUY', item_id='stock_100', quantity=10.0, price_limit=50.0, price_pennies=5000, market_id='stock_market')

@pytest.fixture
def sample_sell_order_dto():
    return OrderDTO(agent_id=2, side='SELL', item_id='stock_100', quantity=10.0, price_limit=45.0, price_pennies=4500, market_id='stock_market')

class TestStockMarketInitialization:

    def test_initialization(self, stock_market):
        assert stock_market.id == 'stock_market'
        summary = stock_market.get_market_summary(100)
        assert summary['buy_order_count'] == 0
        assert summary['sell_order_count'] == 0

    def test_update_reference_prices(self, stock_market, golden_firms):
        mock_firm = golden_firms[0]
        mock_firm.id = 100
        mock_firm.is_active = True
        mock_firm.get_book_value_per_share = Mock(return_value=80.0)
        firms = {100: mock_firm}
        stock_market.update_reference_prices(firms)
        assert stock_market.reference_prices[100] == 80.0

class TestStockOrderPlacement:

    def test_place_buy_order(self, stock_market, sample_buy_order_dto):
        stock_market.reference_prices[100] = 50.0
        stock_market.place_order(sample_buy_order_dto, tick=1)
        summary = stock_market.get_market_summary(100)
        assert summary['buy_order_count'] == 1
        assert stock_market.get_best_bid(100) == 50.0

    def test_place_sell_order(self, stock_market, sample_sell_order_dto):
        stock_market.reference_prices[100] = 50.0
        stock_market.place_order(sample_sell_order_dto, tick=1)
        summary = stock_market.get_market_summary(100)
        assert summary['sell_order_count'] == 1
        assert stock_market.get_best_ask(100) == 45.0

    def test_price_clamping(self, stock_market):
        firm_id = 100
        stock_market.reference_prices[firm_id] = 100.0
        high_order = OrderDTO(agent_id=1, side='BUY', item_id=f'stock_{firm_id}', quantity=1.0, price_limit=120.0, price_pennies=12000, market_id='stock')
        stock_market.place_order(high_order, tick=1)
        best_bid = stock_market.get_best_bid(firm_id)
        assert best_bid == pytest.approx(115.0)
        low_order = OrderDTO(agent_id=1, side='SELL', item_id=f'stock_{firm_id}', quantity=1.0, price_limit=80.0, price_pennies=8000, market_id='stock')
        stock_market.place_order(low_order, tick=1)
        best_ask = stock_market.get_best_ask(firm_id)
        assert best_ask == pytest.approx(85.0)

    def test_order_sorting(self, stock_market):
        firm_id = 100
        stock_market.reference_prices[firm_id] = 50.0
        o1 = OrderDTO(agent_id=1, side='BUY', item_id=f'stock_{firm_id}', quantity=1.0, price_limit=45.0, price_pennies=4500, market_id='stock')
        o2 = OrderDTO(agent_id=2, side='BUY', item_id=f'stock_{firm_id}', quantity=1.0, price_limit=55.0, price_pennies=5500, market_id='stock')
        o3 = OrderDTO(agent_id=3, side='BUY', item_id=f'stock_{firm_id}', quantity=1.0, price_limit=50.0, price_pennies=5000, market_id='stock')
        stock_market.place_order(o1, 1)
        stock_market.place_order(o2, 1)
        stock_market.place_order(o3, 1)
        assert stock_market.get_best_bid(firm_id) == 55.0

class TestStockOrderMatching:

    def test_full_match(self, stock_market, sample_buy_order_dto, sample_sell_order_dto):
        stock_market.reference_prices[100] = 50.0
        stock_market.place_order(sample_buy_order_dto, tick=1)
        stock_market.place_order(sample_sell_order_dto, tick=1)
        transactions = stock_market.match_orders(tick=1)
        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.buyer_id == 1
        assert tx.seller_id == 2
        assert tx.quantity == 10.0
        assert tx.price == pytest.approx(47.5)
        summary = stock_market.get_market_summary(100)
        assert summary['buy_order_count'] == 0
        assert summary['sell_order_count'] == 0

    def test_partial_match(self, stock_market):
        firm_id = 100
        stock_market.reference_prices[firm_id] = 50.0
        buy_order = OrderDTO(agent_id=1, side='BUY', item_id=f'stock_{firm_id}', quantity=15.0, price_limit=50.0, price_pennies=5000, market_id='stock')
        sell_order = OrderDTO(agent_id=2, side='SELL', item_id=f'stock_{firm_id}', quantity=10.0, price_limit=45.0, price_pennies=4500, market_id='stock')
        stock_market.place_order(buy_order, tick=1)
        stock_market.place_order(sell_order, tick=1)
        transactions = stock_market.match_orders(tick=1)
        assert len(transactions) == 1
        assert transactions[0].quantity == 10.0
        sell_order_2 = OrderDTO(agent_id=3, side='SELL', item_id=f'stock_{firm_id}', quantity=5.0, price_limit=45.0, price_pennies=4500, market_id='stock')
        stock_market.place_order(sell_order_2, tick=2)
        transactions_2 = stock_market.match_orders(tick=2)
        assert len(transactions_2) == 1
        assert transactions_2[0].quantity == 5.0
        assert transactions_2[0].buyer_id == 1

class TestOrderExpiry:

    def test_clear_expired_orders(self, stock_market, mock_config):
        mock_config.STOCK_ORDER_EXPIRY_TICKS = 3
        firm_id = 100
        stock_market.reference_prices[firm_id] = 50.0
        o1 = OrderDTO(agent_id=1, side='BUY', item_id=f'stock_{firm_id}', quantity=5.0, price_limit=50.0, price_pennies=5000, market_id='stock')
        stock_market.place_order(o1, tick=1)
        removed = stock_market.clear_expired_orders(current_tick=5)
        assert removed == 1
        summary = stock_market.get_market_summary(firm_id)
        assert summary['buy_order_count'] == 0