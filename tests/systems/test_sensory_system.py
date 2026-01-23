import pytest
from collections import deque
from unittest.mock import MagicMock
from simulation.systems.sensory_system import SensorySystem
from simulation.systems.api import SensoryContext


@pytest.fixture
def sensory_system():
    config = MagicMock()
    return SensorySystem(config)


def test_generate_government_sensory_dto(sensory_system):
    # Setup
    tracker = MagicMock()
    # Mock return of get_latest_indicators
    tracker.get_latest_indicators.return_value = {
        "avg_goods_price": 11.0,  # Last was 10.0 -> 10% inflation
        "unemployment_rate": 0.05,
        "total_production": 110.0,  # Last was 0.0 -> ? (Assume 100 base)
        "avg_wage": 20.0,
    }
    # Initial state of system
    sensory_system.last_avg_price_for_sma = 10.0
    sensory_system.last_gdp_for_sma = 100.0

    government = MagicMock()
    government.approval_rating = 0.8

    context: SensoryContext = {"tracker": tracker, "government": government, "time": 10}

    # Execute
    dto = sensory_system.generate_government_sensory_dto(context)

    # Verify DTO
    assert dto.tick == 10

    # Inflation: (11 - 10) / 10 = 0.1
    assert sensory_system.inflation_buffer[-1] == 0.1
    assert dto.inflation_sma == 0.1  # Single value average

    # GDP Growth: (110 - 100) / 100 = 0.1
    assert sensory_system.gdp_growth_buffer[-1] == 0.1
    assert dto.gdp_growth_sma == 0.1

    assert dto.unemployment_sma == 0.05
    assert dto.wage_sma == 20.0
    assert dto.approval_sma == 0.8
    assert dto.current_gdp == 110.0


def test_buffer_smoothing(sensory_system):
    # Add some history
    sensory_system.inflation_buffer.append(0.0)
    sensory_system.inflation_buffer.append(0.1)

    # Avg should be 0.05

    tracker = MagicMock()
    tracker.get_latest_indicators.return_value = {
        "avg_goods_price": 10.0,  # No change from last
    }
    sensory_system.last_avg_price_for_sma = 10.0

    government = MagicMock()
    government.approval_rating = 0.5

    context: SensoryContext = {"tracker": tracker, "government": government, "time": 2}

    dto = sensory_system.generate_government_sensory_dto(context)

    # Buffer: [0.0, 0.1, 0.0] -> Avg = 0.1 / 3 = 0.0333...
    assert len(sensory_system.inflation_buffer) == 3
    assert abs(dto.inflation_sma - 0.0333) < 0.001
