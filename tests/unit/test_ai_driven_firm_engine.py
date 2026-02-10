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
    from simulation.schemas import FirmActionVector

    mock_firm.inventory["food"] = 200
    mock_firm.production_target = 100
    firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
        sales_aggressiveness=1.0, # High aggressiveness -> Lower price
        hiring_aggressiveness=0.5,
        rd_aggressiveness=0.5,
        capital_aggressiveness=0.5,
        dividend_aggressiveness=0.5,
        debt_aggressiveness=0.5
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
    state_dto.agent_data = {"productivity_factor": 1.0}

    state_dto.finance = Mock()
    state_dto.finance.revenue_this_turn = 0.0
    state_dto.finance.balance = 1000.0
    state_dto.finance.altman_z_score = 3.0
    state_dto.finance.consecutive_loss_turns = 0
    state_dto.finance.is_publicly_traded = True
    state_dto.finance.treasury_shares = 0
    state_dto.finance.total_shares = 100

    state_dto.hr = Mock()
    state_dto.hr.employees_data = {}
    state_dto.hr.employees = []

    state_dto.production = Mock()
    state_dto.production.automation_level = 0.0
    state_dto.production.inventory = mock_firm.inventory
    state_dto.production.production_target = 100.0
    state_dto.production.specialization = "food"
    state_dto.production.capital_stock = 100.0
    state_dto.production.productivity_factor = 1.0

    state_dto.sales = Mock()
    state_dto.sales.price_history = mock_firm.last_prices
    state_dto.sales.marketing_budget = 0.0

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
