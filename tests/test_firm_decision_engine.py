import pytest
from simulation.firms import Firm
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
import config
from unittest.mock import Mock, MagicMock
from simulation.ai.enums import Tactic, Aggressiveness
from simulation.dtos import DecisionContext
from simulation.schemas import FirmActionVector


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

    # Mock additional config for CorporateManager
    monkeypatch.setattr(config, "CAPITAL_TO_OUTPUT_RATIO", 2.0, raising=False)
    monkeypatch.setattr(config, "DIVIDEND_RATE_MIN", 0.1, raising=False)
    monkeypatch.setattr(config, "DIVIDEND_RATE_MAX", 0.5, raising=False)
    monkeypatch.setattr(config, "MAX_SELL_QUANTITY", 100, raising=False)
    monkeypatch.setattr(config, "LABOR_MARKET_MIN_WAGE", 5.0, raising=False)
    monkeypatch.setattr(config, "GOODS", {"basic_food": {"production_cost": 5.0, "inputs": {}}}, raising=False)
    monkeypatch.setattr(config, "AUTOMATION_COST_PER_PCT", 1000.0, raising=False)
    monkeypatch.setattr(config, "FIRM_SAFETY_MARGIN", 2000.0, raising=False)
    monkeypatch.setattr(config, "AUTOMATION_TAX_RATE", 0.05, raising=False)
    monkeypatch.setattr(config, "SEVERANCE_PAY_WEEKS", 4, raising=False)
    monkeypatch.setattr(config, "STARTUP_COST", 30000.0, raising=False)
    monkeypatch.setattr(config, "SEO_TRIGGER_RATIO", 0.5, raising=False)
    monkeypatch.setattr(config, "SEO_MAX_SELL_RATIO", 0.10, raising=False)
    monkeypatch.setattr(config, "LABOR_ALPHA", 0.7, raising=False)
    monkeypatch.setattr(config, "AUTOMATION_LABOR_REDUCTION", 0.5, raising=False)
    monkeypatch.setattr(config, "DIVIDEND_SUSPENSION_LOSS_TICKS", 3, raising=False)


@pytest.fixture
def sample_firm():
    mock_ai_engine = Mock()  # Create a mock AI engine
    firm = Firm(
        id=1,
        initial_capital=10000.0, # Increased capital for safety margin
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
    # Initial setup for HR
    firm.hr = MagicMock()
    firm.hr.employees = []
    firm.hr.employee_wages = {}
    return firm


@pytest.fixture
def sample_market_data():
    return {
        "time": 0,
        "goods_market": {"basic_food_avg_traded_price": 10.0, "basic_food_current_sell_price": 10.0}, # Fixed key
        "labor_market": {"avg_wage": 5.0},
        "loan_market": {"interest_rate": 0.05},
        "all_households": [],
        "goods_data": [
            {"id": "basic_food", "name": "Basic Food", "utility_per_need": {"survival_need": 1.0}}
        ],
    }


def test_firm_production_decision_with_employees(sample_firm, sample_market_data):
    # Simulate having employees
    class MockHousehold:
        def __init__(self, id, labor_skill):
            self.id = id
            self.labor_skill = labor_skill

        @property
        def is_active(self):
            return True

    employee1 = MockHousehold(id=101, labor_skill=1.0)
    employee2 = MockHousehold(id=102, labor_skill=0.8)
    sample_firm.hr.employees = [employee1, employee2]
    sample_firm.hr.employee_wages = {101: 5.0, 102: 5.0}

    # Mock AI to return a Vector that causes hiring/production adjustments
    # If inventory < target, CorporateManager checks inventory gap.
    # Gap = 100 - 50 = 50.
    # Need labor.
    # Current employees = 2.
    # Productivity = 1.0. Needed labor = 50 / 1.0 = 50.
    # So we need to hire 48 more.
    # Hiring aggressiveness needs to be high enough? No, logic just calculates gap.
    # But hiring_aggressiveness affects wage offer.
    # We want BUY orders.

    sample_firm.decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
        hiring_aggressiveness=0.5,
        sales_aggressiveness=0.5,
        rd_aggressiveness=0.0,
        capital_aggressiveness=0.0,
        dividend_aggressiveness=0.0,
        debt_aggressiveness=0.0
    )

    # Call make_decisions
    firm_state_dto = sample_firm.create_state_dto()

    context = DecisionContext(
        firm_state=firm_state_dto,
        markets={sample_firm.specialization: Mock()},
        goods_data=[],
        market_data=sample_market_data,
        current_time=0,
        government=None,
    )
    orders, _ = sample_firm.decision_engine.make_decisions(context)

    # Test if a BUY order for 'labor' is generated
    buy_labor_orders = [
        order
        for order in orders
        if order.order_type == "BUY" and order.item_id == "labor" # CorporateManager uses "labor" as item_id
    ]
    assert len(buy_labor_orders) > 0, "Expected firm to generate BUY orders for labor"
    assert buy_labor_orders[0].item_id == "labor"
    assert buy_labor_orders[0].quantity == 1


