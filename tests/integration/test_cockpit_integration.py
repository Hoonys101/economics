import pytest
from unittest.mock import MagicMock
from simulation.engine import Simulation
from simulation.dtos.commands import GodCommandDTO
from modules.system.api import OriginType
from uuid import uuid4

# Mock dependencies for Simulation
@pytest.fixture
def mock_simulation_deps():
    config_manager = MagicMock()
    config_module = MagicMock()
    logger = MagicMock()
    repository = MagicMock()

    # Mocks for new dependencies
    registry = MagicMock()
    settlement_system = MagicMock()
    agent_registry = MagicMock()

    # Mock WorldState components
    world_state = MagicMock()
    world_state.config_manager = config_manager
    world_state.central_bank = MagicMock()
    world_state.government = MagicMock()
    world_state.government.corporate_tax_rate = 0.2
    world_state.government.income_tax_rate = 0.1
    world_state.god_command_queue = []
    world_state.time = 0
    world_state.baseline_money_supply = 100000.0

    return config_manager, config_module, logger, repository, registry, settlement_system, agent_registry, world_state

def test_simulation_processes_pause_resume(mock_simulation_deps):
    cm, config_module, logger, repo, registry, settlement_system, agent_registry, ws = mock_simulation_deps

    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        sim = Simulation(cm, config_module, logger, repo, registry, settlement_system, agent_registry)
        # Force world_state to be our mock (since Simulation creates its own even if we mock class)
        sim.world_state = ws

        # Verify initial state
        assert sim.is_paused is False

        # Enqueue PAUSE (GodCommandDTO)
        cmd = GodCommandDTO(
            command_type="PAUSE_STATE",
            target_domain="System",
            parameter_key="pause",
            new_value=True,
            command_id=uuid4()
        )
        ws.god_command_queue.append(cmd)

        # Run tick (should process command)
        sim.run_tick()
        assert sim.is_paused is True

        # Enqueue RESUME
        cmd = GodCommandDTO(
            command_type="PAUSE_STATE",
            target_domain="System",
            parameter_key="pause",
            new_value=False,
            command_id=uuid4()
        )
        ws.god_command_queue.append(cmd)

        # Run tick
        sim.run_tick()
        assert sim.is_paused is False

def test_simulation_processes_set_base_rate(mock_simulation_deps):
    cm, config_module, logger, repo, registry, settlement_system, agent_registry, ws = mock_simulation_deps

    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        sim = Simulation(cm, config_module, logger, repo, registry, settlement_system, agent_registry)
        sim.world_state = ws

        # Enqueue SET_PARAM central_bank.base_rate
        cmd = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="CentralBank",
            parameter_key="central_bank.base_rate",
            new_value=0.15,
            command_id=uuid4()
        )
        ws.god_command_queue.append(cmd)

        sim.run_tick()

        # Check if Registry.set was called
        registry.set.assert_called_with("central_bank.base_rate", 0.15, origin=OriginType.GOD_MODE)

def test_simulation_processes_set_tax_rate(mock_simulation_deps):
    cm, config_module, logger, repo, registry, settlement_system, agent_registry, ws = mock_simulation_deps

    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        sim = Simulation(cm, config_module, logger, repo, registry, settlement_system, agent_registry)
        sim.world_state = ws

        # Enqueue SET_PARAM government.corporate_tax_rate
        cmd = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="Government",
            parameter_key="government.corporate_tax_rate",
            new_value=0.25,
            command_id=uuid4()
        )
        ws.god_command_queue.append(cmd)

        sim.run_tick()

        registry.set.assert_any_call("government.corporate_tax_rate", 0.25, origin=OriginType.GOD_MODE)

        # Enqueue SET_PARAM government.income_tax_rate
        cmd = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="Government",
            parameter_key="government.income_tax_rate",
            new_value=0.15,
            command_id=uuid4()
        )
        ws.god_command_queue.append(cmd)

        sim.run_tick()

        registry.set.assert_any_call("government.income_tax_rate", 0.15, origin=OriginType.GOD_MODE)
