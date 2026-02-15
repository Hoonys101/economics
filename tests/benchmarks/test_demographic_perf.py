
import pytest
import time
from unittest.mock import MagicMock
from simulation.systems.demographic_manager import DemographicManager
from simulation.core_agents import Household

def test_demographic_manager_perf():
    # Setup
    manager = DemographicManager()
    manager._stats_cache = {
        "M": {"count": 5000, "total_labor_hours": 20000.0},
        "F": {"count": 5000, "total_labor_hours": 20000.0}
    }

    start_time = time.time()
    for _ in range(1000):
        stats = manager.get_gender_stats()
    end_time = time.time()

    duration = end_time - start_time
    print(f"1000 calls took {duration:.6f}s")

    assert duration < 0.1, "O(1) stats retrieval is too slow!"
    assert stats["total_population"] == 10000
