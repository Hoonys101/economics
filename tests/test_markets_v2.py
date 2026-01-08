import pytest
from simulation.markets.order_book_market import OrderBookMarket
from simulation.models import Order
from utils.logger import Logger


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
        order = Order(
            agent_id=1,
            order_type="BUY",
            item_id="food",
            quantity=10,
            price=100,
            market_id="test_market",
        )
        market.place_order(order, 1)

        buy_book = market.buy_orders.get("food", [])
        sell_book = market.sell_orders.get("food", [])
        assert len(buy_book) == 1
        assert len(sell_book) == 0
        assert buy_book[0].price == 100

    def test_add_buy_orders_sorted(self, market: OrderBookMarket):
        """여러 매수 주문이 가격 내림차순으로 정렬되는지 테스트합니다."""
        order1 = Order(
            agent_id=1,
            order_type="BUY",
            item_id="food",
            quantity=10,
            price=100,
            market_id="test_market",
        )
        order2 = Order(
            agent_id=2,
            order_type="BUY",
            item_id="food",
            quantity=5,
            price=110,
            market_id="test_market",
        )
        order3 = Order(
            agent_id=3,
            order_type="BUY",
            item_id="food",
            quantity=8,
            price=105,
            market_id="test_market",
        )

        market.place_order(order1, 1)
        market.place_order(order2, 2)
        market.place_order(order3, 3)

        buy_book = market.buy_orders.get("food", [])
        assert len(buy_book) == 3
        assert [o.price for o in buy_book] == [110, 105, 100]

    def test_add_sell_orders_sorted(self, market: OrderBookMarket):
        """여러 매도 주문이 가격 오름차순으로 정렬되는지 테스트합니다."""
        order1 = Order(
            agent_id=1,
            order_type="SELL",
            item_id="food",
            quantity=10,
            price=100,
            market_id="test_market",
        )
        order2 = Order(
            agent_id=2,
            order_type="SELL",
            item_id="food",
            quantity=5,
            price=90,
            market_id="test_market",
        )
        order3 = Order(
            agent_id=3,
            order_type="SELL",
            item_id="food",
            quantity=8,
            price=95,
            market_id="test_market",
        )

        market.place_order(order1, 1)
        market.place_order(order2, 2)
        market.place_order(order3, 3)

        sell_book = market.sell_orders.get("food", [])
        assert len(sell_book) == 3
        assert [o.price for o in sell_book] == [90, 95, 100]

    def test_add_orders_with_same_price(self, market: OrderBookMarket):
        """가격이 같은 주문은 시간 순서(FIFO)대로 정렬되는지 테스트합니다."""
        # 이 테스트는 현재 bisect 구현 상 통과함 (stable sort와 유사하게 동작)
        order1 = Order(
            agent_id=1,
            order_type="BUY",
            item_id="food",
            quantity=10,
            price=100,
            market_id="test_market",
        )
        order2 = Order(
            agent_id=2,
            order_type="BUY",
            item_id="food",
            quantity=5,
            price=110,
            market_id="test_market",
        )
        order3 = Order(
            agent_id=3,
            order_type="BUY",
            item_id="food",
            quantity=8,
            price=100,
            market_id="test_market",
        )  # order1과 가격 동일

        market.place_order(order1, 1)
        market.place_order(order2, 2)
        market.place_order(order3, 3)

        buy_book = market.buy_orders.get("food", [])
        assert len(buy_book) == 3
        assert [o.price for o in buy_book] == [110, 100, 100]
        # 가격이 100인 주문들 중 먼저 들어온 order1(agent_id=1)이 앞에 위치해야 함
        assert [o.agent_id for o in buy_book if o.price == 100] == [1, 3]


