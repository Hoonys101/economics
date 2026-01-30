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
    from simulation.dtos import DecisionContext, FirmStateDTO
    from tests.utils.factories import create_firm_config_dto

    mock_firm.inventory["food"] = 200
    mock_firm.production_target = 100
    firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = (
        (Tactic.ADJUST_PRICE, 1.0)
    )

    state_dto = Mock(spec=FirmStateDTO)
    state_dto.inventory = mock_firm.inventory
    state_dto.production_target = mock_firm.production_target
    state_dto.specialization = mock_firm.specialization
    state_dto.id = mock_firm.id
    state_dto.last_prices = mock_firm.last_prices
    state_dto.marketing_budget = 0.0 # Required field
    state_dto.base_quality = 1.0
    state_dto.inventory_quality = {mock_firm.specialization: 1.0}

    context = DecisionContext(
        state=state_dto,
        config=create_firm_config_dto(),
        market_data={},
        goods_data=[],
        current_time=1,
    )
    orders, _ = firm_decision_engine_instance.make_decisions(context)

    assert len(orders) == 1
    order = orders[0]
    assert order.item_id == "food"
    assert order.order_type == "SELL"
    assert order.price < 10  # Price should be adjusted downwards due to overstock
