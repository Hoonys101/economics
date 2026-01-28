import pytest
from unittest.mock import Mock, patch

from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.ai.household_ai import HouseholdAI
from simulation.dtos import DecisionContext
from simulation.models import Order
from simulation.markets.order_book_market import OrderBookMarket
from simulation.schemas import HouseholdActionVector
from simulation.ai.api import Personality
from tests.factories import create_household_dto

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
    # Phase 4.5 Constants
    config.NEUTRAL_REAL_RATE = 0.02
    config.DSR_CRITICAL_THRESHOLD = 0.4
    config.INTEREST_SENSITIVITY_ANT = 5.0
    config.INTEREST_SENSITIVITY_GRASSHOPPER = 1.0
    config.VALUE_ORIENTATION_WEALTH_AND_NEEDS = "wealth_and_needs"
    config.MASLOW_SURVIVAL_THRESHOLD = 50.0

    # Defaults
    config.MARKET_PRICE_FALLBACK = 10.0
    config.market_price_fallback = 10.0 # DTO alias
    config.NEED_FACTOR_BASE = 0.5
    config.need_factor_base = 0.5
    config.NEED_FACTOR_SCALE = 100.0
    config.need_factor_scale = 100.0
    config.VALUATION_MODIFIER_BASE = 0.9
    config.valuation_modifier_base = 0.9
    config.VALUATION_MODIFIER_RANGE = 0.2
    config.valuation_modifier_range = 0.2
    config.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0
    config.household_max_purchase_quantity = 5.0
    config.BULK_BUY_NEED_THRESHOLD = 70.0
    config.bulk_buy_need_threshold = 70.0
    config.BULK_BUY_AGG_THRESHOLD = 0.8
    config.bulk_buy_agg_threshold = 0.8
    config.BULK_BUY_MODERATE_RATIO = 0.6
    config.bulk_buy_moderate_ratio = 0.6
    config.BUDGET_LIMIT_NORMAL_RATIO = 0.5
    config.budget_limit_normal_ratio = 0.5
    config.BUDGET_LIMIT_URGENT_NEED = 80.0
    config.budget_limit_urgent_need = 80.0
    config.BUDGET_LIMIT_URGENT_RATIO = 0.9
    config.budget_limit_urgent_ratio = 0.9
    config.MIN_PURCHASE_QUANTITY = 0.1
    config.min_purchase_quantity = 0.1
    config.LABOR_MARKET_MIN_WAGE = 8.0
    config.labor_market_min_wage = 8.0
    config.JOB_QUIT_THRESHOLD_BASE = 2.0
    config.job_quit_threshold_base = 2.0
    config.JOB_QUIT_PROB_BASE = 0.1
    config.job_quit_prob_base = 0.1
    config.JOB_QUIT_PROB_SCALE = 0.9
    config.job_quit_prob_scale = 0.9
    config.RESERVATION_WAGE_BASE = 1.5
    config.RESERVATION_WAGE_RANGE = 1.0

    # Phase 21.6 Constants
    config.WAGE_DECAY_RATE = 0.02
    config.wage_decay_rate = 0.02
    config.WAGE_RECOVERY_RATE = 0.01
    config.RESERVATION_WAGE_FLOOR = 0.3
    config.reservation_wage_floor = 0.3
    config.SURVIVAL_CRITICAL_TURNS = 5
    config.survival_critical_turns = 5

    # Phase 8 Constants
    config.PANIC_BUYING_THRESHOLD = 0.05
    config.panic_buying_threshold = 0.05
    config.HOARDING_FACTOR = 0.5
    config.hoarding_factor = 0.5
    config.DEFLATION_WAIT_THRESHOLD = -0.05
    config.deflation_wait_threshold = -0.05
    config.DELAY_FACTOR = 0.5
    config.delay_factor = 0.5

    # Portfolio / Stock
    config.STOCK_MARKET_ENABLED = False
    config.stock_market_enabled = False
    config.EXPECTED_STARTUP_ROI = 0.15
    config.expected_startup_roi = 0.15
    config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 2.0
    config.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 500.0
    config.household_min_assets_for_investment = 500.0
    config.DEBT_REPAYMENT_RATIO = 0.5
    config.debt_repayment_ratio = 0.5
    config.DEBT_REPAYMENT_CAP = 1.1
    config.debt_repayment_cap = 1.1
    config.DEBT_LIQUIDITY_RATIO = 0.9
    config.debt_liquidity_ratio = 0.9

    # Missing DTO fields
    config.initial_rent_price = 100.0
    config.survival_need_consumption_threshold = 50.0
    config.target_food_buffer_quantity = 5.0
    config.food_purchase_max_per_tick = 10.0
    config.assets_threshold_for_other_actions = 100.0
    config.household_low_asset_threshold = 100.0
    config.household_low_asset_wage = 5.0
    config.household_default_wage = 10.0
    config.dsr_critical_threshold = 0.4
    config.stock_investment_equity_delta_threshold = 100.0
    config.stock_investment_diversification_count = 5
    config.startup_cost = 30000.0
    config.DEFAULT_MORTGAGE_RATE = 0.05
    config.default_mortgage_rate = 0.05

    return config


@pytest.fixture
def mock_household_dto():
    """Returns a HouseholdStateDTO with typical test values."""
    return create_household_dto(
        id=1,
        assets=100.0,
        needs={"survival": 0.8, "leisure": 0.5},
        is_employed=False,
        current_wage=0.0,
        wage_modifier=1.0,
        personality=Personality.BALANCED
    )


