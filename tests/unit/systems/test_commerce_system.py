import pytest
from unittest.mock import MagicMock
from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.api import CommerceContext

@pytest.fixture
def commerce_system():
    config = MagicMock()
    # Mock config values
    config.FOOD_CONSUMPTION_QUANTITY = 1.0
    config.SALES_TAX_RATE = 0.05
    return CommerceSystem(config)

def test_plan_consumption_and_leisure_generates_transaction(commerce_system):
    # Setup Households
    h1 = MagicMock()
    h1.id = 1
    h1.is_active = True
    h1._econ_state.assets = 100.0
    h1._econ_state.inventory = {"basic_food": 0}
    h1._bio_state.needs = {"survival": 80.0}
    h1._bio_state.is_active = True

    households = [h1]

    # Mock Vector Planner
    planner = MagicMock()
    # h1 consumes 1, buys 2
    planner.decide_consumption_batch.return_value = {
        "consume": [1.0],
        "buy": [2.0],
        "price": 10.0
    }
    planner.survival_threshold = 50.0

    # Mock Context
    context: CommerceContext = {
        "households": households,
        "breeding_planner": planner,
        "household_time_allocation": {1: 8.0},
        "market_data": {},
        "config": commerce_system.config,
        "time": 1
    }

    # Execute
    planned, transactions = commerce_system.plan_consumption_and_leisure(context)

    # Verify
    # Should generate 1 transaction
    assert len(transactions) == 1
    tx = transactions[0]
    assert tx.buyer_id == 1
    assert tx.quantity == 2.0
    assert tx.price == 10.0
    assert tx.item_id == "basic_food"

    # Verify Plan
    assert planned[1]["buy_amount"] == 2.0
    assert planned[1]["consume_amount"] == 1.0

def test_plan_consumption_refuses_when_tax_unaffordable(commerce_system):
    # Setup Households
    h1 = MagicMock()
    h1.id = 1
    h1.is_active = True
    # Assets enough for Price (10.0 * 2 = 20.0), but not Price + Tax (20.0 * 1.05 = 21.0)
    h1._econ_state.assets = 20.5
    h1._econ_state.inventory = {"basic_food": 0}
    h1._bio_state.needs = {"survival": 80.0}
    h1._bio_state.is_active = True

    households = [h1]

    # Mock Vector Planner
    planner = MagicMock()
    # h1 consumes 1, buys 2
    planner.decide_consumption_batch.return_value = {
        "consume": [1.0],
        "buy": [2.0],
        "price": 10.0
    }
    planner.survival_threshold = 50.0

    # Mock Context
    context: CommerceContext = {
        "households": households,
        "breeding_planner": planner,
        "household_time_allocation": {1: 8.0},
        "market_data": {},
        "config": commerce_system.config,
        "time": 1
    }

    # Execute
    planned, transactions = commerce_system.plan_consumption_and_leisure(context)

    # Verify
    # Should NOT generate transaction because 20.5 < 21.0
    assert len(transactions) == 0
    assert planned[1].get("buy_amount", 0.0) == 0.0
