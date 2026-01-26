import pytest
from simulation.firms import Firm
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
import config
from unittest.mock import Mock
from simulation.ai.enums import Tactic, Aggressiveness
from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
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

def _create_firm_config():
    return FirmConfigDTO(
        firm_min_production_target=10.0,
        firm_max_production_target=500.0,
        startup_cost=30000.0,
        seo_trigger_ratio=0.5,
        seo_max_sell_ratio=0.1,
        automation_cost_per_pct=1000.0,
        firm_safety_margin=2000.0,
        automation_tax_rate=0.05,
        altman_z_score_threshold=1.81,
        dividend_suspension_loss_ticks=3,
        dividend_rate_min=0.1,
        dividend_rate_max=0.5,
        labor_alpha=0.7,
        automation_labor_reduction=0.5,
        severance_pay_weeks=4,
        labor_market_min_wage=5.0,
        overstock_threshold=1.2,
        understock_threshold=0.8,
        production_adjustment_factor=0.1,
        max_sell_quantity=50.0,
        invisible_hand_sensitivity=0.1,
        capital_to_output_ratio=2.0
    )

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

    # Update HR component for DTO creation
    mock_hr = Mock()
    mock_hr.employees = [employee1, employee2]
    mock_hr.employee_wages = {101: 5.0, 102: 5.0}
    sample_firm.hr = mock_hr

    # Ensure firm has enough assets
    sample_firm._assets = 100000.0 # Above safety margin
    sample_firm.production_target = 200.0 # High enough to trigger hiring
    sample_firm.inventory = {sample_firm.specialization: 0.0} # Needs production
    sample_firm.capital_stock = 1000.0 # Increase capital to ensure high labor productivity isn't bottleneck? No, wait.
    # Production Function: Gap / (TFP * K^beta) ^ (1/alpha)
    # If Gap=200, K=100. Beta=0.3. Alpha=0.7.
    # TFP=1.0.
    # Term = 200 / (1 * 100^0.3) = 200 / 3.98 = 50.
    # Needed = 50 ^ (1/0.7) = 50^1.42 = 266.
    # Current Emp = 2.
    # To Hire = 264.
    # So Logic should produce orders.
    # Check if automation_level is 0.0
    sample_firm.automation_level = 0.0

    sample_firm.decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
        hiring_aggressiveness=0.8,
        sales_aggressiveness=0.5,
        rd_aggressiveness=0.5,
        capital_aggressiveness=0.5,
        dividend_aggressiveness=0.5,
        debt_aggressiveness=0.5
    )

    # Call make_decisions
    firm_state = FirmStateDTO.from_firm(sample_firm)
    firm_config = _create_firm_config()

    context = DecisionContext(
        state=firm_state,
        config=firm_config,
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
        if order.order_type == "BUY" and order.market_id == "labor"
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
        if order.order_type == "SELL" and order.market_id == sample_firm.specialization
    ]
    assert len(sell_orders) == 0, (
        "Expected no SELL orders when inventory is below target"
    )


def test_firm_no_production_if_target_met(sample_firm, sample_market_data):
    # Set inventory to meet or exceed target
    sample_firm.inventory[sample_firm.specialization] = 150.0  # Above target of 100

    # Ensure firm has at least 1 employee to satisfy skeleton crew logic
    class MockHousehold:
        def __init__(self, id, labor_skill):
            self.id = id
            self.labor_skill = labor_skill

    employee1 = MockHousehold(id=101, labor_skill=1.0)
    sample_firm.employees = [employee1]

    # Update HR component
    mock_hr = Mock()
    mock_hr.employees = [employee1]
    mock_hr.employee_wages = {101: 5.0}
    sample_firm.hr = mock_hr

    # Ensure firm has enough assets
    sample_firm._assets = 100000.0

    sample_firm.decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
        sales_aggressiveness=0.8, # Implies price adjustment
        hiring_aggressiveness=0.5,
        rd_aggressiveness=0.5,
        capital_aggressiveness=0.5,
        dividend_aggressiveness=0.5,
        debt_aggressiveness=0.5
    )

    firm_state = FirmStateDTO.from_firm(sample_firm)
    firm_config = _create_firm_config()

    context = DecisionContext(
        state=firm_state,
        config=firm_config,
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
        if order.order_type == "SELL" and order.market_id == sample_firm.specialization
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
        if order.order_type == "BUY" and order.market_id == "labor"
    ]
    assert len(buy_labor_orders) == 0, (
        "Expected no labor BUY orders if production target is met/exceeded"
    )


def test_firm_hiring_decision_no_inventory(sample_firm, sample_market_data):
    # Set inventory to 0, so it needs to produce
    sample_firm.inventory[sample_firm.specialization] = 0.0
    sample_firm.employees = []  # No employees

    # Update HR component
    mock_hr = Mock()
    mock_hr.employees = []
    mock_hr.employee_wages = {}
    sample_firm.hr = mock_hr

    # Ensure firm has enough assets
    sample_firm._assets = 100000.0
    sample_firm.production_target = 100.0
    sample_firm.inventory = {sample_firm.specialization: 0.0}
    sample_firm.capital_stock = 100.0

    sample_firm.decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(
        hiring_aggressiveness=0.8,
        sales_aggressiveness=0.5,
        rd_aggressiveness=0.5,
        capital_aggressiveness=0.5,
        dividend_aggressiveness=0.5,
        debt_aggressiveness=0.5
    )

    firm_state = FirmStateDTO.from_firm(sample_firm)
    firm_config = _create_firm_config()

    context = DecisionContext(
        state=firm_state,
        config=firm_config,
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
        if order.order_type == "BUY" and order.market_id == "labor"
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
        if order.order_type == "SELL" and order.market_id == sample_firm.specialization
    ]
    assert len(sell_orders) == 0, "Expected no SELL orders when inventory is 0"
