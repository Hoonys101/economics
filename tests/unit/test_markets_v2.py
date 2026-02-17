import pytest
from simulation.markets.order_book_market import OrderBookMarket
from simulation.models import Order
from modules.common.utils.logger import Logger
from modules.system.api import DEFAULT_CURRENCY


@pytest.fixture
def market():
    """테스트를 위한 OrderBookMarket 객체를 생성합니다."""
    return OrderBookMarket(
        market_id="test_goods_market", logger=Logger()
    )  # 테스트 중에는 기본 로거 사용


class TestOrderBookMarketInitialization:
    def test_market_initialization(self, market: OrderBookMarket):
        """시장이 올바르게 초기화되는지 테스트합니다."""
        assert market.id == "test_goods_market"
        assert isinstance(market.logger, Logger)
        assert not market.buy_orders
        assert not market.sell_orders


# --- Phase 1: 시장 기반 구축 테스트 ---


class TestPlaceOrderToBook:
    def test_add_single_buy_order(self, market: OrderBookMarket):
        """단일 매수 주문이 오더북에 올바르게 추가되는지 테스트합니다."""
        # Order(..., pennies, limit, ...)
        # 100 pennies = $1.00
        order = Order(
            1, "BUY", "food", 10, 100, 1.00, "test_market"
        )
        market.place_order(order, 1)

        buy_book = market.buy_orders.get("food", [])
        sell_book = market.sell_orders.get("food", [])
        assert len(buy_book) == 1
        assert len(sell_book) == 0
        assert buy_book[0].price_pennies == 100

    def test_add_buy_orders_sorted(self, market: OrderBookMarket):
        """여러 매수 주문이 가격 내림차순으로 정렬되는지 테스트합니다."""
        # 100 pennies ($1.00), 110 ($1.10), 105 ($1.05)
        order1 = Order(1, "BUY", "food", 10, 100, 1.00, "test_market")
        order2 = Order(2, "BUY", "food", 5, 110, 1.10, "test_market")
        order3 = Order(3, "BUY", "food", 8, 105, 1.05, "test_market")

        market.place_order(order1, 1)
        market.place_order(order2, 2)
        market.place_order(order3, 3)

        buy_book = market.buy_orders.get("food", [])
        assert len(buy_book) == 3
        # Check SSoT (Pennies)
        assert [o.price_pennies for o in buy_book] == [110, 105, 100]

    def test_add_sell_orders_sorted(self, market: OrderBookMarket):
        """여러 매도 주문이 가격 오름차순으로 정렬되는지 테스트합니다."""
        order1 = Order(1, "SELL", "food", 10, 100, 1.00, "test_market")
        order2 = Order(2, "SELL", "food", 5, 90, 0.90, "test_market")
        order3 = Order(3, "SELL", "food", 8, 95, 0.95, "test_market")

        market.place_order(order1, 1)
        market.place_order(order2, 2)
        market.place_order(order3, 3)

        sell_book = market.sell_orders.get("food", [])
        assert len(sell_book) == 3
        assert [o.price_pennies for o in sell_book] == [90, 95, 100]

    def test_add_orders_with_same_price(self, market: OrderBookMarket):
        """가격이 같은 주문은 시간 순서(FIFO)대로 정렬되는지 테스트합니다."""
        order1 = Order(1, "BUY", "food", 10, 100, 1.00, "test_market")
        order2 = Order(2, "BUY", "food", 5, 110, 1.10, "test_market")
        order3 = Order(3, "BUY", "food", 8, 100, 1.00, "test_market")

        market.place_order(order1, 1)
        market.place_order(order2, 2)
        market.place_order(order3, 3)

        buy_book = market.buy_orders.get("food", [])
        assert len(buy_book) == 3
        assert [o.price_pennies for o in buy_book] == [110, 100, 100]
        # 가격이 100인 주문들 중 먼저 들어온 order1(agent_id=1)이 앞에 위치해야 함
        assert [o.agent_id for o in buy_book if o.price_pennies == 100] == [1, 3]


