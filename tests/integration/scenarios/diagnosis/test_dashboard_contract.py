
import pytest
from unittest.mock import MagicMock
from simulation.dtos.watchtower import WatchtowerSnapshotDTO
from simulation.orchestration.dashboard_service import DashboardService
from simulation.engine import Simulation
from simulation.world_state import WorldState
from simulation.metrics.economic_tracker import EconomicIndicatorTracker

@pytest.fixture
def mock_sim_instance():
    sim = MagicMock(spec=Simulation)
    sim.world_state = MagicMock(spec=WorldState)
    sim.world_state.tracker = MagicMock(spec=EconomicIndicatorTracker)
    # Setup mocks for tracker
    sim.world_state.tracker.get_latest_indicators.return_value = {
        "gdp": 1000.0,
        "gini": 0.3,
        "goods_price_index": 1.0,
        "unemployment_rate": 5.0,
        "velocity_of_money": 1.5,
        "social_cohesion": 0.7,
        "quintile_1_avg_assets": 100.0,
        "quintile_2_avg_assets": 200.0,
        "quintile_3_avg_assets": 300.0,
        "quintile_4_avg_assets": 400.0,
        "quintile_5_avg_assets": 500.0,
        "active_population": 100
    }
    sim.world_state.tracker.calculate_monetary_aggregates.return_value = {
        "m0": 100.0,
        "m1": 500.0,
        "m2": 600.0
    }
    sim.world_state.time = 42
    sim.world_state.run_id = "test_run"
    sim.world_state.governments = []
    sim.world_state.markets = {}
    sim.world_state.central_bank = None
    sim.world_state.bank = None
    sim.world_state.calculate_total_money.return_value = {"USD": 1000.0}
    sim.world_state.baseline_money_supply = 1000.0

    return sim

def test_dashboard_snapshot_structure(mock_sim_instance):
    """
    Phase 3-A: Verify DashboardService produces a valid WatchtowerSnapshotDTO.
    """
    service = DashboardService(mock_sim_instance)
    snapshot = service.get_snapshot()

    assert isinstance(snapshot, WatchtowerSnapshotDTO)
    assert snapshot.tick == 42
    assert snapshot.macro.gdp == 1000.0
    assert snapshot.macro.gini == 0.3
    assert snapshot.finance.supply.m2 == 600.0
    assert snapshot.finance.supply.m0 == 100.0
    assert snapshot.population.active_count == 100
    assert snapshot.population.distribution.q1 == 100.0
