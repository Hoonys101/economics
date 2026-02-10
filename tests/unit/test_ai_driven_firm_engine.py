import pytest
from unittest.mock import Mock

from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.ai.enums import Tactic
from tests.unit.mocks.mock_factory import MockFactory


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
    config.SYSTEM2_TICKS_PER_CALC = 10
    config.SYSTEM2_HORIZON = 10
    config.SYSTEM2_DISCOUNT_RATE = 0.98
    config.FIRM_MAINTENANCE_FEE = 10.0
    config.AUTOMATION_COST_PER_PCT = 1000.0
    config.AUTOMATION_LABOR_REDUCTION = 0.5
    return config


@pytest.fixture
def firm_decision_engine_instance(mock_ai_engine, mock_config):
    return AIDrivenFirmDecisionEngine(mock_ai_engine, mock_config)


@pytest.fixture
def mock_firm(mock_config):
    return MockFactory.create_mock_firm(
        id=1,
        specialization="food",
        inventory={"food": 100},
        production_target=100,
        price_history={"food": 10},
        productivity_factor=1.0,
        config=mock_config
    )


def test_adjust_price_tactic(firm_decision_engine_instance, mock_firm):
    """Test that the ADJUST_PRICE tactic correctly adjusts the price."""
    from simulation.dtos import DecisionContext
    from tests.utils.factories import create_firm_config_dto
    from simulation.schemas import FirmActionVector

    # Update state via MockFactory for specific test case conditions
    state_dto = MockFactory.create_firm_state_dto(
        id=1,
        specialization="food",
        inventory={"food": 200}, # Overstock
        production_target=100,
        price_history={"food": 10},
        inventory_quality={"food": 1.0},
        agent_data={"productivity_factor": 1.0},
        balance=1000.0,
        altman_z_score=3.0,
        consecutive_loss_turns=0,
        is_publicly_traded=True,
        total_shares=100,
        treasury_shares=0
    )

    mock_firm.get_state_dto.return_value = state_dto

    firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
        sales_aggressiveness=1.0, # High aggressiveness -> Lower price
        hiring_aggressiveness=0.5,
        rd_aggressiveness=0.5,
        capital_aggressiveness=0.5,
        dividend_aggressiveness=0.5,
        debt_aggressiveness=0.5
    )

    market_signals = {
        "food": Mock(
            last_trade_tick=1,
            best_bid=10.0,
            best_ask=10.0
        )
    }
    market_snapshot = Mock()
    market_snapshot.market_signals = market_signals

    context = DecisionContext(
        state=state_dto,
        config=create_firm_config_dto(),
        market_data={},
        goods_data=[],
        current_time=1,
        market_snapshot=market_snapshot
    )
    output = firm_decision_engine_instance.make_decisions(context)
    orders = output.orders

    food_orders = [o for o in orders if o.item_id == "food" and o.side == "SELL"]
    assert len(food_orders) > 0
    order = food_orders[0]
    # Check price or price_limit
    price = getattr(order, 'price_limit', order.price)
    assert price < 10  # Price should be adjusted downwards due to overstock