class TestOrderMatching:
    def test_unfilled_order_no_match(self, market: OrderBookMarket):
        """가격이 교차하지 않아 매칭이 발생하지 않는 경우를 테스트합니다."""
        # Sell @ 110 ($1.10), Buy @ 100 ($1.00) -> No match
        sell_order = Order(1, "SELL", "food", 10, 110, 1.10, "test_market")
        market.place_order(sell_order, current_time=1)

        buy_order = Order(2, "BUY", "food", 10, 100, 1.00, "test_market")
        market.place_order(buy_order, current_time=2)

        # Act
        transactions = market.match_orders(current_time=3)

        # Assert
        assert len(transactions) == 0

        buy_book = market.buy_orders.get("food", [])
        sell_book = market.sell_orders.get("food", [])

        assert len(buy_book) == 1
        assert len(sell_book) == 1
        assert buy_book[0].price_pennies == 100
        assert sell_book[0].price_pennies == 110

    def test_full_match_one_to_one(self, market: OrderBookMarket):
        """매수 주문 1개와 매도 주문 1개가 완전히 체결되는 경우를 테스트합니다."""
        # Sell @ 100 ($1.00)
        sell_order = Order(2, "SELL", "food", 10, 100, 1.00, "test_market")
        market.place_order(sell_order, current_time=1)

        # Buy @ 105 ($1.05)
        buy_order = Order(1, "BUY", "food", 10, 105, 1.05, "test_market")
        market.place_order(buy_order, current_time=2)

        transactions = market.match_orders(current_time=2)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.quantity == 10
        # Integer Math: (105 + 100) // 2 = 102 pennies
        # Price (Float) = 1.02
        assert tx.price == 1.02
        assert tx.total_pennies == 1020
        assert tx.buyer_id == 1
        assert tx.seller_id == 2
        assert tx.currency == DEFAULT_CURRENCY

        assert not market.buy_orders.get("food", [])
        assert not market.sell_orders.get("food", [])

    def test_partial_match_then_book(self, market: OrderBookMarket):
        """새로운 매수 주문이 부분 체결된 후 나머지가 오더북에 등록되는 경우를 테스트합니다."""
        # Sell 5 @ 100 ($1.00)
        sell_order = Order(2, "SELL", "food", 5, 100, 1.00, "test_market")
        market.place_order(sell_order, current_time=1)

        # Buy 10 @ 105 ($1.05)
        buy_order = Order(1, "BUY", "food", 10, 105, 1.05, "test_market")
        market.place_order(buy_order, current_time=2)

        transactions = market.match_orders(current_time=2)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.quantity == 5
        assert tx.price == 1.02 # 102 pennies

        buy_book = market.buy_orders.get("food", [])
        sell_book = market.sell_orders.get("food", [])
        assert not sell_book
        assert len(buy_book) == 1
        assert buy_book[0].agent_id == 1
        assert buy_book[0].quantity == 5

    def test_match_with_multiple_orders(self, market: OrderBookMarket):
        """새로운 큰 주문 하나가 여러 개의 작은 주문과 체결되는 경우를 테스트합니다."""
        # Sell 5 @ 98 ($0.98)
        sell1 = Order(2, "SELL", "food", 5, 98, 0.98, "test_market")
        # Sell 5 @ 100 ($1.00)
        sell2 = Order(3, "SELL", "food", 5, 100, 1.00, "test_market")
        market.place_order(sell1, current_time=1)
        market.place_order(sell2, current_time=2)

        # Buy 12 @ 105 ($1.05)
        buy_order = Order(1, "BUY", "food", 12, 105, 1.05, "test_market")
        market.place_order(buy_order, current_time=3)

        transactions = market.match_orders(current_time=3)

        assert len(transactions) == 2
        assert transactions[0].quantity == 5
        # (105 + 98) // 2 = 101 pennies -> 1.01
        assert transactions[0].price == 1.01
        assert transactions[1].quantity == 5
        # (105 + 100) // 2 = 102 pennies -> 1.02
        assert transactions[1].price == 1.02

        buy_book = market.buy_orders.get("food", [])
        assert len(buy_book) == 1
        assert buy_book[0].quantity == 2


# --- Phase 2: API 구현 테스트 ---


class TestMarketAPI:
    def test_get_best_bid_empty(self, market: OrderBookMarket):
        assert market.get_best_bid("food") is None

    def test_get_best_bid_non_empty(self, market: OrderBookMarket):
        # 100 pennies ($1.00), 110 pennies ($1.10)
        market.place_order(Order(1, "BUY", "food", 10, 100, 1.00, "test"), 1)
        market.place_order(Order(2, "BUY", "food", 5, 110, 1.10, "test"), 2)
        assert market.get_best_bid("food") == 1.10 # Returns Dollars (Float)

    def test_get_best_ask_empty(self, market: OrderBookMarket):
        assert market.get_best_ask("food") is None

    def test_get_best_ask_non_empty(self, market: OrderBookMarket):
        # 100 pennies, 90 pennies
        market.place_order(Order(1, "SELL", "food", 10, 100, 1.00, "test"), 1)
        market.place_order(Order(2, "SELL", "food", 5, 90, 0.90, "test"), 2)
        assert market.get_best_ask("food") == 0.90 # Returns Dollars (Float)

    def test_get_last_traded_price(self, market: OrderBookMarket):
        market.place_order(Order(1, 'SELL', 'food', 10, 100, 1.00, 'test'), 1)
        market.place_order(Order(2, 'BUY', 'food', 10, 105, 1.05, 'test'), 2)
        market.match_orders(2)
        # 102 pennies -> 1.02 Dollars
        assert market.get_last_traded_price('food') == 1.02

    def test_get_spread(self, market: OrderBookMarket):
        market.place_order(Order(1, 'BUY', 'food', 10, 100, 1.00, 'test'), 1)
        market.place_order(Order(2, 'SELL', 'food', 10, 105, 1.05, 'test'), 2)
        # 1.05 - 1.00 = 0.05
        assert market.get_spread('food') == pytest.approx(0.05)

    def test_get_spread_no_bid_or_ask(self, market: OrderBookMarket):
        market.place_order(Order(1, 'BUY', 'food', 10, 100, 1.00, 'test'), 1)
        assert market.get_spread('food') is None
        market = OrderBookMarket(market_id="test_goods_market", logger=Logger())
        market.place_order(Order(2, 'SELL', 'food', 10, 105, 1.05, 'test'), 2)
        assert market.get_spread('food') is None

    def test_get_market_depth(self, market: OrderBookMarket):
        market.place_order(Order(1, 'BUY', 'food', 10, 100, 1.00, 'test'), 1)
        market.place_order(Order(2, 'BUY', 'food', 5, 90, 0.90, 'test'), 2)
        market.place_order(Order(3, 'SELL', 'food', 10, 105, 1.05, 'test'), 3)
        assert market.get_market_depth('food') == {'buy_orders': 2, 'sell_orders': 1}
