import pytest
from unittest.mock import MagicMock
from simulation.systems.event_system import EventSystem
from simulation.systems.api import EventContext

@pytest.fixture
def event_system():
    config = MagicMock()
    return EventSystem(config)

def test_inflation_shock(event_system):
    # Setup
    market = MagicMock()
    market.current_price = 100.0
    market.avg_price = 100.0
    markets = {"goods": market}

    context: EventContext = {
        "markets": markets,
        "households": [],
        "firms": []
    }

    # Execute Tick 200
    event_system.execute_scheduled_events(200, context)

    # Verify
    assert market.current_price == 150.0
    assert market.avg_price == 150.0

def test_recession_shock(event_system):
    # Setup
    h1 = MagicMock()
    h1.assets = 1000.0
    households = [h1]

    context: EventContext = {
        "markets": {},
        "households": households,
        "firms": []
    }

    # Execute Tick 600
    event_system.execute_scheduled_events(600, context)

    # Verify
    assert h1.assets == 500.0

def test_no_event(event_system):
    # Setup
    h1 = MagicMock()
    h1.assets = 1000.0
    market = MagicMock()
    market.current_price = 100.0

    context: EventContext = {
        "markets": {"goods": market},
        "households": [h1],
        "firms": []
    }

    # Execute Tick 100 (No event)
    event_system.execute_scheduled_events(100, context)

    # Verify
    assert h1.assets == 1000.0
    assert market.current_price == 100.0
