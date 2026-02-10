import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import cast, Dict
import os
import sys

from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.markets.order_book_market import OrderBookMarket
from simulation.models import Order
from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
import config
from simulation.ai.api import Tactic, Aggressiveness
from simulation.core_markets import Market
from simulation.dtos.api import DecisionInputDTO, MarketSnapshotDTO, HousingMarketSnapshotDTO, LoanMarketSnapshotDTO, LaborMarketSnapshotDTO

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock data for goods
GOODS_DATA = [
    {
        "id": "food",
        "name": "Food",
        "utility_per_need": {"survival_need": 10.0},
        "storability": 0.5,
    },
    {
        "id": "luxury_food",
        "name": "Luxury Food",
        "utility_per_need": {"recognition_need": 5.0},
        "is_luxury": True,
        "storability": 0.1,
    },
]


# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch(
        "simulation.decisions.ai_driven_household_engine.logger"
    ) as mock_hh_logger:
        with patch(
            "simulation.decisions.ai_driven_firm_engine.logger"
        ) as mock_firm_logger:
            mock_hh_logger_instance = MagicMock(name="household_logger")
            mock_firm_logger_instance = MagicMock(name="firm_logger")
            mock_hh_logger.return_value = mock_hh_logger_instance
            mock_firm_logger.return_value = mock_firm_logger_instance
            yield mock_hh_logger_instance  # Yield one of them, or both if needed separately


@pytest.fixture
def household():
    hh = Mock(spec=Household)
    hh.id = 1

    # Initialize nested states
    hh._econ_state = Mock()
    hh._econ_state.assets = 1000.0
    hh._econ_state.inventory = {"food": 10.0}
    hh._econ_state.is_employed = False
    hh._econ_state.perceived_avg_prices = {"food": 10.0}

    hh._bio_state = Mock()
    hh._bio_state.needs = {"survival_need": 50.0, "labor_need": 0.0}

    hh._social_state = Mock()

    hh.goods_info_map = {g["id"]: g for g in GOODS_DATA}
    hh.decision_engine = Mock(spec=AIDrivenHouseholdDecisionEngine)
    hh.decision_engine.ai_engine = (
        Mock()
    )  # Mock the AI engine within the decision engine
    return hh


@pytest.fixture
def firm():
    f = Mock(spec=Firm)
    f.id = 1
    f._assets = 10000.0
    f.inventory = {"food": 50.0}
    f.employees = []
    f.production_targets = {"food": 100.0}
    f.productivity_factor = 1.0
    f.revenue_this_turn = 0.0
    f.cost_this_turn = 0.0
    f.decision_engine = Mock(spec=AIDrivenFirmDecisionEngine)
    f.decision_engine.ai_engine = (
        Mock()
    )  # Mock the AI engine within the decision engine
    return f


@pytest.fixture
def goods_market():
    market = OrderBookMarket("goods_market")
    return market


@pytest.fixture
def labor_market():
    market = OrderBookMarket("labor_market")
    return market


@pytest.fixture(autouse=True)
def set_config_for_tests():
    original_values = {}
    test_values = {
        "HOUSEHOLD_RESERVATION_PRICE_BASE": 5.0,
        "HOUSEHOLD_NEED_PRICE_MULTIPLIER": 1.0,
        "HOUSEHOLD_ASSET_PRICE_MULTIPLIER": 0.1,
        "HOUSEHOLD_PRICE_ELASTICITY_FACTOR": 0.5,
        "HOUSEHOLD_STOCKPILING_BONUS_FACTOR": 0.2,
        "MIN_SELL_PRICE": 1.0,
        "GOODS_MARKET_SELL_PRICE": 10.0,
        "LABOR_NEED_THRESHOLD": 50.0,
        "HOUSEHOLD_MIN_WAGE_DEMAND": 10.0,
        "WAGE_DECAY_RATE": 0.9,
        "RND_WAGE_PREMIUM": 1.5,
        "GROWTH_NEED_THRESHOLD": 60.0,
        "IMITATION_NEED_THRESHOLD": 70.0,
        "IMITATION_ASSET_THRESHOLD": 500.0,
        "CHILD_REARING_NEED_THRESHOLD": 80.0,
        "CHILD_REARING_ASSET_THRESHOLD": 1000.0,
        "SURVIVAL_NEED_THRESHOLD": 30.0,
        "ASSETS_THRESHOLD_FOR_OTHER_ACTIONS": 200.0,
        "RECOGNITION_NEED_THRESHOLD": 40.0,
        "LIQUIDITY_RATIO_MAX": 0.8,
        "LIQUIDITY_RATIO_MIN": 0.1,
        "LIQUIDITY_RATIO_DIVISOR": 100.0,
    }

    for key, value in test_values.items():
        if hasattr(config, key):
            original_values[key] = getattr(config, key)
        setattr(config, key, value)

    yield

    for key, value in original_values.items():
        setattr(config, key, value)


