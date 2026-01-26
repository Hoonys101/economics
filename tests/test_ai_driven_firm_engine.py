import pytest
from unittest.mock import Mock

from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.ai.enums import Tactic


@pytest.fixture
def mock_ai_engine():
    return Mock()


@pytest.fixture
def mock_config():
    config = Mock()
    config.OVERSTOCK_THRESHOLD = 1.5
    config.UNDERSTOCK_THRESHOLD = 0.5
    config.PRODUCTION_ADJUSTMENT_FACTOR = 0.1
    config.FIRM_MIN_PRODUCTION_TARGET = 10
    config.FIRM_MAX_PRODUCTION_TARGET = 1000
    config.FIRM_MIN_EMPLOYEES = 1
    config.FIRM_MAX_EMPLOYEES = 100
    config.BASE_WAGE = 100
    config.WAGE_PROFIT_SENSITIVITY = 0.1
    config.MAX_WAGE_PREMIUM = 0.5
    config.GOODS_MARKET_SELL_PRICE = 10
    config.PRICE_ADJUSTMENT_EXPONENT = 0.5
    config.PRICE_ADJUSTMENT_FACTOR = 0.1
    config.MIN_SELL_PRICE = 1
    config.MAX_SELL_PRICE = 1000
    config.MAX_SELL_QUANTITY = 100

    # System 2 Config
    config.SYSTEM2_TICKS_PER_CALC = 10
    config.SYSTEM2_HORIZON = 50
    config.SYSTEM2_DISCOUNT_RATE = 0.95
    config.FIRM_MAINTENANCE_FEE = 10.0
    config.AUTOMATION_COST_PER_PCT = 1000.0
    config.AUTOMATION_LABOR_REDUCTION = 0.5

    return config


@pytest.fixture
def firm_decision_engine_instance(mock_ai_engine, mock_config):
    return AIDrivenFirmDecisionEngine(mock_ai_engine, mock_config)


@pytest.fixture
def mock_firm(mock_config):
    firm = Mock()
    firm.id = 1
    firm.specialization = "food"
    firm.inventory = {"food": 100}
    firm.production_target = 100
    firm.last_prices = {"food": 10}
    firm.employees = []
    firm.profit_history = []
    firm.productivity_factor = 1.0
    firm.age = 25 # Add age for solvency checks
    firm.finance = Mock() # Mock the finance department
    return firm


def test_adjust_price_tactic(firm_decision_engine_instance, mock_firm):
    """Test that the ADJUST_PRICE tactic correctly adjusts the price."""
    from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
    from simulation.schemas import FirmActionVector

    mock_firm.inventory["food"] = 200
    mock_firm.production_target = 100

    # Use FirmActionVector instead of tuple
    firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
        sales_aggressiveness=0.8, # High aggressiveness -> Lower price
        hiring_aggressiveness=0.5,
        rd_aggressiveness=0.5,
        capital_aggressiveness=0.5,
        dividend_aggressiveness=0.5,
        debt_aggressiveness=0.5
    )

    # Convert Mock to DTO
    # Note: mock_firm needs to be populated enough for DTO conversion or manually created
    # Since DTO conversion is complex with Mocks, we'll manually create the DTO

    firm_state = FirmStateDTO(
        id=mock_firm.id,
        assets=1000.0,
        is_active=True,
        inventory=mock_firm.inventory,
        inventory_quality={"food": 1.0},
        input_inventory={},
        current_production=0.0,
        productivity_factor=mock_firm.productivity_factor,
        production_target=mock_firm.production_target,
        capital_stock=100.0,
        base_quality=1.0,
        automation_level=0.0,
        specialization=mock_firm.specialization,
        total_shares=100.0,
        treasury_shares=0.0,
        dividend_rate=0.0,
        is_publicly_traded=False,
        valuation=1000.0,
        revenue_this_turn=0.0,
        expenses_this_tick=0.0,
        consecutive_loss_turns=0,
        altman_z_score=3.0,
        price_history=mock_firm.last_prices,
        profit_history=[],
        brand_awareness=0.0,
        perceived_quality=1.0,
        marketing_budget=0.0,
        employees=[],
        employees_data={},
        agent_data={},
        system2_guidance={},
        sentiment_index=0.5,
        last_sales_volume=100.0
    )

    # Mock Config DTO
    firm_config = FirmConfigDTO(
        firm_min_production_target=10.0,
        firm_max_production_target=1000.0,
        startup_cost=30000.0,
        seo_trigger_ratio=0.5,
        seo_max_sell_ratio=0.1,
        automation_cost_per_pct=1000.0,
        firm_safety_margin=2000.0,
        automation_tax_rate=0.05,
        altman_z_score_threshold=1.8,
        dividend_suspension_loss_ticks=3,
        dividend_rate_min=0.1,
        dividend_rate_max=0.5,
        labor_alpha=0.7,
        automation_labor_reduction=0.5,
        severance_pay_weeks=4,
        labor_market_min_wage=10.0,
        overstock_threshold=1.5,
        understock_threshold=0.5,
        production_adjustment_factor=0.1,
        max_sell_quantity=100.0,
        invisible_hand_sensitivity=0.1,
        capital_to_output_ratio=2.0
    )

    context = DecisionContext(
        state=firm_state,
        config=firm_config,
        markets={"food": Mock()},
        goods_data=[],
        market_data={},
        current_time=1,
        government=None,
    )
    orders, _ = firm_decision_engine_instance.make_decisions(context)

    # Check for SELL order
    sell_orders = [o for o in orders if o.order_type == "SELL"]
    assert len(sell_orders) > 0
    order = sell_orders[0]
    assert order.item_id == "food"
    # Price check: high sales aggressiveness (0.8) should lower price below market (10)
    # Price logic: target = market * (1 + (0.5 - 0.8)*0.4) = 10 * (1 - 0.12) = 8.8
    # With decay: 8.8 * decay.
    assert order.price < 10
