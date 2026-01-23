import pytest
from simulation.firms import Firm
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
import config
from unittest.mock import Mock
from simulation.ai.enums import Tactic, Aggressiveness
from simulation.dtos import DecisionContext


# Mock config values for testing
@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
    monkeypatch.setattr(
        config, "FIRM_SPECIALIZATIONS", {0: "basic_food", 1: "luxury_food"}
    )
    monkeypatch.setattr(config, "FIRM_PRODUCTIVITY_FACTOR", 1.0)

    monkeypatch.setattr(config, "BASE_WAGE", 5.0)
    # Add thresholds for the fix
    monkeypatch.setattr(config, "UNDERSTOCK_THRESHOLD", 0.8)
    monkeypatch.setattr(config, "OVERSTOCK_THRESHOLD", 1.2)


@pytest.fixture
def sample_firm():
    mock_ai_engine = Mock()  # Create a mock AI engine
    firm = Firm(
        id=1,
        initial_capital=1000.0,
        initial_liquidity_need=10.0,
        specialization="basic_food",
        productivity_factor=1.0,
        decision_engine=AIDrivenFirmDecisionEngine(
            ai_engine=mock_ai_engine, config_module=config
        ),  # Pass the mock AI engine
        value_orientation="test_firm_vo",
        config_module=config,  # Pass the config module
        logger=None,  # Pass None for logger in tests or mock it
    )
    firm.production_target = 100.0  # Initialize production_target
    firm.inventory[firm.specialization] = 50.0  # Initial inventory for specialized good
    firm.last_prices = {firm.specialization: 10.0}  # Initialize last_prices
    return firm


@pytest.fixture
def sample_market_data():
    return {
        "time": 0,
        "goods_market": {"food_current_sell_price": 10.0},
        "labor_market": {"avg_wage": 5.0},
        "loan_market": {"interest_rate": 0.05},
        "all_households": [],
        "goods_data": [
            {"id": "food", "name": "Food", "utility_per_need": {"survival_need": 1.0}}
        ],
    }


def test_firm_production_decision_with_employees(sample_firm, sample_market_data):
    # Simulate having employees
    class MockHousehold:
        def __init__(self, id, labor_skill):
            self.id = id
            self.labor_skill = labor_skill

        # Add a mock for is_active if needed by the firm's logic
        @property
        def is_active(self):
            return True

    employee1 = MockHousehold(id=101, labor_skill=1.0)
    employee2 = MockHousehold(id=102, labor_skill=0.8)
    sample_firm.employees = [employee1, employee2]
    sample_firm.decision_engine.ai_engine.decide_action_vector.return_value = (
        Tactic.ADJUST_WAGES,
        Aggressiveness.NORMAL,
    )

    # Call make_decisions
    context = DecisionContext(
        firm=sample_firm,
        markets={},
        goods_data=[],
        market_data=sample_market_data,
        current_time=0,
        government=None,
    )
    orders, _ = sample_firm.decision_engine.make_decisions(context)

    # Test if a BUY order for 'labor' is generated if it needs more production
    buy_labor_orders = [
        order
        for order in orders
        if order.order_type == "BUY" and order.market_id == "labor_market"
    ]
    assert len(buy_labor_orders) > 0, "Expected firm to generate BUY orders for labor"
    assert buy_labor_orders[0].item_id == "labor"
    assert (
        buy_labor_orders[0].quantity == 1
    )  # Assuming it tries to hire one unit of labor

    # Test if no SELL order for 'food' is generated if inventory is below target
    sell_orders = [
        order
        for order in orders
        if order.order_type == "SELL" and order.market_id == "goods_market"
    ]
    assert len(sell_orders) == 0, (
        "Expected no SELL orders when inventory is below target"
    )


def test_firm_no_production_if_target_met(sample_firm, sample_market_data):
    # Set inventory to meet or exceed target
    sample_firm.inventory[sample_firm.specialization] = 150.0  # Above target of 100
    sample_firm.employees = []  # Ensure no employees are present to focus on inventory decision
    sample_firm.decision_engine.ai_engine.decide_action_vector.return_value = (
        Tactic.ADJUST_PRICE,
        Aggressiveness.NORMAL,
    )

    context = DecisionContext(
        firm=sample_firm,
        markets={},
        goods_data=[],
        market_data=sample_market_data,
        current_time=0,
        government=None,
    )
    orders, _ = sample_firm.decision_engine.make_decisions(context)

    # Expect SELL orders to reduce inventory, but not necessarily BUY labor orders
    sell_orders = [
        order
        for order in orders
        if order.order_type == "SELL" and order.market_id == "goods_market"
    ]
    assert len(sell_orders) > 0, (
        "Expected firm to generate SELL orders to reduce excess inventory"
    )
    assert sell_orders[0].item_id == sample_firm.specialization
    assert sell_orders[0].quantity > 0

    # If target is met/exceeded, it should not try to hire more for production
    buy_labor_orders = [
        order
        for order in orders
        if order.order_type == "BUY" and order.market_id == "labor_market"
    ]
    assert len(buy_labor_orders) == 0, (
        "Expected no labor BUY orders if production target is met/exceeded"
    )


def test_firm_hiring_decision_no_inventory(sample_firm, sample_market_data):
    # Set inventory to 0, so it needs to produce
    sample_firm.inventory[sample_firm.specialization] = 0.0
    sample_firm.employees = []  # No employees
    sample_firm.decision_engine.ai_engine.decide_action_vector.return_value = (
        Tactic.ADJUST_WAGES,
        Aggressiveness.NORMAL,
    )

    context = DecisionContext(
        firm=sample_firm,
        markets={},
        goods_data=[],
        market_data=sample_market_data,
        current_time=0,
        government=None,
    )
    orders, _ = sample_firm.decision_engine.make_decisions(context)

    # Expect BUY labor orders to meet production target
    buy_labor_orders = [
        order
        for order in orders
        if order.order_type == "BUY" and order.market_id == "labor_market"
    ]
    assert len(buy_labor_orders) > 0, (
        "Expected firm to generate BUY orders for labor when inventory is low"
    )
    assert buy_labor_orders[0].item_id == "labor"
    assert (
        buy_labor_orders[0].quantity == 1
    )  # Assuming it tries to hire one unit of labor

    sell_orders = [
        order
        for order in orders
        if order.order_type == "SELL" and order.market_id == "goods_market"
    ]
    assert len(sell_orders) == 0, "Expected no SELL orders when inventory is 0"
