import pytest
from unittest.mock import Mock, MagicMock
from simulation.systems.sensory_system import SensorySystem
from simulation.systems.api import SensoryContext
from modules.simulation.api import ISensoryDataProvider

@pytest.fixture
def sensory_system():
    return SensorySystem(config=Mock())

def test_sensory_dto_generation(sensory_system):
    mock_tracker = Mock()
    mock_tracker.get_latest_indicators.return_value = {
        "avg_goods_price": 10.0,
        "unemployment_rate": 0.05,
        "total_production": 1000.0,
        "avg_wage": 50.0
    }

    mock_gov = Mock()
    mock_gov.approval_rating = 0.5

    mock_inequality = Mock()
    mock_inequality.calculate_gini_coefficient.return_value = 0.35

    # Mock Households with assets
    h1 = Mock(spec=ISensoryDataProvider)
    h1.get_sensory_snapshot.return_value = {"is_active": True, "total_wealth": 100.0, "approval_rating": 0.2}

    h2 = Mock(spec=ISensoryDataProvider)
    h2.get_sensory_snapshot.return_value = {"is_active": True, "total_wealth": 1000.0, "approval_rating": 0.8}

    households = [h1, h2]

    context: SensoryContext = {
        "tracker": mock_tracker,
        "government": mock_gov,
        "time": 1,
        "inequality_tracker": mock_inequality,
        "households": households
    }

    dto = sensory_system.generate_government_sensory_dto(context)

    assert dto.gini_index == 0.35

    # Low Asset = Bottom 50% = h1. Approval = 0.2
    assert dto.approval_low_asset == 0.2

    # High Asset = Top 20% of 2 agents?
    # n=2. Top 20% -> 0.4 agents -> int -> 0?
    # Logic was: n_high = int(n * 0.2). If 0, high_hh = [].
    # So approval_high_asset remains 0.5 (default).

    # Let's add more households to test Top 20%
    households_extended = []
    for i in range(10):
        h = Mock(spec=ISensoryDataProvider)
        h.get_sensory_snapshot.return_value = {
            "is_active": True,
            "total_wealth": float(i * 100),
            "approval_rating": i / 10.0
        }
        households_extended.append(h)

    context["households"] = households_extended
    # Mock inequality tracker call for new list (or ignore as we check logic inside)
    # The logic calls inequality_tracker.calculate_gini_coefficient with assets list.

    dto_ext = sensory_system.generate_government_sensory_dto(context)

    # Top 20% of 10 = 2 agents (Index 8, 9). Approval 0.8, 0.9. Avg = 0.85.
    assert dto_ext.approval_high_asset == pytest.approx(0.85)

    # Bottom 50% of 10 = 5 agents (Index 0-4). Approval 0.0, 0.1, 0.2, 0.3, 0.4. Avg = 0.2.
    assert dto_ext.approval_low_asset == pytest.approx(0.2)

def test_sensory_dto_missing_tracker(sensory_system):
    mock_tracker = Mock()
    mock_tracker.get_latest_indicators.return_value = {}
    mock_gov = Mock()
    mock_gov.approval_rating = 0.5

    context: SensoryContext = {
        "tracker": mock_tracker,
        "government": mock_gov,
        "time": 1,
        # No inequality tracker
    }

    dto = sensory_system.generate_government_sensory_dto(context)
    assert dto.gini_index == 0.0
    assert dto.approval_low_asset == 0.5
