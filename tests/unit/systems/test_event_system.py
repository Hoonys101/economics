import pytest
from unittest.mock import MagicMock
from simulation.systems.event_system import EventSystem
from simulation.systems.api import EventContext

@pytest.fixture
def event_system():
    config = MagicMock()
    settlement_system = MagicMock()
    return EventSystem(config, settlement_system)

def test_inflation_shock(event_system):
    # Setup
    # Hyperinflation now injects cash via Central Bank
    central_bank = MagicMock()

    h1 = MagicMock()
    # Mock wallet or assets
    h1.wallet.get_balance.return_value = 100.0

    context: EventContext = {
        "markets": {},
        "households": [h1],
        "firms": [],
        "central_bank": central_bank,
        "bank": MagicMock()
    }

    config = MagicMock()
    config.scenario_name = 'hyperinflation'
    config.start_tick = 200
    config.is_active = True
    config.demand_shock_cash_injection = 0.5

    # Execute Tick 200
    event_system.execute_scheduled_events(200, context, config)

    # Verify Cash Injection
    event_system.settlement_system.create_and_transfer.assert_called()
    # 100.0 * 0.5 = 50.0 injected

def test_recession_shock(event_system):
    # Setup
    h1 = MagicMock()
    h1.wallet.get_balance.return_value = 1000.0
    households = [h1]

    central_bank = MagicMock()

    context: EventContext = {
        "markets": {},
        "households": households,
        "firms": [],
        "central_bank": central_bank,
        "bank": MagicMock()
    }

    config = MagicMock()
    config.scenario_name = 'deflation'
    config.start_tick = 600
    config.is_active = True
    config.asset_shock_reduction = 0.5

    # Execute Tick 600
    event_system.execute_scheduled_events(600, context, config)

    # Verify Asset Destruction
    event_system.settlement_system.transfer_and_destroy.assert_called()
    # 1000.0 * 0.5 = 500.0 destroyed

def test_no_event(event_system):
    # Setup
    h1 = MagicMock()
    h1.wallet.get_balance.return_value = 1000.0

    context: EventContext = {
        "markets": {},
        "households": [h1],
        "firms": []
    }

    config = MagicMock()
    config.is_active = False # Inactive

    # Execute Tick 100 (No event)
    event_system.execute_scheduled_events(100, context, config)

    # Verify NO calls
    event_system.settlement_system.create_and_transfer.assert_not_called()
    event_system.settlement_system.transfer_and_destroy.assert_not_called()
