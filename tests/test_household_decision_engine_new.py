import pytest
from unittest.mock import Mock, patch

from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.core_agents import Household
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.enums import Tactic, Aggressiveness
from simulation.dtos import DecisionContext
from simulation.models import Order
from simulation.markets.order_book_market import OrderBookMarket


# Mock Logger
@pytest.fixture(autouse=True)
def mock_logger_fixture():
    with patch(
        "simulation.decisions.ai_driven_household_engine.logging.getLogger"
    ) as mock_get_logger:
        yield mock_get_logger


@pytest.fixture
def mock_config():
    config = Mock()
    config.GOODS = {
        "basic_food": {"utility_effects": {"survival": 10}},
        "luxury_food": {"utility_effects": {"leisure": 10}},
    }
    return config


@pytest.fixture
def mock_household():
    hh = Mock(spec=Household)
    hh.id = 1
    hh.assets = 100.0
    hh.needs = {"survival": 0.8, "leisure": 0.5}
    hh.get_agent_data.return_value = {}
    hh.get_pre_state_data.return_value = {}
    hh.get_desired_wage.return_value = 50.0
    hh.perceived_avg_prices = {}
    hh.inventory = {}
    hh.is_employed = False
    return hh


@pytest.fixture
def mock_ai_engine():
    ai = Mock(spec=HouseholdAI)
    ai.decide_and_learn.return_value = (
        Tactic.DO_NOTHING_CONSUMPTION,
        Aggressiveness.NORMAL,
    )
    return ai


@pytest.fixture
def decision_engine(mock_ai_engine, mock_config):
    return AIDrivenHouseholdDecisionEngine(
        ai_engine=mock_ai_engine, config_module=mock_config
    )


class TestAIDrivenHouseholdDecisionEngine:
    def test_make_decisions_calls_ai(
        self, decision_engine, mock_household, mock_ai_engine
    ):
        context = DecisionContext(
            household=mock_household,
            markets={},
            goods_data=[],
            market_data={},
            current_time=1,
        )
        decision_engine.make_decisions(context)
        mock_ai_engine.decide_and_learn.assert_called_once()

    def test_consumption_do_nothing(
        self, decision_engine, mock_household, mock_ai_engine
    ):
        mock_ai_engine.decide_and_learn.return_value = (
            Tactic.DO_NOTHING_CONSUMPTION,
            Aggressiveness.NORMAL,
        )
        context = DecisionContext(
            household=mock_household,
            markets={},
            goods_data=[],
            market_data={},
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)
        assert len(orders) == 0

    def test_consumption_buy_basic_food_sufficient_assets(
        self, decision_engine, mock_household, mock_ai_engine, mock_config
    ):
        mock_goods_market = Mock(spec=OrderBookMarket, id="goods_market")
        mock_goods_market.get_best_ask.return_value = 10.0
        mock_markets = {"goods_market": mock_goods_market}
        
        mock_ai_engine.decide_and_learn.return_value = (
            Tactic.BUY_BASIC_FOOD,
            Aggressiveness.NORMAL,
        )

        context = DecisionContext(
            household=mock_household,
            markets=mock_markets,
            goods_data=[],
            market_data={},
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        assert len(orders) == 1
        assert orders[0].item_id == "basic_food"
        assert orders[0].price == 10.0

    def test_consumption_buy_luxury_food_insufficient_assets(
        self, decision_engine, mock_household, mock_ai_engine, mock_config
    ):
        mock_goods_market = Mock(spec=OrderBookMarket, id="goods_market")
        mock_goods_market.get_best_ask.return_value = 1000.0
        mock_markets = {"goods_market": mock_goods_market}
        
        mock_household.assets = 100.0
        mock_ai_engine.decide_and_learn.return_value = (
            Tactic.BUY_LUXURY_FOOD,
            Aggressiveness.AGGRESSIVE,
        )

        context = DecisionContext(
            household=mock_household,
            markets=mock_markets,
            goods_data=[],
            market_data={},
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        assert len(orders) == 0

    def test_consumption_evaluate_options_chooses_best_utility(
        self, decision_engine, mock_household, mock_ai_engine, mock_config
    ):
        mock_goods_market = Mock(spec=OrderBookMarket, id="goods_market")
        # Utility/dollar = (0.8*10)/10 = 0.8 for basic_food
        # Utility/dollar = (0.5*10)/20 = 0.25 for luxury_food
        mock_goods_market.get_best_ask.side_effect = lambda item_id: 10.0 if item_id == "basic_food" else (20.0 if item_id == "luxury_food" else None)
        
        mock_markets = {"goods_market": mock_goods_market}
        
        mock_ai_engine.decide_and_learn.return_value = (
            Tactic.EVALUATE_CONSUMPTION_OPTIONS,
            Aggressiveness.NORMAL,
        )

        context = DecisionContext(
            household=mock_household,
            markets=mock_markets,
            goods_data=[],
            market_data={},
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        assert len(orders) == 1
        assert orders[0].item_id == "basic_food"  # Higher utility per dollar

    def test_labor_market_participation_aggressive(
        self, decision_engine, mock_household, mock_ai_engine
    ):
        mock_labor_market = Mock(spec=OrderBookMarket, id="labor_market")
        mock_labor_market.get_all_bids = Mock(
            return_value=[Order(2, "BUY", "labor", 1, 45.0, "labor_market")]
        )
        mock_markets = {"labor": mock_labor_market}
        mock_ai_engine.decide_and_learn.return_value = (
            Tactic.PARTICIPATE_LABOR_MARKET,
            Aggressiveness.AGGRESSIVE,
        )
        mock_household.get_desired_wage.return_value = 50.0  # Base reservation wage

        context = DecisionContext(
            household=mock_household,
            markets=mock_markets,
            goods_data=[],
            market_data={},
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        assert len(orders) == 1
        assert orders[0].order_type == "SELL"
        assert orders[0].item_id == "labor"
        assert orders[0].price == 45.0  # Accepts lower wage due to aggressiveness

    def test_labor_market_participation_passive_no_offer(
        self, decision_engine, mock_household, mock_ai_engine
    ):
        mock_labor_market = Mock(spec=OrderBookMarket, id="labor_market")
        mock_labor_market.get_all_bids = Mock(
            return_value=[Order(2, "BUY", "labor", 1, 55.0, "labor_market")]
        )
        mock_markets = {"labor": mock_labor_market}
        mock_ai_engine.decide_and_learn.return_value = (
            Tactic.PARTICIPATE_LABOR_MARKET,
            Aggressiveness.PASSIVE,
        )
        mock_household.get_desired_wage.return_value = (
            50.0  # Base reservation wage (adjusted to 60)
        )

        context = DecisionContext(
            household=mock_household,
            markets=mock_markets,
            goods_data=[],
            market_data={},
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        assert len(orders) == 0  # Does not accept offer below adjusted reservation wage