def test_firm_no_production_if_target_met(sample_firm, sample_market_data):
    # Set inventory to meet or exceed target
    sample_firm.inventory[sample_firm.specialization] = 150.0  # Above target of 100
    sample_firm.hr.employees = []

    # AI decides to sell
    sample_firm.decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
        sales_aggressiveness=0.5,
        hiring_aggressiveness=0.0,
        rd_aggressiveness=0.0,
        capital_aggressiveness=0.0,
        dividend_aggressiveness=0.0,
        debt_aggressiveness=0.0
    )

    firm_state_dto = sample_firm.create_state_dto()

    context = DecisionContext(
        firm_state=firm_state_dto,
        markets={sample_firm.specialization: Mock()},
        goods_data=[],
        market_data=sample_market_data,
        current_time=0,
        government=None,
    )
    orders, _ = sample_firm.decision_engine.make_decisions(context)

    # Expect SELL orders
    # CorporateManager _manage_pricing returns SELL orders if inventory > 0
    sell_orders = [
        order
        for order in orders
        if order.order_type == "SELL" and order.market_id == sample_firm.specialization
    ]
    # Note: CorporateManager emits SELL order with market_id=item_id (basic_food)

    assert len(sell_orders) > 0, (
        "Expected firm to generate SELL orders to reduce excess inventory"
    )
    assert sell_orders[0].item_id == sample_firm.specialization
    assert sell_orders[0].quantity > 0

    # No hiring
    buy_labor_orders = [
        order
        for order in orders
        if order.order_type == "BUY" and order.item_id == "labor"
    ]
    assert len(buy_labor_orders) == 0


def test_firm_hiring_decision_no_inventory(sample_firm, sample_market_data):
    # Set inventory to 0, so it needs to produce
    sample_firm.inventory[sample_firm.specialization] = 0.0
    sample_firm.hr.employees = []

    sample_firm.decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
        hiring_aggressiveness=0.5,
        sales_aggressiveness=0.5,
        rd_aggressiveness=0.0,
        capital_aggressiveness=0.0,
        dividend_aggressiveness=0.0,
        debt_aggressiveness=0.0
    )

    firm_state_dto = sample_firm.create_state_dto()

    context = DecisionContext(
        firm_state=firm_state_dto,
        markets={},
        goods_data=[],
        market_data=sample_market_data,
        current_time=0,
        government=None,
    )
    orders, _ = sample_firm.decision_engine.make_decisions(context)

    buy_labor_orders = [
        order
        for order in orders
        if order.order_type == "BUY" and order.item_id == "labor"
    ]
    assert len(buy_labor_orders) > 0
    assert buy_labor_orders[0].item_id == "labor"
    assert buy_labor_orders[0].quantity == 1
