import pytest
from unittest.mock import Mock, MagicMock

from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.core_agents import Household
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.enums import Tactic, Aggressiveness
from simulation.dtos import DecisionContext, HouseholdConfigDTO
from modules.household.dtos import HouseholdStateDTO
from simulation.markets.order_book_market import OrderBookMarket


# Mock config_module for testing purposes
class MockConfig:
    GOODS = {
        "basic_food": {"production_cost": 3, "utility_effects": {"survival": 10}},
        "luxury_food": {
            "production_cost": 10,
            "utility_effects": {"survival": 12, "social": 5},
        },
        "education_service": {
            "production_cost": 50,
            "utility_effects": {"improvement": 20},
        },
    }
    SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 50.0
    BASE_DESIRE_GROWTH = 1.0
    MAX_DESIRE_VALUE = 100.0
    PERCEIVED_FAIR_PRICE_THRESHOLD_FACTOR = 0.9
    FOOD_PURCHASE_MAX_PER_TICK = 5.0
    TARGET_FOOD_BUFFER_QUANTITY = 5.0
    HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0
    LABOR_MARKET_MIN_WAGE = 8.0
    # New config constants for refactored code
    MARKET_PRICE_FALLBACK = 10.0
    NEED_FACTOR_BASE = 0.5
    NEED_FACTOR_SCALE = 100.0
    VALUATION_MODIFIER_BASE = 0.9
    VALUATION_MODIFIER_RANGE = 0.2
    BULK_BUY_NEED_THRESHOLD = 70.0
    BULK_BUY_AGG_THRESHOLD = 0.8
    BULK_BUY_MODERATE_RATIO = 0.6
    BUDGET_LIMIT_NORMAL_RATIO = 0.5
    BUDGET_LIMIT_URGENT_NEED = 80.0
    BUDGET_LIMIT_URGENT_RATIO = 0.9
    MIN_PURCHASE_QUANTITY = 0.1
    JOB_QUIT_THRESHOLD_BASE = 2.0
    JOB_QUIT_PROB_BASE = 0.1
    JOB_QUIT_PROB_SCALE = 0.9
    RESERVATION_WAGE_BASE = 1.5
    RESERVATION_WAGE_RANGE = 1.0

    # Missing fields
    DEFAULT_MORTGAGE_RATE = 0.05
    DSR_CRITICAL_THRESHOLD = 0.4
    DEBT_REPAYMENT_RATIO = 0.1
    DEBT_REPAYMENT_CAP = 0.5
    DEBT_LIQUIDITY_RATIO = 0.5
    INITIAL_RENT_PRICE = 100.0
    ENABLE_VANITY_SYSTEM = False
    MIMICRY_FACTOR = 0.1
    MAINTENANCE_RATE_PER_TICK = 0.01
    STOCK_MARKET_ENABLED = False
    HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 1000.0
    STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD = 100.0
    STOCK_INVESTMENT_DIVERSIFICATION_COUNT = 5
    EXPECTED_STARTUP_ROI = 0.15
    STARTUP_COST = 30000.0


@pytest.fixture
def mock_config_module():
    return MockConfig()


@pytest.fixture
def mock_household(mock_config_module):
    household = Mock(spec=Household)
    household.id = 1
    household.assets = 100.0
    household.inventory = {"basic_food": 0, "luxury_food": 0}
    household.needs = {
        "survival": 70.0,
        "social": 30.0,
        "improvement": 10.0,
        "asset": 50.0,
    }
    household.perceived_avg_prices = {}
    household.config_module = mock_config_module
    household.get_agent_data.return_value = {
        "assets": household.assets,
        "needs": household.needs.copy(),
        "inventory": household.inventory.copy(),
    }
    household.logger = MagicMock()  # Mock the logger
    household.current_wage = 10.0
    household.is_employed = True
    household.portfolio = {}
    household.owned_properties = []
    household.expected_inflation = {} # Add explicit dictionary for inflation
    household.durable_assets = [] # Add explicit list for durable assets

    # Add personality for DTO
    from simulation.ai.api import Personality
    household.personality = Personality.BALANCED

    return household


