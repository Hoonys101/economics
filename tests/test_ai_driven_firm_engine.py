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
    return firm


def test_adjust_price_tactic(firm_decision_engine_instance, mock_firm):
    """Test that the ADJUST_PRICE tactic correctly adjusts the price."""
    mock_firm.inventory["food"] = 200
    mock_firm.production_target = 100
    firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = (
        Tactic.ADJUST_PRICE
    )

    orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)

    assert len(orders) == 1
    order = orders[0]
    assert order.item_id == "food"
    assert order.order_type == "SELL"
    assert order.price < 10  # Price should be adjusted downwards due to overstock
