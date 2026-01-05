"""
주식 시장 (StockMarket) 단위 테스트
"""

import pytest
from unittest.mock import Mock, MagicMock
from simulation.markets.stock_market import StockMarket
from simulation.models import StockOrder, Transaction


@pytest.fixture
def mock_config():
    config = Mock()
    config.STOCK_MARKET_ENABLED = True
    config.STOCK_PRICE_LIMIT_RATE = 0.10
    config.STOCK_BOOK_VALUE_MULTIPLIER = 1.0
    config.STOCK_MIN_ORDER_QUANTITY = 1.0
    config.STOCK_ORDER_EXPIRY_TICKS = 5
    config.STOCK_TRANSACTION_FEE_RATE = 0.001
    return config


@pytest.fixture
def stock_market(mock_config):
    return StockMarket(config_module=mock_config)


@pytest.fixture
def sample_buy_order():
    return StockOrder(
        agent_id=1,
        order_type="BUY",
        firm_id=100,
        quantity=10.0,
        price=50.0,
    )


@pytest.fixture
def sample_sell_order():
    return StockOrder(
        agent_id=2,
        order_type="SELL",
        firm_id=100,
        quantity=10.0,
        price=45.0,
    )


class TestStockMarketInitialization:
    def test_initialization(self, stock_market):
        assert stock_market.id == "stock_market"
        assert stock_market.buy_orders == {}
        assert stock_market.sell_orders == {}
        assert stock_market.last_prices == {}

    def test_update_reference_prices(self, stock_market):
        mock_firm = Mock()
        mock_firm.id = 100
        mock_firm.is_active = True
        
        # Since logic is delegated to firm.get_book_value_per_share, we just mock that return value
        mock_firm.get_book_value_per_share.return_value = 80.0

        firms = {100: mock_firm}
        stock_market.update_reference_prices(firms)
        
        assert 100 in stock_market.reference_prices
        assert stock_market.reference_prices[100] == 80.0


class TestStockOrderPlacement:
    def test_place_buy_order(self, stock_market, sample_buy_order):
        # 기준가 설정 (가격 제한 체크를 위해)
        stock_market.reference_prices[100] = 50.0
        
        stock_market.place_order(sample_buy_order, tick=1)
        
        assert 100 in stock_market.buy_orders
        assert len(stock_market.buy_orders[100]) == 1
        assert stock_market.buy_orders[100][0].price == 50.0

    def test_place_sell_order(self, stock_market, sample_sell_order):
        stock_market.reference_prices[100] = 50.0
        
        stock_market.place_order(sample_sell_order, tick=1)
        
        assert 100 in stock_market.sell_orders
        assert len(stock_market.sell_orders[100]) == 1
        assert stock_market.sell_orders[100][0].price == 45.0

    def test_buy_orders_sorted_by_price_descending(self, stock_market):
        stock_market.reference_prices[100] = 50.0
        
        order1 = StockOrder(agent_id=1, order_type="BUY", firm_id=100, quantity=5.0, price=45.0)
        order2 = StockOrder(agent_id=2, order_type="BUY", firm_id=100, quantity=5.0, price=55.0)
        order3 = StockOrder(agent_id=3, order_type="BUY", firm_id=100, quantity=5.0, price=50.0)
        
        stock_market.place_order(order1, tick=1)
        stock_market.place_order(order2, tick=1)
        stock_market.place_order(order3, tick=1)
        
        # 높은 가격순으로 정렬되어야 함
        assert stock_market.buy_orders[100][0].price == 55.0
        assert stock_market.buy_orders[100][1].price == 50.0
        assert stock_market.buy_orders[100][2].price == 45.0

    def test_sell_orders_sorted_by_price_ascending(self, stock_market):
        stock_market.reference_prices[100] = 50.0
        
        order1 = StockOrder(agent_id=1, order_type="SELL", firm_id=100, quantity=5.0, price=55.0)
        order2 = StockOrder(agent_id=2, order_type="SELL", firm_id=100, quantity=5.0, price=45.0)
        order3 = StockOrder(agent_id=3, order_type="SELL", firm_id=100, quantity=5.0, price=50.0)
        
        stock_market.place_order(order1, tick=1)
        stock_market.place_order(order2, tick=1)
        stock_market.place_order(order3, tick=1)
        
        # 낮은 가격순으로 정렬되어야 함
        assert stock_market.sell_orders[100][0].price == 45.0
        assert stock_market.sell_orders[100][1].price == 50.0
        assert stock_market.sell_orders[100][2].price == 55.0