class TestOrderFillStatus:
    def test_order_remains_unfilled(self, market: OrderBookMarket):
        """매칭되지 않은 주문이 오더북에 그대로 남고 수량이 유지되는지 테스트합니다."""
        # 1. Place Order
        order = Order(
            agent_id=1,
            order_type="BUY",
            item_id="food",
            quantity=10,
            price=100,
            market_id="test_market",
        )
        market.place_order(order, current_time=1)

        # 2. Match (no opposing orders)
        market.match_orders(current_time=1)

        # 3. Verify
        buy_book = market.buy_orders.get("food", [])
        assert len(buy_book) == 1
        assert buy_book[0].quantity == 10  # 수량 변동 없음
        assert buy_book[0].agent_id == 1

    def test_order_fully_filled(self, market: OrderBookMarket):
        """완전히 체결된 주문이 오더북에서 제거되고 수량이 0이 되는지 테스트합니다."""
        # 1. Place Buy Order
        buy_order = Order(
            agent_id=1,
            order_type="BUY",
            item_id="food",
            quantity=10,
            price=100,
            market_id="test_market",
        )
        market.place_order(buy_order, current_time=1)

        # 2. Place Sell Order (Matching)
        sell_order = Order(
            agent_id=2,
            order_type="SELL",
            item_id="food",
            quantity=10,
            price=100,
            market_id="test_market",
        )
        market.place_order(sell_order, current_time=1)

        # 3. Match
        market.match_orders(current_time=1)

        # 4. Verify
        buy_book = market.buy_orders.get("food", [])
        sell_book = market.sell_orders.get("food", [])

        # 오더북에서 제거되었는지 확인
        assert len(buy_book) == 0
        assert len(sell_book) == 0

        # 주문 객체의 수량이 0으로 업데이트되었는지 확인
        # (match_orders는 객체를 직접 수정함)
        assert buy_order.quantity == 0
        assert sell_order.quantity == 0

    def test_order_partially_filled(self, market: OrderBookMarket):
        """부분 체결된 주문이 오더북에 남고 수량이 차감되는지 테스트합니다."""
        # 1. Place Buy Order (Large)
        buy_order = Order(
            agent_id=1,
            order_type="BUY",
            item_id="food",
            quantity=10,
            price=100,
            market_id="test_market",
        )
        market.place_order(buy_order, current_time=1)

        # 2. Place Sell Order (Small)
        sell_order = Order(
            agent_id=2,
            order_type="SELL",
            item_id="food",
            quantity=4,
            price=100,
            market_id="test_market",
        )
        market.place_order(sell_order, current_time=1)

        # 3. Match
        market.match_orders(current_time=1)

        # 4. Verify
        buy_book = market.buy_orders.get("food", [])
        sell_book = market.sell_orders.get("food", [])

        # 매수 주문은 남아야 함
        assert len(buy_book) == 1
        # 매도 주문은 사라져야 함
        assert len(sell_book) == 0

        # 남은 주문의 수량 확인 (10 - 4 = 6)
        assert buy_book[0].quantity == 6
        assert buy_order.quantity == 6

        # 매도 주문은 완전 체결됨
        assert sell_order.quantity == 0


class TestOrderMatching:
    def test_unfilled_order_no_match(self, market: OrderBookMarket):
        """가격이 교차하지 않아 매칭이 발생하지 않는 경우를 테스트합니다."""
        # Arrange: 매도 110, 매수 100 (가격 불일치)
        sell_order = Order(
            agent_id=1,
            order_type="SELL",
            item_id="food",
            quantity=10,
            price=110,
            market_id="test_market",
        )
        market.place_order(sell_order, current_time=1)

        buy_order = Order(
            agent_id=2,
            order_type="BUY",
            item_id="food",
            quantity=10,
            price=100,
            market_id="test_market",
        )
        market.place_order(buy_order, current_time=2)

        # Act
        transactions = market.match_orders(current_time=3)

        # Assert: 거래 없음, 주문 잔존
        assert len(transactions) == 0

        buy_book = market.buy_orders.get("food", [])
        sell_book = market.sell_orders.get("food", [])

        assert len(buy_book) == 1
        assert len(sell_book) == 1
        assert buy_book[0].price == 100
        assert sell_book[0].price == 110

    def test_full_match_one_to_one(self, market: OrderBookMarket):
        """매수 주문 1개와 매도 주문 1개가 완전히 체결되는 경우를 테스트합니다."""
        sell_order = Order(
            agent_id=2,
            order_type="SELL",
            item_id="food",
            quantity=10,
            price=100,
            market_id="test_market",
        )
        market.place_order(sell_order, current_time=1)

        buy_order = Order(
            agent_id=1,
            order_type="BUY",
            item_id="food",
            quantity=10,
            price=105,
            market_id="test_market",
        )
        market.place_order(buy_order, current_time=2)

        transactions = market.match_orders(current_time=2)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.quantity == 10
        assert tx.price == 102.5  # FIX: 매치가격은 중간값으로 설정
        assert tx.buyer_id == 1
        assert tx.seller_id == 2

        # 오더북이 비어있는지 확인
        assert not market.buy_orders.get("food", [])
        assert not market.sell_orders.get("food", [])

    def test_partial_match_then_book(self, market: OrderBookMarket):
        """새로운 매수 주문이 부분 체결된 후 나머지가 오더북에 등록되는 경우를 테스트합니다."""
        sell_order = Order(
            agent_id=2,
            order_type="SELL",
            item_id="food",
            quantity=5,
            price=100,
            market_id="test_market",
        )
        market.place_order(sell_order, current_time=1)

        buy_order = Order(
            agent_id=1,
            order_type="BUY",
            item_id="food",
            quantity=10,
            price=105,
            market_id="test_market",
        )
        market.place_order(buy_order, current_time=2)

        transactions = market.match_orders(current_time=2)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.quantity == 5  # 매도 주문의 수량만큼만 체결

        # 매도 오더북은 비워지고, 매수 오더북에 남은 주문이 등록되어야 함
        buy_book = market.buy_orders.get("food", [])
        sell_book = market.sell_orders.get("food", [])
        assert not sell_book
        assert len(buy_book) == 1
        assert buy_book[0].agent_id == 1
        assert buy_book[0].quantity == 5  # 10 - 5 = 5

    def test_match_with_multiple_orders(self, market: OrderBookMarket):
        """새로운 큰 주문 하나가 여러 개의 작은 주문과 체결되는 경우를 테스트합니다."""
        sell1 = Order(
            agent_id=2,
            order_type="SELL",
            item_id="food",
            quantity=5,
            price=98,
            market_id="test_market",
        )
        sell2 = Order(
            agent_id=3,
            order_type="SELL",
            item_id="food",
            quantity=5,
            price=100,
            market_id="test_market",
        )
        market.place_order(sell1, current_time=1)
        market.place_order(sell2, current_time=2)

        buy_order = Order(
            agent_id=1,
            order_type="BUY",
            item_id="food",
            quantity=12,
            price=105,
            market_id="test_market",
        )
        market.place_order(buy_order, current_time=3)

        transactions = market.match_orders(current_time=3)

        assert len(transactions) == 2
        assert transactions[0].quantity == 5
        assert transactions[0].price == 101.5  # FIX: (105+98)/2
        assert transactions[1].quantity == 5
        assert transactions[1].price == 102.5  # FIX: (105+100)/2

        # 매도 오더북은 비워지고, 매수 오더북에 남은 주문이 등록되어야 함
        buy_book = market.buy_orders.get("food", [])
        sell_book = market.sell_orders.get("food", [])
        assert not sell_book
        assert len(buy_book) == 1
        assert buy_book[0].quantity == 2  # 12 - 5 - 5 = 2


