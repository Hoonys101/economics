
import pytest
from unittest.mock import MagicMock
from simulation.dtos import DecisionContext, FirmStateDTO
from modules.household.dtos import HouseholdStateDTO
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.decisions.standalone_rule_based_firm_engine import StandaloneRuleBasedFirmDecisionEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine

def test_decision_context_purity():
    """Verify DecisionContext does not expose raw agents."""
    assert not hasattr(DecisionContext, 'household')
    assert not hasattr(DecisionContext, 'firm')

    # Try to instantiate with deprecated fields (should fail type check or init if slots used,
    # but since it's a dataclass, it might accept kwargs if we are not careful,
    # but we removed fields so it should raise TypeError on init if passed)

    try:
        DecisionContext(
            markets={}, goods_data=[], market_data={}, current_time=0,
            state=MagicMock(), config=MagicMock(),
            household=MagicMock() # Should fail
        )
        pytest.fail("DecisionContext accepted 'household' argument.")
    except TypeError:
        pass

def test_standalone_firm_engine_uses_dto():
    """Verify StandaloneRuleBasedFirmDecisionEngine accepts FirmStateDTO."""
    config_mock = MagicMock()
    config_mock.OVERSTOCK_THRESHOLD = 1.2
    config_mock.UNDERSTOCK_THRESHOLD = 0.8
    config_mock.FIRM_MIN_PRODUCTION_TARGET = 10.0
    config_mock.FIRM_MAX_PRODUCTION_TARGET = 100.0
    config_mock.PRODUCTION_ADJUSTMENT_FACTOR = 0.1
    config_mock.FIRM_LABOR_REQUIREMENT_RATIO = 1.0
    config_mock.FIRM_MIN_EMPLOYEES = 1
    config_mock.LABOR_FIRING_BUFFER_RATIO = 1.1
    config_mock.GOODS = {"wood": {"production_cost": 10.0}}
    config_mock.MIN_SELL_PRICE = 1.0
    config_mock.MAX_SELL_PRICE = 100.0
    config_mock.MAX_SELL_QUANTITY = 100.0
    config_mock.BASE_WAGE = 10.0 # Float, not Mock
    # Fix getattr(mock) returning Mock instead of default
    config_mock.GENESIS_PRICE_ADJUSTMENT_MULTIPLIER = 1.0
    config_mock.PRICE_ADJUSTMENT_EXPONENT = 1.0
    config_mock.PRICE_ADJUSTMENT_FACTOR = 0.1

    engine = StandaloneRuleBasedFirmDecisionEngine(config_mock)

    firm_dto = FirmStateDTO(
        id=1, assets=1000.0, is_active=True, inventory={"wood": 50.0}, inventory_quality={}, input_inventory={},
        current_production=0.0, productivity_factor=1.0, production_target=50.0, capital_stock=10.0, base_quality=1.0,
        automation_level=0.0, specialization="wood", total_shares=100, treasury_shares=0, dividend_rate=0.0,
        is_publicly_traded=False, valuation=0.0, revenue_this_turn=0.0, expenses_this_tick=0.0, consecutive_loss_turns=0,
        altman_z_score=0.0, price_history={"wood": 10.0}, profit_history=[], brand_awareness=0.0, perceived_quality=0.0,
        marketing_budget=0.0, employees=[], employees_data={}, agent_data={}, system2_guidance={}, sentiment_index=0.5
    )

    context = MagicMock(spec=DecisionContext)
    context.state = firm_dto
    context.markets = {}
    context.goods_data = []
    context.market_data = {}
    context.current_time = 1

    orders, (tactic, agg) = engine.make_decisions(context)

    assert isinstance(orders, list)
    # Check that it didn't crash