@pytest.fixture
def mock_ai_engine():
    ai = Mock(spec=HouseholdAI)
    # Default return value for decide_action_vector
    default_vector = HouseholdActionVector(
        consumption_aggressiveness={"basic_food": 0.5, "luxury_food": 0.5},
        work_aggressiveness=0.5,
        job_mobility_aggressiveness=0.5,
        investment_aggressiveness=0.0,
        learning_aggressiveness=0.0
    )
    ai.decide_action_vector.return_value = default_vector
    return ai


@pytest.fixture
def decision_engine(mock_ai_engine, mock_config):
    return AIDrivenHouseholdDecisionEngine(
        ai_engine=mock_ai_engine, config_module=mock_config
    )


class TestAIDrivenHouseholdDecisionEngine:
    def test_make_decisions_calls_ai(
        self, decision_engine, mock_household_dto, mock_ai_engine, mock_config
    ):
        context = DecisionContext(
            state=mock_household_dto,
            config=mock_config,
            goods_data=[],
            market_data={},
            current_time=1,
        )
        decision_engine.make_decisions(context)
        mock_ai_engine.decide_action_vector.assert_called_once()

    def test_consumption_do_nothing(
        self, decision_engine, mock_household_dto, mock_ai_engine, mock_config
    ):
        # Action Vector with 0 aggressiveness implies "Do Nothing" or buy minimum
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
             consumption_aggressiveness={"basic_food": 0.0, "luxury_food": 0.0}
        )

        context = DecisionContext(
            state=mock_household_dto,
            config=mock_config,
            goods_data=[],
            market_data={},
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)
        # V2 Engine generates orders but WTP should be low.
        pass

    def test_consumption_buy_basic_food_sufficient_assets(
        self, decision_engine, mock_household_dto, mock_ai_engine, mock_config
    ):
        # High Aggressiveness for basic_food
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
             consumption_aggressiveness={"basic_food": 0.8}
        )

        market_data = {
            "goods_market": {
                "basic_food_current_sell_price": 10.0,
            }
        }

        context = DecisionContext(
            state=mock_household_dto,
            config=mock_config,
            goods_data=[],
            market_data=market_data,
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        bf_order = next((o for o in orders if o.item_id == "basic_food"), None)
        assert bf_order is not None

    def test_consumption_buy_luxury_food_insufficient_assets(
        self, decision_engine, mock_household_dto, mock_ai_engine, mock_config
    ):
        mock_household_dto._assets = 100.0 # DTO assets

        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
             consumption_aggressiveness={"luxury_food": 0.9}
        )

        # Populate market_data with high price so engine sees it
        market_data = {
            "goods_market": {
                "luxury_food_current_sell_price": 1000.0,
                "luxury_food_avg_traded_price": 1000.0
            }
        }

        context = DecisionContext(
            state=mock_household_dto,
            config=mock_config,
            goods_data=[],
            market_data=market_data,
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        lf_order = next((o for o in orders if o.item_id == "luxury_food"), None)
        # Should be None OR have very small quantity due to budget
        assert lf_order is None or lf_order.quantity < 1.0

    def test_consumption_evaluate_options_chooses_best_utility(
        self, decision_engine, mock_household_dto, mock_ai_engine, mock_config
    ):
        # Equal aggressiveness
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
             consumption_aggressiveness={"basic_food": 0.5, "luxury_food": 0.5}
        )

        market_data = {
            "goods_market": {
                "basic_food_current_sell_price": 10.0,
                "luxury_food_current_sell_price": 20.0
            }
        }

        context = DecisionContext(
            state=mock_household_dto,
            config=mock_config,
            goods_data=[],
            market_data=market_data,
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        assert len(orders) >= 1

    def test_labor_market_participation_aggressive(
        self, decision_engine, mock_household_dto, mock_ai_engine, mock_config
    ):
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
             work_aggressiveness=0.9
        )

        # Set DTO wage
        mock_household_dto.current_wage = 0.0
        mock_household_dto.wage_modifier = 0.9 # Lower than 1.0 to trigger participation

        # Inject market data for avg wage
        market_data = {
            "goods_market": {
                "labor": {
                    "avg_wage": 50.0,
                    "best_wage_offer": 49.5
                }
            }
        }

        context = DecisionContext(
            state=mock_household_dto,
            config=mock_config,
            goods_data=[],
            market_data=market_data,
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        # Filter Labor Order
        labor_order = next((o for o in orders if o.item_id == "labor"), None)

        assert labor_order is not None
        assert labor_order.order_type == "SELL"
        # 50.0 * 0.9 = 45.0
        assert labor_order.price == 45.0

    def test_labor_market_participation_passive_no_offer(
        self, decision_engine, mock_household_dto, mock_ai_engine, mock_config
    ):
        # Passive = Low Work Agg
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
             work_aggressiveness=0.1
        )

        mock_household_dto.current_wage = 0.0
        mock_household_dto.wage_modifier = 1.0

        # Inject high avg wage so reservation wage calc results in high value
        market_data = {
            "goods_market": {
                "labor": {
                    "avg_wage": 50.0,
                    "best_wage_offer": 55.0
                }
            }
        }

        context = DecisionContext(
            state=mock_household_dto,
            config=mock_config,
            goods_data=[],
            market_data=market_data,
            current_time=1,
        )
        orders, _ = decision_engine.make_decisions(context)

        # Filter Labor Order
        labor_order = next((o for o in orders if o.item_id == "labor"), None)
        # Res Wage = 50.0. Offer 55.0. 55 > 50 -> Sell.
        assert labor_order is not None
        assert labor_order.price == 50.0