# --- Phase 2: API 구현 테스트 ---


class TestMarketAPI:
    def test_get_best_bid_empty(self, market: OrderBookMarket):
        """매수 오더북이 비어있을 때 get_best_bid가 None을 반환하는지 테스트합니다."""
        assert market.get_best_bid("food") is None

    def test_get_best_bid_non_empty(self, market: OrderBookMarket):
        """매수 오더북에 주문이 있을 때 get_best_bid가 최고가를 반환하는지 테스트합니다."""
        market.place_order(Order(1, "BUY", "food", 10, 100, "test"), 1)
        market.place_order(Order(2, "BUY", "food", 5, 110, "test"), 2)
        assert market.get_best_bid("food") == 110

    def test_get_best_ask_empty(self, market: OrderBookMarket):
        """매도 오더북이 비어있을 때 get_best_ask가 None을 반환하는지 테스트합니다."""
        assert market.get_best_ask("food") is None

    def test_get_best_ask_non_empty(self, market: OrderBookMarket):
        """매도 오더북에 주문이 있을 때 get_best_ask가 최저가를 반환하는지 테스트합니다."""
        market.place_order(Order(1, "SELL", "food", 10, 100, "test"), 1)
        market.place_order(Order(2, "SELL", "food", 5, 90, "test"), 2)
        assert market.get_best_ask("food") == 90

    def test_get_last_traded_price(self, market: OrderBookMarket):
        """거래 발생 후 get_last_traded_price가 올바른 가격을 반환하는지 테스트합니다."""
        market.place_order(Order(1, 'SELL', 'food', 10, 100, 'test'), 1)
        market.place_order(Order(2, 'BUY', 'food', 10, 105, 'test'), 2)
        market.match_orders(2)
        assert market.get_last_traded_price('food') == 102.5

    def test_get_spread(self, market: OrderBookMarket):
        """스프레드 계산이 올바른지 테스트합니다."""
        market.place_order(Order(1, 'BUY', 'food', 10, 100, 'test'), 1)
        market.place_order(Order(2, 'SELL', 'food', 10, 105, 'test'), 2)
        assert market.get_spread('food') == 5

    def test_get_spread_no_bid_or_ask(self, market: OrderBookMarket):
        """매수/매도 호가가 없을 때 get_spread가 None을 반환하는지 테스트합니다."""
        market.place_order(Order(1, 'BUY', 'food', 10, 100, 'test'), 1)
        assert market.get_spread('food') is None
        market = OrderBookMarket(market_id="test_goods_market", logger=Logger()) # Reset market
        market.place_order(Order(2, 'SELL', 'food', 10, 105, 'test'), 2)
        assert market.get_spread('food') is None

    def test_get_market_depth(self, market: OrderBookMarket):
        """시장 깊이(주문 수) 계산이 올바른지 테스트합니다."""
        market.place_order(Order(1, 'BUY', 'food', 10, 100, 'test'), 1)
        market.place_order(Order(2, 'BUY', 'food', 5, 90, 'test'), 2)
        market.place_order(Order(3, 'SELL', 'food', 10, 105, 'test'), 3)
        assert market.get_market_depth('food') == {'buy_orders': 2, 'sell_orders': 1}
