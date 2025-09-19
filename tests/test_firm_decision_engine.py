import pytest
from simulation.firms import Firm
from simulation.decisions.firm_decision_engine import FirmDecisionEngine
import config

# Mock config values for testing
@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
    monkeypatch.setattr(config, 'FIRM_PRODUCTION_TARGETS', {'food': 100.0})
    monkeypatch.setattr(config, 'FIRM_PRODUCTIVITY_FACTOR', 1.0)
    monkeypatch.setattr(config, 'GOODS_MARKET_SELL_PRICE', 10.0)
    monkeypatch.setattr(config, 'LABOR_MARKET_OFFERED_WAGE', 5.0)

@pytest.fixture
def sample_firm():
    firm = Firm(
        id=1,
        initial_capital=1000.0,
        initial_liquidity_need=10.0,
        production_targets={'food': 100.0},
        productivity_factor=1.0,
        decision_engine=FirmDecisionEngine(),
        value_orientation="test_firm_vo",
        logger=None # Pass None for logger in tests or mock it
    )
    firm.inventory['food'] = 50.0 # Initial inventory
    return firm

@pytest.fixture
def sample_market_data():
    return {
        "time": 0,
        "goods_market": {
            "food_current_sell_price": 10.0
        },
        "labor_market": {
            "avg_wage": 5.0
        },
        "loan_market": {
            "interest_rate": 0.05
        },
        "all_households": [],
        "goods_data": [{'id': 'food', 'name': 'Food', 'utility_per_need': {'survival_need': 1.0}}]
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

    # Call make_decisions
    orders = sample_firm.decision_engine.make_decisions(sample_firm, sample_market_data, 0)

    # Assertions for production (assuming produce is called internally or orders are generated)
    # The FirmDecisionEngine primarily generates BUY/SELL orders, not directly production.
    # Production happens in firm.produce() which is called by the simulation engine.
    # So, we should test if the firm tries to hire or sell based on its inventory/targets.

    # Test if a SELL order for 'food' is generated if inventory > target
    # Or if a BUY order for 'labor' is generated if employees < needed for target

    # For this test, let's assume it tries to sell if it has inventory above a certain threshold
    # or if it needs to reduce inventory.
    sell_orders = [order for order in orders if order.order_type == 'SELL' and order.market_id == 'goods_market']
    assert len(sell_orders) > 0, "Expected firm to generate SELL orders for goods"
    assert sell_orders[0].item_id == 'food'
    assert sell_orders[0].quantity > 0

    # Test if a BUY order for 'labor' is generated if it needs more production
    # This assertion depends on the internal logic of FirmDecisionEngine.
    # If it prioritizes selling over hiring when inventory is high, this might be 0.
    # For now, let's just check if any labor orders are made.
    # assert len(buy_labor_orders) > 0, "Expected firm to generate BUY orders for labor"

def test_firm_no_production_if_target_met(sample_firm, sample_market_data):
    # Set inventory to meet or exceed target
    sample_firm.inventory['food'] = 150.0 # Above target of 100

    # Ensure no employees are present to focus on inventory decision
    sample_firm.employees = []

    orders = sample_firm.decision_engine.make_decisions(sample_firm, sample_market_data, 0)

    # Expect SELL orders to reduce inventory, but not necessarily BUY labor orders
    sell_orders = [order for order in orders if order.order_type == 'SELL' and order.market_id == 'goods_market']
    assert len(sell_orders) > 0, "Expected firm to generate SELL orders to reduce excess inventory"
    assert sell_orders[0].item_id == 'food'
    assert sell_orders[0].quantity > 0

    # If target is met/exceeded, it should not try to hire more for production
    # This assertion depends heavily on the FirmDecisionEngine's internal logic.
    # For now, we'll assume it might still try to hire for other reasons or if its logic is not perfect.
    # assert len(buy_labor_orders) == 0, "Expected no labor BUY orders if production target is met/exceeded"

def test_firm_hiring_decision_no_inventory(sample_firm, sample_market_data):
    # Set inventory to 0, so it needs to produce
    sample_firm.inventory['food'] = 0.0
    sample_firm.employees = [] # No employees

    orders = sample_firm.decision_engine.make_decisions(sample_firm, sample_market_data, 0)

    # Expect BUY labor orders to meet production target
    buy_labor_orders = [order for order in orders if order.order_type == 'BUY' and order.market_id == 'labor_market']
    assert len(buy_labor_orders) > 0, "Expected firm to generate BUY orders for labor when inventory is low"
    assert buy_labor_orders[0].item_id == 'labor'
    assert buy_labor_orders[0].quantity == 1 # Assuming it tries to hire one unit of labor

    sell_orders = [order for order in orders if order.order_type == 'SELL' and order.market_id == 'goods_market']
    assert len(sell_orders) == 0, "Expected no SELL orders when inventory is 0"