@pytest.fixture
def mock_ai_engine_registry():
    registry = Mock()
    mock_ai_decision_engine = Mock()
    mock_ai_decision_engine.is_trained = True
    registry.get_engine.return_value = mock_ai_decision_engine
    return registry


@pytest.fixture
def household_decision_engine(
    mock_household, mock_ai_engine_registry, mock_config_module
):
    # Create a mock for the ai_engine
    mock_ai_engine = Mock(spec=HouseholdAI)
    # Set the ai_engine for the AIDrivenHouseholdDecisionEngine
    engine = AIDrivenHouseholdDecisionEngine(
        ai_engine=mock_ai_engine,  # Pass the mock ai_engine here
        config_module=mock_config_module,
    )
    return engine, mock_ai_engine  # Return both the engine and its mock ai_engine


@pytest.fixture
def mock_markets():
    markets = {
        "goods_market": Mock(spec=OrderBookMarket),
        "labor_market": Mock(spec=OrderBookMarket),
        "loan_market": Mock(),
    }
    # Set return values for get_best_ask
    markets["goods_market"].get_best_ask.side_effect = lambda item_id: {
        "basic_food": 5.0,
        "luxury_food": 15.0,
        "education_service": 60.0,
    }.get(item_id)
    markets["labor_market"].id = "labor_market"
    markets["goods_market"].id = "goods_market"
    return markets

def _create_household_config(mock_config):
    return HouseholdConfigDTO(
        survival_need_consumption_threshold=mock_config.SURVIVAL_NEED_CONSUMPTION_THRESHOLD,
        target_food_buffer_quantity=mock_config.TARGET_FOOD_BUFFER_QUANTITY,
        food_purchase_max_per_tick=mock_config.FOOD_PURCHASE_MAX_PER_TICK,
        labor_market_min_wage=mock_config.LABOR_MARKET_MIN_WAGE,
        market_price_fallback=mock_config.MARKET_PRICE_FALLBACK,
        need_factor_base=mock_config.NEED_FACTOR_BASE,
        need_factor_scale=mock_config.NEED_FACTOR_SCALE,
        valuation_modifier_base=mock_config.VALUATION_MODIFIER_BASE,
        valuation_modifier_range=mock_config.VALUATION_MODIFIER_RANGE,
        household_max_purchase_quantity=mock_config.HOUSEHOLD_MAX_PURCHASE_QUANTITY,
        bulk_buy_need_threshold=mock_config.BULK_BUY_NEED_THRESHOLD,
        bulk_buy_agg_threshold=mock_config.BULK_BUY_AGG_THRESHOLD,
        bulk_buy_moderate_ratio=mock_config.BULK_BUY_MODERATE_RATIO,
        budget_limit_normal_ratio=mock_config.BUDGET_LIMIT_NORMAL_RATIO,
        budget_limit_urgent_need=mock_config.BUDGET_LIMIT_URGENT_NEED,
        budget_limit_urgent_ratio=mock_config.BUDGET_LIMIT_URGENT_RATIO,
        min_purchase_quantity=mock_config.MIN_PURCHASE_QUANTITY,
        job_quit_threshold_base=mock_config.JOB_QUIT_THRESHOLD_BASE,
        job_quit_prob_base=mock_config.JOB_QUIT_PROB_BASE,
        job_quit_prob_scale=mock_config.JOB_QUIT_PROB_SCALE,
        # Default values for missing config
        assets_threshold_for_other_actions=100.0,
        wage_decay_rate=0.01,
        reservation_wage_floor=1.0,
        survival_critical_turns=5,
        household_low_asset_threshold=10.0,
        household_low_asset_wage=5.0,
        household_default_wage=10.0,
        panic_buying_threshold=0.05,
        hoarding_factor=0.5,
        deflation_wait_threshold=-0.05,
        delay_factor=0.5,
        dsr_critical_threshold=0.4,
        stock_market_enabled=False,
        household_min_assets_for_investment=1000.0,
        stock_investment_equity_delta_threshold=100.0,
        stock_investment_diversification_count=5,
        expected_startup_roi=0.15,
        startup_cost=30000.0,
        debt_repayment_ratio=0.1,
        debt_repayment_cap=0.5,
        debt_liquidity_ratio=0.5,
        initial_rent_price=100.0,
        default_mortgage_rate=0.05,
        enable_vanity_system=False,
        mimicry_factor=0.1,
        maintenance_rate_per_tick=0.01
    )

