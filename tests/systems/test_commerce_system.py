import pytest
from unittest.mock import MagicMock
from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.api import CommerceContext


@pytest.fixture
def commerce_system():
    config = MagicMock()
    # Mock config values
    config.FOOD_CONSUMPTION_QUANTITY = 1.0
    reflux_system = MagicMock()
    return CommerceSystem(config, reflux_system)


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

    households = [h1]

    # Mock Vector Planner
    planner = MagicMock()
    # h1 consumes 1, buys 2
    planner.decide_consumption_batch.return_value = {
        "consume": [1.0],
        "buy": [2.0],
        "price": 10.0,
    }

    # Mock Context
    context: CommerceContext = {
        "households": households,
        "breeding_planner": planner,
        "household_time_allocation": {1: 8.0},
        "reflux_system": commerce_system.reflux_system,
        "market_data": {},
        "config": commerce_system.config,
        "time": 1,
    }

    # Execute
    leisure_effects = commerce_system.execute_consumption_and_leisure(context)

    # Verify
    # 1. Purchase: Buy 2.0 @ 10.0 = 20.0 cost
    assert h1.assets == 80.0  # 100 - 20
    assert h1.inventory["basic_food"] == 2.0

    # 2. Consumption: Consume 1.0 (Fast Consumption)
    h1.consume.assert_called_with("basic_food", 1.0, 1)

    # 3. Leisure
    h1.apply_leisure_effect.assert_called_with(8.0, {"basic_food": 1.0})

    # 4. Return Value
    assert leisure_effects[1] == 5.0

    # 5. Lifecycle Update called
    h1.update_needs.assert_called_once()

    # 6. Reflux Capture
    commerce_system.reflux_system.capture.assert_called_with(
        20.0, source="Household_1", category="emergency_food"
    )


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

    planner = MagicMock()
    planner.decide_consumption_batch.return_value = {
        "consume": [0.0],  # Planner says consume 0 because inventory was 0
        "buy": [2.0],
        "price": 10.0,
    }

    context: CommerceContext = {
        "households": [h1],
        "breeding_planner": planner,
        "household_time_allocation": {},
        "reflux_system": commerce_system.reflux_system,
        "market_data": {},
        "config": commerce_system.config,
        "time": 1,
    }

    commerce_system.execute_consumption_and_leisure(context)

    # Verify Immediate Consumption
    # Expect consume call with default 1.0 (from config) or min(bought, default)
    h1.consume.assert_called_with("basic_food", 1.0, 1)
