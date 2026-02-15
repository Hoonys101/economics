
import pytest
from unittest.mock import MagicMock
from simulation.systems.demographic_manager import DemographicManager
from simulation.core_agents import Household
from simulation.factories.household_factory import HouseholdFactory
from simulation.models import Order

class MockAgent:
    def __init__(self, id, gender, is_active=True):
        self.id = id
        self.gender = gender
        self.is_active = is_active

def test_demographic_event_consistency():
    # Setup
    manager = DemographicManager()
    manager._stats_cache = {
        "M": {"count": 0, "total_labor_hours": 0.0},
        "F": {"count": 0, "total_labor_hours": 0.0}
    }

    # Birth
    agent_m = MockAgent(1, "M")
    agent_f = MockAgent(2, "F")

    manager.register_birth(agent_m)
    manager.register_birth(agent_f)

    stats = manager.get_gender_stats()
    assert stats["M"]["count"] == 1
    assert stats["F"]["count"] == 1
    assert stats["total_population"] == 2

    # Labor Update
    manager.update_labor_hours("M", 8.0)
    manager.update_labor_hours("F", 4.0)

    stats = manager.get_gender_stats()
    assert stats["M"]["total_labor_hours"] == 8.0
    assert stats["M"]["avg_labor_hours"] == 8.0
    assert stats["F"]["total_labor_hours"] == 4.0
    assert stats["F"]["avg_labor_hours"] == 4.0

    # Death
    manager.register_death(agent_m)

    stats = manager.get_gender_stats()
    assert stats["M"]["count"] == 0
    assert stats["F"]["count"] == 1
    # Note: Labor hours should be cleared by the agent sending a negative delta before death
    # The manager itself doesn't auto-clear unless agent sends signal.
    # In this test, we verify that count decremented.

    assert agent_m.is_active == False

def test_sync_stats():
    manager = DemographicManager()

    agents = [
        MockAgent(1, "M"),
        MockAgent(2, "M"),
        MockAgent(3, "F")
    ]

    manager.sync_stats(agents)

    stats = manager.get_gender_stats()
    assert stats["M"]["count"] == 2
    assert stats["F"]["count"] == 1
    assert stats["total_population"] == 3
