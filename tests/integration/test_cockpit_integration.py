import pytest
import queue
from unittest.mock import MagicMock
from simulation.engine import Simulation
from simulation.dtos.commands import GodCommandDTO
from modules.system.services.command_service import CommandService
from modules.system.api import IGlobalRegistry, IAgentRegistry
from simulation.finance.api import ISettlementSystem

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

    from collections import deque
    # Initialize queues as real objects to allow draining
    world_state.command_queue = queue.Queue()
    world_state.god_command_queue = deque()

    return config_manager, config_module, logger, repository, world_state

def test_simulation_processes_pause_resume(mock_simulation_deps):
    cm, config_module, logger, repo, ws = mock_simulation_deps

    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        # Mocks for new dependencies
        reg = MagicMock(spec=IGlobalRegistry)
        settle = MagicMock(spec=ISettlementSystem)
        agent_reg = MagicMock(spec=IAgentRegistry)

        sim = Simulation(cm, config_module, logger, repo, reg, settle, agent_reg)

        # Verify initial state
        assert sim.is_paused is False

        # Enqueue PAUSE (using new DTO format)
        cmd = GodCommandDTO(
            command_type="PAUSE_STATE",
            target_domain="System",
            parameter_key="PAUSE",
            new_value=True
        )
        ws.command_queue.put(cmd)

        # Run tick (should process command locally in _process_commands)
        sim.run_tick()
        assert sim.is_paused is True

        # Enqueue RESUME
        cmd = GodCommandDTO(
            command_type="PAUSE_STATE",
            target_domain="System",
            parameter_key="PAUSE",
            new_value=False
        )
        ws.command_queue.put(cmd)

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

        reg = MagicMock(spec=IGlobalRegistry)
        settle = MagicMock(spec=ISettlementSystem)
        agent_reg = MagicMock(spec=IAgentRegistry)

        sim = Simulation(cm, config_module, logger, repo, reg, settle, agent_reg)

        # Enqueue SET_BASE_RATE via SET_PARAM
        cmd = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="CentralBank",
            parameter_key="base_rate",
            new_value=0.15
        )
        ws.command_queue.put(cmd)

        # Run tick
        # Note: Since TickOrchestrator is mocked, it won't execute Phase 0.
        # We verify that Simulation forwarded the command to god_command_queue.
        sim.run_tick()

        assert len(ws.god_command_queue) == 1
        assert ws.god_command_queue[0].command_type == "SET_PARAM"
        assert ws.god_command_queue[0].new_value == 0.15

def test_simulation_processes_set_tax_rate(mock_simulation_deps):
    cm, config_module, logger, repo, ws = mock_simulation_deps

    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        reg = MagicMock(spec=IGlobalRegistry)
        settle = MagicMock(spec=ISettlementSystem)
        agent_reg = MagicMock(spec=IAgentRegistry)

        sim = Simulation(cm, config_module, logger, repo, reg, settle, agent_reg)

        # Enqueue SET_TAX_RATE (Corporate)
        cmd = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="Government",
            parameter_key="corporate_tax_rate",
            new_value=0.25
        )
        ws.command_queue.put(cmd)

        sim.run_tick()
        assert len(ws.god_command_queue) == 1
        assert ws.god_command_queue[0].parameter_key == "corporate_tax_rate"
        assert ws.god_command_queue[0].new_value == 0.25

        # Clear queue for next step
        ws.god_command_queue.clear()

        # Enqueue SET_TAX_RATE (Income)
        cmd = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="Government",
            parameter_key="income_tax_rate",
            new_value=0.15
        )
        ws.command_queue.put(cmd)

        sim.run_tick()
        assert len(ws.god_command_queue) == 1
        assert ws.god_command_queue[0].parameter_key == "income_tax_rate"
        assert ws.god_command_queue[0].new_value == 0.15