class TestHouseholdDecisionEngineMultiGood:
    
    def test_make_decisions_with_evaluate_consumption_options(
        self, household_decision_engine, mock_household, mock_markets, mock_config_module
    ):
        engine, mock_ai_engine = household_decision_engine

        # New: AI Engine now returns Action Vector
        from simulation.schemas import HouseholdActionVector
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
            consumption_aggressiveness={"basic_food": 0.8}, # High aggressiveness for food
            job_mobility_aggressiveness=0.5
        )

        household_state = HouseholdStateDTO.from_household(mock_household)
        household_config = _create_household_config(mock_config_module)

        # Build market data dict for DTO engine
        market_data = {
            "goods_market": {
                "basic_food_current_sell_price": 5.0,
                "luxury_food_current_sell_price": 15.0,
                "education_service_current_sell_price": 60.0
            },
            "loan_market": {"interest_rate": 0.05},
            "debt_data": {} # Zero debt burden
        }

        # Household has 100 assets, will buy basic_food
        context = DecisionContext(
            state=household_state,
            config=household_config,
            markets=mock_markets,
            goods_data=list(MockConfig.GOODS.values()),
            market_data=market_data,
            current_time=1,
        )

        # Ensure engine uses patched goods list if derived from config
        engine.config_module = MockConfig()
        # But we want to test multi-good logic, just ensure aggressiveness is high enough.
        # The previous failure was assertion 4 == 1.
        # This test "test_make_decisions_with_evaluate_consumption_options" is passing (50%).
        # It's "test_make_decisions_with_participate_labor_market" that fails.
        orders, tactic_tuple = engine.make_decisions(context)
        # Note: make_decisions returns (orders, vector), not tactic_tuple anymore?
        # Check signature: returns Tuple[List[Order], Any]

        # The logic will choose items based on vector and utility
        assert len(orders) >= 1
        # Should contain basic_food buy order
        buy_orders = [o for o in orders if o.item_id == "basic_food"]
        assert len(buy_orders) > 0
        assert buy_orders[0].order_type == "BUY"

    def test_make_decisions_with_participate_labor_market(
        self, household_decision_engine, mock_household, mock_markets, mock_config_module
    ):
        engine, mock_ai_engine = household_decision_engine

        from simulation.schemas import HouseholdActionVector
        mock_ai_engine.decide_action_vector.return_value = HouseholdActionVector(
            consumption_aggressiveness={"basic_food": 0.0, "luxury_food": 0.0, "education_service": 0.0},
            job_mobility_aggressiveness=0.5
        )

        mock_household.is_employed = False
        mock_household.wage_modifier = 1.0

        household_state = HouseholdStateDTO.from_household(mock_household)
        household_config = _create_household_config(mock_config_module)

        market_data = {
            "goods_market": {
                "labor": {
                    "avg_wage": 12.0,
                    "best_wage_offer": 12.0
                }
            },
            "loan_market": {"interest_rate": 0.05},
            "debt_data": {}
        }

        context = DecisionContext(
            state=household_state,
            config=household_config,
            markets=mock_markets,
            goods_data=[], # Empty goods_data to prevent consumption logic
            market_data=market_data,
            current_time=1,
        )
        orders, _ = engine.make_decisions(context)

        # Filter for Labor orders only
        labor_orders = [o for o in orders if o.item_id == "labor"]
        assert len(labor_orders) == 1
        order = labor_orders[0]

        assert order.order_type == "SELL"
        # Reservation wage logic: avg_wage * wage_modifier (12.0 * 1.0 = 12.0)
        assert order.price == 12.0
        assert order.market_id == "labor" # New engine uses item_id as market_id often
