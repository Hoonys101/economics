import pytest
from unittest.mock import MagicMock
from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.api import CommerceContext

@pytest.fixture
def commerce_system():
    config = MagicMock()
    # Mock config values
    config.FOOD_CONSUMPTION_QUANTITY = 1.0
    return CommerceSystem(config)

def test_execute_consumption_and_leisure(commerce_system):
    # Setup Households
    h1 = MagicMock()
    h1.id = 1
    h1.is_active = True
    h1._assets = 100.0
    h1.inventory = {"basic_food": 0}
    # Mock apply_leisure_effect return
    effect_dto = MagicMock()
    effect_dto.utility_gained = 5.0
    effect_dto.leisure_type = "IDLE"
    h1.apply_leisure_effect.return_value = effect_dto

    # Mock get_quantity for education_service check
    h1.get_quantity.return_value = 0.0

    households = [h1]

    # Mock Context
    mock_reflux = MagicMock()
    context: CommerceContext = {
        "households": households,
        "breeding_planner": MagicMock(),
        "household_time_allocation": {1: 8.0},
        "reflux_system": mock_reflux,
        "market_data": {},
        "config": commerce_system.config,
        "time": 1
    }

    # Plan
    planned_consumptions = {
        1: {
            "consume_amount": 1.0,
            "buy_amount": 2.0,
            "consumed_immediately_from_buy": 0.0
        }
    }

    # Execute
    leisure_effects = commerce_system.finalize_consumption_and_leisure(context, planned_consumptions)

    # Verify
    # 2. Consumption: Consume 1.0
    h1.consume.assert_called_with("basic_food", 1.0, 1)

    # 3. Leisure
    h1.apply_leisure_effect.assert_called_with(8.0, {'basic_food': 1.0})

    # 4. Return Value
    assert leisure_effects[1] == 5.0

def test_fast_track_consumption_if_needed(commerce_system):
    # Case: Inventory 0, Consumes 0 (in vector), Buys 2.
    # Should trigger immediate consumption from bought items.

    h1 = MagicMock()
    h1.id = 1
    h1.is_active = True
    h1._assets = 100.0
    h1.inventory = {"basic_food": 0}

    effect_dto = MagicMock()
    effect_dto.utility_gained = 0.0
    h1.apply_leisure_effect.return_value = effect_dto

    # Mock get_quantity for education_service check
    h1.get_quantity.return_value = 0.0

    # Mock Reflux System (Fix injection)
    mock_reflux = MagicMock()

    context: CommerceContext = {
        "households": [h1],
        "breeding_planner": MagicMock(),
        "household_time_allocation": {},
        "reflux_system": mock_reflux,
        "market_data": {},
        "config": commerce_system.config,
        "time": 1
    }

    # Plan
    # Simulate Fast Track: buy_amount=2.0, consume_amount=1.0 (logic assumes we consume what we need)
    planned_consumptions = {
        1: {
            "consume_amount": 1.0,
            "buy_amount": 2.0,
            "consumed_immediately_from_buy": 1.0
        }
    }

    commerce_system.finalize_consumption_and_leisure(context, planned_consumptions)

    # Verify Immediate Consumption
    # Expect consume call with default 1.0 (from config) or min(bought, default)
    h1.consume.assert_called_with("basic_food", 1.0, 1)
