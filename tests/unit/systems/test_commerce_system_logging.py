import pytest
from unittest.mock import MagicMock, patch
from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.api import CommerceContext

@patch("simulation.systems.commerce_system.simulation")
def test_log_reject_when_stock_out_and_insolvent(mock_simulation):
    # Setup
    config = MagicMock()
    config.SALES_TAX_RATE = 0.05
    commerce_system = CommerceSystem(config)

    # Mock Household
    h1 = MagicMock()
    h1.id = 1
    h1.is_active = True
    # Update for Econ/Bio component structure
    h1._econ_state.assets = 10.0
    h1._econ_state.inventory = {"basic_food": 0}
    h1._bio_state.needs = {"survival": 80.0}
    h1._bio_state.is_active = True

    # Mock Planner
    planner = MagicMock()
    planner.survival_threshold = 50.0
    # Consumes 0 (stock out), Buys 0 (insolvent? or just didn't buy)
    planner.decide_consumption_batch.return_value = {
        "consume": [0.0],
        "buy": [0.0],
        "price": 20.0 # High price > assets
    }

    context = {
        "households": [h1],
        "breeding_planner": planner,
        "market_data": {},
        "time": 1,
        "household_time_allocation": {}
    }

    # Enable logging
    mock_simulation.logger = MagicMock()

    # Execute
    commerce_system.plan_consumption_and_leisure(context)

    # Verify
    mock_simulation.logger.log_thought.assert_called_once()
    args, kwargs = mock_simulation.logger.log_thought.call_args
    assert kwargs['decision'] == 'REJECT'
    assert kwargs['reason'] == 'INSOLVENT' # assets 10 < price 20

@patch("simulation.systems.commerce_system.simulation")
def test_log_reject_when_stock_out_but_solvent(mock_simulation):
    # Setup
    config = MagicMock()
    config.SALES_TAX_RATE = 0.05
    commerce_system = CommerceSystem(config)

    # Mock Household
    h1 = MagicMock()
    h1.id = 1
    h1.is_active = True
    h1._econ_state.assets = 100.0 # Solvent
    h1._econ_state.inventory = {"basic_food": 0}
    h1._bio_state.needs = {"survival": 80.0}
    h1._bio_state.is_active = True

    # Mock Planner
    planner = MagicMock()
    planner.survival_threshold = 50.0
    # Consumes 0 (stock out), Buys 0 (planner didn't buy for some reason)
    planner.decide_consumption_batch.return_value = {
        "consume": [0.0],
        "buy": [0.0],
        "price": 20.0
    }

    context = {
        "households": [h1],
        "breeding_planner": planner,
        "market_data": {},
        "time": 1,
        "household_time_allocation": {}
    }

    # Enable logging
    mock_simulation.logger = MagicMock()

    # Execute
    commerce_system.plan_consumption_and_leisure(context)

    # Verify
    mock_simulation.logger.log_thought.assert_called_once()
    args, kwargs = mock_simulation.logger.log_thought.call_args
    assert kwargs['decision'] == 'REJECT'
    assert kwargs['reason'] == 'STOCK_OUT'
