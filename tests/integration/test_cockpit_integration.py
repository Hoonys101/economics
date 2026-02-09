import pytest
from unittest.mock import MagicMock
from simulation.engine import Simulation
from modules.governance.cockpit.api import CockpitCommand
from simulation.orchestration.command_service import CommandService

# Mock dependencies for Simulation
@pytest.fixture
def mock_simulation_deps():
    config_manager = MagicMock()
    config_module = MagicMock()
    logger = MagicMock()
    repository = MagicMock()

    # Mock WorldState components
    world_state = MagicMock()
    world_state.config_manager = config_manager
    world_state.central_bank = MagicMock()
    world_state.government = MagicMock()
    world_state.government.corporate_tax_rate = 0.2
    world_state.government.income_tax_rate = 0.1

    return config_manager, config_module, logger, repository, world_state

def test_simulation_processes_pause_resume(mock_simulation_deps):
    cm, config_module, logger, repo, ws = mock_simulation_deps

    # Initialize Simulation (we need to patch WorldState creation or inject it)
    # Since Simulation creates WorldState internally, we can mock it after init
    # or rely on the fact that we can monkeypatch.
    # But simpler: just instantiate Simulation and mock its internals.

    # We can't easily mock __init__ without patching, so let's rely on patching WorldState class
    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        sim = Simulation(cm, config_module, logger, repo)

        # Verify initial state
        assert sim.is_paused is False

        # Enqueue PAUSE
        cmd = CockpitCommand(type="PAUSE", payload={})
        sim.command_service.enqueue_command(cmd)

        # Run tick (should process command)
        sim.run_tick()
        assert sim.is_paused is True

        # Enqueue RESUME
        cmd = CockpitCommand(type="RESUME", payload={})
        sim.command_service.enqueue_command(cmd)

        # Run tick
        sim.run_tick()
        assert sim.is_paused is False

def test_simulation_processes_set_base_rate(mock_simulation_deps):
    cm, config_module, logger, repo, ws = mock_simulation_deps

    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        sim = Simulation(cm, config_module, logger, repo)

        # Enqueue SET_BASE_RATE
        cmd = CockpitCommand(type="SET_BASE_RATE", payload={"rate": 0.15})
        sim.command_service.enqueue_command(cmd)

        sim.run_tick()

        assert ws.central_bank.base_rate == 0.15

def test_simulation_processes_set_tax_rate(mock_simulation_deps):
    cm, config_module, logger, repo, ws = mock_simulation_deps

    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        sim = Simulation(cm, config_module, logger, repo)

        # Enqueue SET_TAX_RATE (Corporate)
        cmd = CockpitCommand(type="SET_TAX_RATE", payload={"tax_type": "corporate", "rate": 0.25})
        sim.command_service.enqueue_command(cmd)

        sim.run_tick()
        assert ws.government.corporate_tax_rate == 0.25

        # Enqueue SET_TAX_RATE (Income)
        cmd = CockpitCommand(type="SET_TAX_RATE", payload={"tax_type": "income", "rate": 0.15})
        sim.command_service.enqueue_command(cmd)

        sim.run_tick()
        assert ws.government.income_tax_rate == 0.15