class TestDecisionEngineIntegration:

    def test_firm_places_sell_order_for_food(
        self, firm: Firm, goods_market: OrderBookMarket
    ):
        """기업이 식량 판매 주문을 올바르게 제출하는지 테스트합니다."""
        # Configure the mock instance directly
        firm.make_decision.return_value = (
            [
                Order(
                    agent_id=firm.id,
                    side="SELL",
                    item_id="food",
                    quantity=10.0,
                    price_limit=15.0,
                    market_id="goods_market",
                )
            ],
            (Tactic.ADJUST_PRICE, Aggressiveness.NORMAL)
        )
        markets = {"goods_market": goods_market}

        input_dto = DecisionInputDTO(
            goods_data=GOODS_DATA,
            market_data={"all_households": [], "goods_data": GOODS_DATA},
            current_time=1,
            market_snapshot=MarketSnapshotDTO(tick=1, market_signals={}, housing=None, loan=None, labor=None)
        )
        orders, _ = firm.make_decision(input_dto)

        for order in orders:
            goods_market.place_order(order, current_time=1)

        assert len(goods_market.sell_orders["food"]) == 1
        assert goods_market.sell_orders["food"][0].agent_id == firm.id

    def test_household_places_buy_order_for_food(
        self, household: Household, goods_market: OrderBookMarket
    ):
        """가계가 식량 구매 주문을 올바르게 제출하는지 테스트합니다."""
        household._bio_state.needs["survival_need"] = 80.0
        household._econ_state.inventory["food"] = 0.0

        # Configure the mock instance directly
        household.make_decision.return_value = (
            [
                Order(
                    agent_id=household.id,
                    side="BUY",
                    item_id="food",
                    quantity=1.0,
                    price_limit=1.6,
                    market_id="goods_market",
                )
            ],
            (Tactic.EVALUATE_CONSUMPTION_OPTIONS, Aggressiveness.NORMAL)
        )

        markets = {"goods_market": goods_market}

        input_dto = DecisionInputDTO(
            goods_data=GOODS_DATA,
            market_data={"all_households": [], "goods_data": GOODS_DATA},
            current_time=1,
            market_snapshot=MarketSnapshotDTO(tick=1, market_signals={}, housing=None, loan=None, labor=None)
        )
        orders, _ = household.make_decision(input_dto)

        for order in orders:
            goods_market.place_order(order, current_time=1)

        assert len(orders) > 0
        assert len(goods_market.buy_orders["food"]) == 1
        assert goods_market.buy_orders["food"][0].agent_id == household.id

    def test_household_sells_labor(
        self, household: Household, labor_market: OrderBookMarket
    ):
        """가계가 노동 판매 주문을 올바르게 제출하는지 테스트합니다."""
        household._econ_state.is_employed = False
        household._bio_state.needs["labor_need"] = 50
        household._bio_state.needs["survival_need"] = 10.0

        # Configure the mock instance directly
        household.make_decision.return_value = (
            [
                Order(
                    agent_id=household.id,
                    side="SELL",
                    item_id="labor",
                    quantity=1,
                    price_limit=10,
                    market_id="labor_market",
                )
            ],
            (Tactic.PARTICIPATE_LABOR_MARKET, Aggressiveness.NORMAL)
        )
        markets = {"labor_market": labor_market}

        input_dto = DecisionInputDTO(
            goods_data=GOODS_DATA,
            market_data={"all_households": [household], "goods_data": GOODS_DATA},
            current_time=1,
            market_snapshot=MarketSnapshotDTO(tick=1, market_signals={}, housing=None, loan=None, labor=None)
        )
        orders, _ = household.make_decision(input_dto)

        for order in orders:
            labor_market.place_order(order, current_time=1)

        assert len(labor_market.sell_orders["labor"]) == 1
        assert labor_market.sell_orders["labor"][0].agent_id == household.id

    def test_firm_buys_labor(
        self, firm: Firm, labor_market: OrderBookMarket
    ):
        """기업이 노동 구매 주문을 올바르게 제출하는지 테스트합니다."""
        firm.employees = []

        # Configure the mock instance directly
        firm.make_decision.return_value = (
            [
                Order(
                    agent_id=firm.id,
                    side="BUY",
                    item_id="labor",
                    quantity=1,
                    price_limit=10,
                    market_id="labor_market",
                )
            ],
            (Tactic.ADJUST_WAGES, Aggressiveness.NORMAL)
        )
        markets = {"labor_market": labor_market}

        input_dto = DecisionInputDTO(
            goods_data=GOODS_DATA,
            market_data={"all_households": [], "goods_data": GOODS_DATA},
            current_time=1,
            market_snapshot=MarketSnapshotDTO(tick=1, market_signals={}, housing=None, loan=None, labor=None)
        )
        orders, _ = firm.make_decision(input_dto)

        for order in orders:
            labor_market.place_order(order, current_time=1)

        assert len(labor_market.buy_orders["labor"]) == 1
        assert labor_market.buy_orders["labor"][0].agent_id == firm.id

    def test_goods_market_matching_integration(
        self, household: Household, firm: Firm, goods_market: OrderBookMarket
    ):
        """가계와 기업의 주문이 상품 시장에서 올바르게 매칭되는지 통합 테스트합니다."""
        firm_sell_order = Order(
            agent_id=firm.id,
            side="SELL",
            item_id="food",
            quantity=5.0,
            price_limit=10.0,
            market_id="goods_market",
        )
        goods_market.place_order(firm_sell_order, current_time=1)
        assert (
            "food" in goods_market.sell_orders
            and len(goods_market.sell_orders["food"]) == 1
        )

        household_buy_order = Order(
            agent_id=household.id,
            side="BUY",
            item_id="food",
            quantity=5.0,
            price_limit=10.0,
            market_id="goods_market",
        )
        goods_market.place_order(household_buy_order, current_time=1)

        transactions = goods_market.match_orders(current_time=1)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.item_id == "food"
        assert tx.quantity == 5.0
        assert tx.price == 10.0
        assert tx.buyer_id == household.id
        assert tx.seller_id == firm.id
        assert not goods_market.sell_orders.get("food")
        assert not goods_market.buy_orders.get("food")

    def test_labor_market_matching_integration(
        self, household: Household, firm: Firm, labor_market: OrderBookMarket
    ):
        """가계와 기업의 주문이 노동 시장에서 올바르게 매칭되는지 통합 테스트합니다."""
        household._econ_state.is_employed = False
        household._bio_state.needs["labor_need"] = 50
        household._bio_state.needs["survival_need"] = 10.0
        household_sell_order = Order(
            agent_id=household.id,
            side="SELL",
            item_id="labor",
            quantity=1,
            price_limit=10,
            market_id="labor_market",
        )
        labor_market.place_order(household_sell_order, current_time=1)
        assert "labor" in labor_market.sell_orders

        firm.employees = []
        firm_buy_order = Order(
            agent_id=firm.id,
            side="BUY",
            item_id="labor",
            quantity=1,
            price_limit=10,
            market_id="labor_market",
        )
        labor_market.place_order(firm_buy_order, current_time=1)

        transactions = labor_market.match_orders(current_time=1)

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.item_id == "labor"
        assert tx.quantity == 1
        assert tx.price == 10.0
        assert tx.buyer_id == firm.id
        assert tx.seller_id == household.id
        assert not labor_market.sell_orders.get("labor")
        assert not labor_market.buy_orders.get("labor")
