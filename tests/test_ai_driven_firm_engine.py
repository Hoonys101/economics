import pytest
from unittest.mock import Mock, MagicMock

from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.ai.enums import Tactic, Personality
from simulation.schemas import FirmActionVector
from simulation.dtos.firm_state_dto import FirmStateDTO


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
    # Additional for CorporateManager
    config.CAPITAL_TO_OUTPUT_RATIO = 2.0
    config.DIVIDEND_RATE_MIN = 0.1
    config.DIVIDEND_RATE_MAX = 0.5
    config.LABOR_MARKET_MIN_WAGE = 5.0
    config.GOODS = {"food": {"production_cost": 10.0, "inputs": {}}}
    config.AUTOMATION_COST_PER_PCT = 1000.0
    config.FIRM_SAFETY_MARGIN = 2000.0
    config.AUTOMATION_TAX_RATE = 0.05
    config.SEVERANCE_PAY_WEEKS = 4
    config.STARTUP_COST = 30000.0
    config.SEO_TRIGGER_RATIO = 0.5
    config.SEO_MAX_SELL_RATIO = 0.10
    config.LABOR_ALPHA = 0.7
    config.AUTOMATION_LABOR_REDUCTION = 0.5
    config.DIVIDEND_SUSPENSION_LOSS_TICKS = 3
    config.SYSTEM2_HORIZON = 10
    config.SYSTEM2_DISCOUNT_RATE = 0.98
    config.SYSTEM2_TICKS_PER_CALC = 10
    config.FIRM_MAINTENANCE_FEE = 50.0

    return config


@pytest.fixture
def firm_decision_engine_instance(mock_ai_engine, mock_config):
    return AIDrivenFirmDecisionEngine(mock_ai_engine, mock_config)


@pytest.fixture
def mock_firm_state(mock_config):
    return FirmStateDTO(
        id=1,
        assets=10000.0,
        is_active=True,
        specialization="food",
        inventory={"food": 200}, # Overstocked
        production_target=100.0,
        last_prices={"food": 10.0},
        productivity_factor=1.0,
        employee_count=0,
        employees=[],
        employee_wages={},
        profit_history=[],
        inventory_quality={"food": 1.0},
        input_inventory={},
        last_revenue=0.0,
        last_sales_volume=1.0,
        revenue_this_turn=0.0,
        expenses_this_tick=0.0,
        consecutive_loss_turns=0,
        total_shares=100.0,
        treasury_shares=0.0,
        dividend_rate=0.1,
        capital_stock=100.0,
        total_debt=0.0,
        personality=Personality.BALANCED,
        base_quality=1.0,
        brand_awareness=0.0,
        perceived_quality=0.0,
        automation_level=0.0,
        needs={},
        current_production=0.0
    )


def test_adjust_price_tactic(firm_decision_engine_instance, mock_firm_state):
    """Test that the ADJUST_PRICE tactic correctly adjusts the price."""
    from simulation.dtos import DecisionContext

    # High Sales Aggressiveness to reduce price
    firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
        sales_aggressiveness=1.0, # Causes price cut
        hiring_aggressiveness=0.0,
        rd_aggressiveness=0.0,
        capital_aggressiveness=0.0,
        dividend_aggressiveness=0.0,
        debt_aggressiveness=0.0
    )

    context = DecisionContext(
        firm_state=mock_firm_state,
        markets={"food": MagicMock()}, # Mock market to allow order
        goods_data=[],
        market_data={},
        current_time=1,
        government=None,
    )
    orders, _ = firm_decision_engine_instance.make_decisions(context)

    # Filter for SELL order
    sell_order = next((o for o in orders if o.order_type == "SELL" and o.item_id == "food"), None)

    assert sell_order is not None
    assert sell_order.price < 10.0 # 10.0 * (1.0 + (0.5 - 1.0)*0.4) = 10 * 0.8 = 8.0
