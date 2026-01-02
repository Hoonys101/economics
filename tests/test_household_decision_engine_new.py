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
from simulation.schemas import HouseholdActionVector


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
    config.MARKET_PRICE_FALLBACK = 10.0
    config.NEED_FACTOR_BASE = 1.0
    config.NEED_FACTOR_SCALE = 100.0
    config.VALUATION_MODIFIER_BASE = 1.0
    config.VALUATION_MODIFIER_RANGE = 0.5
    config.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5
    config.BULK_BUY_NEED_THRESHOLD = 0.7
    config.BULK_BUY_AGG_THRESHOLD = 0.8
    config.BULK_BUY_MODERATE_RATIO = 0.5
    config.BUDGET_LIMIT_NORMAL_RATIO = 0.5
    config.BUDGET_LIMIT_URGENT_NEED = 0.9
    config.BUDGET_LIMIT_URGENT_RATIO = 0.9
    config.MIN_PURCHASE_QUANTITY = 1
    config.LABOR_MARKET_MIN_WAGE = 5.0
    config.JOB_QUIT_THRESHOLD_BASE = 1.5
    config.RESERVATION_WAGE_BASE = 1.0
    config.RESERVATION_WAGE_RANGE = 0.5
    config.STOCK_MARKET_ENABLED = False
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
    hh.shares_owned = {}
    return hh


@pytest.fixture
def mock_ai_engine():
    ai = Mock(spec=HouseholdAI)
    # Default V2 Mock Return
    ai.decide_action_vector.return_value = HouseholdActionVector(
        consumption_aggressiveness={},
        work_aggressiveness=0.5,
        job_mobility_aggressiveness=0.5,
        investment_aggressiveness=0.0,
        learning_aggressiveness=0.0
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
        mock_ai_engine.decide_action_vector.assert_called_once()

    def test_consumption_do_nothing(
        self, decision_engine, mock_household, mock_ai_engine
    ):
        # V2: "Do Nothing" is simulated by very low consumption aggressiveness
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
            consumption_aggressiveness={"basic_food": 0.0, "luxury_food": 0.0}
        )

        # Also need high price or low need to prevent buy.
        # With default config and need=0.8, even 0.0 agg might buy if price is low.
        # But if valuation modifier makes WTP low...
        # Let's set price high.

        market_data = {
            "goods_market": {
                "basic_food_avg_traded_price": 1000.0,
                "luxury_food_avg_traded_price": 1000.0
            }
        }

        context = DecisionContext(
            household=mock_household,
            markets={},
            goods_data=[],
            market_data=market_data,
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        # Ignore labor sell order
        buy_orders = [o for o in orders if o.order_type == "BUY"]
        assert len(buy_orders) == 0

    def test_consumption_buy_basic_food_sufficient_assets(
        self, decision_engine, mock_household, mock_ai_engine, mock_config
    ):
        # V2: Set aggressiveness for basic_food
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
            consumption_aggressiveness={"basic_food": 0.8}
        )

        market_data = {
            "goods_market": {
                "basic_food_avg_traded_price": 10.0
            }
        }

        context = DecisionContext(
            household=mock_household,
            markets={},
            goods_data=[],
            market_data=market_data,
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        buy_orders = [o for o in orders if o.order_type == "BUY" and o.item_id == "basic_food"]
        assert len(buy_orders) == 1
        # WTP calculation involves need factor and valuation modifier.
        # WTP > 0.
        assert buy_orders[0].price > 0

    def test_consumption_buy_luxury_food_insufficient_assets(
        self, decision_engine, mock_household, mock_ai_engine, mock_config
    ):
        # Aggressive buy but price is way too high
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
            consumption_aggressiveness={"luxury_food": 1.0}
        )
        
        market_data = {
            "goods_market": {
                "luxury_food_avg_traded_price": 1000.0
            }
        }
        
        mock_household.assets = 100.0 # Can't afford much

        context = DecisionContext(
            household=mock_household,
            markets={},
            goods_data=[],
            market_data=market_data,
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        # Logic: WTP might be high, but quantity might be reduced to fit budget.
        # If min purchase quantity is 1, and price > budget, should be 0.
        # 1000 * 1 > 100.

        buy_orders = [o for o in orders if o.order_type == "BUY" and o.item_id == "luxury_food"]

        # If budget check works properly, quantity becomes < 1 if WTP is around price.
        # If WTP is super high (e.g. 2000), quantity check: 100 / 2000 = 0.05.
        # max(1, int(0.05)) -> Wait, max(1, 0) is 1.
        # But wait, logic:
        # target_quantity = budget_limit / willingness_to_pay
        # If WTP > price, say WTP=1000. Budget=100. Q = 0.1.
        # if target_quantity >= min_purchase_quantity (1)...
        # 0.1 < 1. So no order.

        assert len(buy_orders) == 0

    def test_labor_market_participation_aggressive(
        self, decision_engine, mock_household, mock_ai_engine
    ):
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
            work_aggressiveness=1.0 # High aggressiveness -> Low Reservation Wage
        )

        # Market Avg Wage = 10.0
        market_data = {
            "goods_market": {
                "labor": {"avg_wage": 10.0}
            }
        }

        context = DecisionContext(
            household=mock_household,
            markets={},
            goods_data=[],
            market_data=market_data,
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        labor_orders = [o for o in orders if o.order_type == "SELL" and o.item_id == "labor"]
        assert len(labor_orders) == 1
        # With agg=1.0, reservation modifier = 1.0 - (1.0 * 0.5) = 0.5
        # Res Wage = 10.0 * 0.5 = 5.0.
        assert labor_orders[0].price == 5.0

    def test_labor_market_participation_passive(
        self, decision_engine, mock_household, mock_ai_engine
    ):
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
            work_aggressiveness=0.0 # Low aggressiveness -> High Reservation Wage
        )

        market_data = {
            "goods_market": {
                "labor": {"avg_wage": 10.0}
            }
        }

        context = DecisionContext(
            household=mock_household,
            markets={},
            goods_data=[],
            market_data=market_data,
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        labor_orders = [o for o in orders if o.order_type == "SELL" and o.item_id == "labor"]
        assert len(labor_orders) == 1
        # With agg=0.0, reservation modifier = 1.0 - (0.0 * 0.5) = 1.0
        # Res Wage = 10.0 * 1.0 = 10.0.
        assert labor_orders[0].price == 10.0