def test_household_engine_uses_dto():
    """Verify AIDrivenHouseholdDecisionEngine accepts HouseholdStateDTO."""
    ai_engine_mock = MagicMock()
    ai_engine_mock.decide_action_vector.return_value = MagicMock(
        consumption_aggressiveness={},
        job_mobility_aggressiveness=0.0
    )

    config_mock = MagicMock()
    config_mock.GOODS = {"food": {}}
    config_mock.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 10
    config_mock.DSR_CRITICAL_THRESHOLD = 0.5
    config_mock.MARKET_PRICE_FALLBACK = 10.0 # Float
    config_mock.BULK_BUY_NEED_THRESHOLD = 100.0
    config_mock.BULK_BUY_AGG_THRESHOLD = 0.8
    config_mock.PANIC_BUYING_THRESHOLD = 0.05
    config_mock.DEFLATION_WAIT_THRESHOLD = -0.05
    config_mock.DELAY_FACTOR = 0.5
    config_mock.HOARDING_FACTOR = 0.5
    config_mock.BUDGET_LIMIT_URGENT_NEED = 50.0
    config_mock.BUDGET_LIMIT_URGENT_RATIO = 0.8
    config_mock.BUDGET_LIMIT_NORMAL_RATIO = 0.5

    engine = AIDrivenHouseholdDecisionEngine(ai_engine_mock, config_mock)

    household_dto = MagicMock(spec=HouseholdStateDTO) # Using Mock of DTO for simplicity
    household_dto.id = 1
    household_dto.agent_data = {}
    household_dto.inventory = {"basic_food": 10.0}
    household_dto.needs = {"hunger": 0.0}
    household_dto.assets = 1000.0
    household_dto.current_wage = 10.0
    household_dto.expected_inflation = {}
    household_dto.personality = "BALANCED" # Enum mock
    household_dto.preference_asset = 1.0
    household_dto.preference_social = 1.0
    household_dto.preference_growth = 1.0
    household_dto.durable_assets = []
    household_dto.is_employed = True
    household_dto.portfolio_holdings = {}
    household_dto.is_homeless = False
    household_dto.residing_property_id = 1
    household_dto.owned_properties = [1]
    household_dto.conformity = 0.5
    household_dto.optimism = 0.5
    household_dto.ambition = 0.5

    config_dto = MagicMock()
    config_dto.market_price_fallback = 10.0
    config_dto.min_purchase_quantity = 1.0
    config_dto.household_max_purchase_quantity = 10.0
    config_dto.bulk_buy_need_threshold = 100.0
    config_dto.bulk_buy_agg_threshold = 0.8
    config_dto.bulk_buy_moderate_ratio = 0.5
    config_dto.panic_buying_threshold = 0.05
    config_dto.hoarding_factor = 0.5
    config_dto.deflation_wait_threshold = -0.05
    config_dto.delay_factor = 0.5
    config_dto.dsr_critical_threshold = 0.5
    config_dto.budget_limit_normal_ratio = 0.5
    config_dto.budget_limit_urgent_need = 50.0
    config_dto.budget_limit_urgent_ratio = 0.8

    # These are used via self.config_module (config_mock)
    config_mock.BUDGET_LIMIT_NORMAL_RATIO = 0.5
    config_mock.BUDGET_LIMIT_URGENT_NEED = 50.0
    config_mock.BUDGET_LIMIT_URGENT_RATIO = 0.8
    config_mock.NEED_FACTOR_BASE = 1.0
    config_mock.NEED_FACTOR_SCALE = 100.0
    config_mock.VALUATION_MODIFIER_BASE = 1.0
    config_mock.VALUATION_MODIFIER_RANGE = 0.2
    config_mock.BULK_BUY_NEED_THRESHOLD = 100.0
    config_mock.BULK_BUY_AGG_THRESHOLD = 0.8
    config_mock.BULK_BUY_MODERATE_RATIO = 0.5
    config_mock.MIN_PURCHASE_QUANTITY = 1.0
    config_mock.LABOR_MARKET_MIN_WAGE = 10.0
    config_mock.JOB_QUIT_THRESHOLD_BASE = 0.5
    config_mock.JOB_QUIT_PROB_BASE = 0.1
    config_mock.JOB_QUIT_PROB_SCALE = 0.1
    config_mock.STOCK_MARKET_ENABLED = True
    config_mock.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 500.0
    config_mock.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 2.0
    config_mock.STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD = 100.0
    config_mock.STOCK_INVESTMENT_DIVERSIFICATION_COUNT = 5

    context = MagicMock(spec=DecisionContext)
    context.state = household_dto
    context.config = config_dto

    context.markets = {}
    context.market_data = {"loan_market": {"interest_rate": 0.05}}
    context.current_time = 1

    orders, vector = engine._make_decisions_internal(context)

    assert isinstance(orders, list)