class TestStockOrderMatching:
    def test_full_match(self, stock_market, sample_buy_order, sample_sell_order):
        stock_market.reference_prices[100] = 50.0
        
        stock_market.place_order(sample_buy_order, tick=1)
        stock_market.place_order(sample_sell_order, tick=1)
        
        transactions = stock_market.match_orders(tick=1)
        
        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.buyer_id == 1
        assert tx.seller_id == 2
        assert tx.quantity == 10.0
        assert tx.price == pytest.approx(47.5)  # (50 + 45) / 2
        assert tx.transaction_type == "stock"
        assert tx.item_id == "stock_100"

    def test_partial_match_buy_order_larger(self, stock_market):
        stock_market.reference_prices[100] = 50.0
        
        buy_order = StockOrder(agent_id=1, order_type="BUY", firm_id=100, quantity=15.0, price=50.0)
        sell_order = StockOrder(agent_id=2, order_type="SELL", firm_id=100, quantity=10.0, price=45.0)
        
        stock_market.place_order(buy_order, tick=1)
        stock_market.place_order(sell_order, tick=1)
        
        transactions = stock_market.match_orders(tick=1)
        
        assert len(transactions) == 1
        assert transactions[0].quantity == 10.0
        
        # 매수 주문 잔량 확인
        assert len(stock_market.buy_orders[100]) == 1
        assert stock_market.buy_orders[100][0].quantity == 5.0
        
        # 매도 주문은 완료되어 제거됨
        assert len(stock_market.sell_orders[100]) == 0

    def test_no_match_price_gap(self, stock_market):
        stock_market.reference_prices[100] = 50.0
        
        buy_order = StockOrder(agent_id=1, order_type="BUY", firm_id=100, quantity=10.0, price=40.0)
        sell_order = StockOrder(agent_id=2, order_type="SELL", firm_id=100, quantity=10.0, price=55.0)
        
        stock_market.place_order(buy_order, tick=1)
        stock_market.place_order(sell_order, tick=1)
        
        transactions = stock_market.match_orders(tick=1)
        
        assert len(transactions) == 0
        assert len(stock_market.buy_orders[100]) == 1
        assert len(stock_market.sell_orders[100]) == 1


class TestStockPriceQueries:
    def test_get_stock_price_with_last_price(self, stock_market):
        stock_market.last_prices[100] = 52.0
        stock_market.reference_prices[100] = 50.0
        
        price = stock_market.get_stock_price(100)
        assert price == 52.0  # 최근 거래가 우선

    def test_get_stock_price_fallback_to_reference(self, stock_market):
        stock_market.reference_prices[100] = 50.0
        
        price = stock_market.get_stock_price(100)
        assert price == 50.0

    def test_get_best_bid(self, stock_market):
        stock_market.reference_prices[100] = 50.0
        
        order1 = StockOrder(agent_id=1, order_type="BUY", firm_id=100, quantity=5.0, price=48.0)
        order2 = StockOrder(agent_id=2, order_type="BUY", firm_id=100, quantity=5.0, price=52.0)
        
        stock_market.place_order(order1, tick=1)
        stock_market.place_order(order2, tick=1)
        
        assert stock_market.get_best_bid(100) == 52.0

    def test_get_best_ask(self, stock_market):
        stock_market.reference_prices[100] = 50.0
        
        order1 = StockOrder(agent_id=1, order_type="SELL", firm_id=100, quantity=5.0, price=48.0)
        order2 = StockOrder(agent_id=2, order_type="SELL", firm_id=100, quantity=5.0, price=52.0)
        
        stock_market.place_order(order1, tick=1)
        stock_market.place_order(order2, tick=1)
        
        assert stock_market.get_best_ask(100) == 48.0


class TestOrderExpiry:
    def test_clear_expired_orders(self, stock_market, mock_config):
        mock_config.STOCK_ORDER_EXPIRY_TICKS = 3
        stock_market.reference_prices[100] = 50.0
        
        # 틱 1에 주문 생성
        order1 = StockOrder(agent_id=1, order_type="BUY", firm_id=100, quantity=5.0, price=50.0)
        stock_market.place_order(order1, tick=1)
        
        # 틱 2에 주문 생성
        order2 = StockOrder(agent_id=2, order_type="BUY", firm_id=100, quantity=5.0, price=49.0)
        stock_market.place_order(order2, tick=2)
        
        # 틱 5에서 만료 체크 (expiry = 3틱)
        # order1은 틱 1에 생성 -> 5 - 1 = 4 >= 3 -> 만료
        # order2는 틱 2에 생성 -> 5 - 2 = 3 >= 3 -> 만료
        removed = stock_market.clear_expired_orders(current_tick=5)
        
        assert removed == 2
        assert len(stock_market.buy_orders[100]) == 0


class TestMarketSummary:
    def test_get_market_summary(self, stock_market):
        stock_market.reference_prices[100] = 50.0
        stock_market.last_prices[100] = 52.0
        stock_market.daily_volumes[100] = 100.0
        stock_market.daily_high[100] = 55.0
        stock_market.daily_low[100] = 48.0
        
        summary = stock_market.get_market_summary(100)
        
        assert summary["firm_id"] == 100
        assert summary["last_price"] == 52.0
        assert summary["reference_price"] == 50.0
        assert summary["daily_volume"] == 100.0
        assert summary["daily_high"] == 55.0
        assert summary["daily_low"] == 48.0
