"""
주식 시장 (StockMarket) 단위 테스트
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from simulation.markets.stock_market import StockMarket
from simulation.models import StockOrder, Transaction


@pytest.fixture
def mock_config(golden_config):
    # Use golden_config if available, otherwise fallback to a fresh Mock
    config = golden_config if golden_config is not None else Mock()

    # State Override Pattern: Set specific test preconditions
    config.STOCK_MARKET_ENABLED = True
    config.STOCK_PRICE_LIMIT_RATE = 0.15
    config.STOCK_BOOK_VALUE_MULTIPLIER = 1.0
    config.STOCK_MIN_ORDER_QUANTITY = 1.0
    config.STOCK_ORDER_EXPIRY_TICKS = 5
    config.STOCK_TRANSACTION_FEE_RATE = 0.001
    config.IPO_INITIAL_SHARES = 1000.0
    config.STARTUP_COST = 30000.0
    config.VALUE_ORIENTATION_MAPPING = {
        "v": {
            "preference_asset": 1.0,
            "preference_social": 1.0,
            "preference_growth": 1.0,
        }
    }
    config.TICKS_PER_YEAR = 100
    config.SEO_TRIGGER_RATIO = 0.5
    config.EDUCATION_WEALTH_THRESHOLDS = {}
    config.SEO_MAX_SELL_RATIO = 0.1
    config.EDUCATION_LEVEL_DISTRIBUTION = [1.0]
    config.INITIAL_WAGE = 10.0
    config.EDUCATION_COST_MULTIPLIERS = {}
    config.QUALITY_PREF_SNOB_MIN = 0.7
    config.QUALITY_PREF_MISER_MAX = 0.3
    config.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 500.0
    config.STOCK_INVESTMENT_DIVERSIFICATION_COUNT = 3
    config.STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD = 10.0
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

    def test_update_reference_prices(self, stock_market, golden_firms):
        mock_firm = golden_firms[0]
        mock_firm.id = 100
        mock_firm.is_active = True
        
        # Since logic is delegated to firm.get_book_value_per_share, we just mock that return value
        # Ensure it's a mock method
        mock_firm.get_book_value_per_share = Mock(return_value=80.0)

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

def test_ipo_share_count(stock_market, mock_config):
    from simulation.firms import Firm
    from tests.utils.factories import create_firm_config_dto
    mock_config.PROFIT_HISTORY_TICKS = 10
    firm_decision_engine = MagicMock()
    firm = Firm(id=1, initial_capital=10000, initial_liquidity_need=100, specialization="food",
                productivity_factor=1, decision_engine=firm_decision_engine, value_orientation="v",
                config_dto=create_firm_config_dto())

    firm.init_ipo(stock_market)

    assert firm.total_shares == 1000.0
    assert firm.treasury_shares == 1000.0
    assert stock_market.shareholders[firm.id][firm.id] == 1000.0

def test_seo_triggers(stock_market, mock_config, golden_firms):
    from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
    mock_config.PROFIT_HISTORY_TICKS = 10
    firm_decision_engine = AIDrivenFirmDecisionEngine(ai_engine=MagicMock(), config_module=mock_config)

    # Use golden_firms[0] but override state
    firm = golden_firms[0]
    firm.id = 1
    firm.decision_engine = firm_decision_engine
    firm.config_module = mock_config
    firm.specialization = "food"

    # State Override
    firm._assets = mock_config.STARTUP_COST * 0.4  # Below threshold
    firm.treasury_shares = 500
    firm.total_shares = 1000.0

    context = MagicMock()
    context.firm = firm
    context.markets = {"stock_market": stock_market}
    context.current_time = 1

    with patch.object(stock_market, 'get_stock_price', return_value=10.0):
        # SEO logic is in FinanceManager now
        # Use factory for config to ensure lowercase attributes
        from tests.utils.factories import create_firm_config_dto
        config_dto = create_firm_config_dto(
            startup_cost=30000.0,
            seo_trigger_ratio=0.5,
            seo_max_sell_ratio=0.1
        )
        order = firm_decision_engine.corporate_manager.finance_manager._attempt_secondary_offering(firm, context, config_dto)

    assert order is not None
    assert order.agent_id == firm.id
    assert order.firm_id == firm.id
    assert order.order_type == "SELL"
    assert order.quantity == 50.0 # 10% of 500

def test_household_investment(stock_market, mock_config, golden_households):
    from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
    from simulation.ai.api import Personality

    mock_config.PROFIT_HISTORY_TICKS = 10
    mock_config.CONFORMITY_RANGES = {
        "STATUS_SEEKER": (0.7, 0.95),
        "CONSERVATIVE": (0.5, 0.7),
        "MISER": (0.1, 0.3),
        "IMPULSIVE": (0.4, 0.6),
        None: (0.3, 0.7)
    }
    mock_config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 1000.0
    mock_config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 2.0
    mock_config.GOODS = {"basic_food": {"initial_price": 5.0}}

    household_decision_engine = AIDrivenHouseholdDecisionEngine(ai_engine=MagicMock(), config_module=mock_config)

    # Use golden_households[0] but override state
    household = golden_households[0]
    household.id = 1
    household.decision_engine = household_decision_engine
    household.config_module = mock_config
    household.personality = Personality.BALANCED

    # State Override
    household._assets = 1000.0
    household.needs = {}
    household.value_orientation = "v"

    # Ensure talent is present if needed (mock usually has it as a mock, but explicit override is safer if logic depends on it)
    # household.talent is likely a Mock, which is fine unless we access specific attrs like max_potential.
    # The original test set max_potential={"labor": 10}.
    from types import SimpleNamespace
    household.talent = SimpleNamespace(max_potential={"labor": 10})

    stock_market.last_prices = {1: 10.0}

    stock_market.reference_prices = {1: 10.0, 2: 20.0, 3: 30.0, 4: 40.0}

    with patch('simulation.decisions.portfolio_manager.PortfolioManager.optimize_portfolio', return_value=(100, 400, 500)) as mock_optimize:

        # We need a market_data structure for the test
        market_data = {
            "loan_market": {"interest_rate": 0.03},
            "avg_dividend_yield": 0.05,
            "inflation": 0.02,
            "goods_market": {"basic_food_current_sell_price": 5.0}
        }

        # Directly test the order creation logic
        # Logic moved to AssetManager
        orders = household_decision_engine.asset_manager._place_buy_orders(household, 500, stock_market, 1)

        assert len(orders) > 0
        assert isinstance(orders[0], StockOrder)
        assert orders[0].order_type == "BUY"
        assert orders[0].agent_id == household.id

def test_price_limit(stock_market):
    firm_id = 1
    stock_market.reference_prices[firm_id] = 100.0

    # Test upper limit
    order = StockOrder(agent_id=1, firm_id=firm_id, order_type="BUY", quantity=1, price=120.0)
    stock_market.place_order(order, 1)
    assert order.price == pytest.approx(115.0)

    # Test lower limit
    order = StockOrder(agent_id=1, firm_id=firm_id, order_type="BUY", quantity=1, price=80.0)
    stock_market.place_order(order, 1)
    assert order.price == pytest.approx(85.0)
