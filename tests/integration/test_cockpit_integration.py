import pytest
import queue
from unittest.mock import MagicMock
from simulation.engine import Simulation
from simulation.dtos.commands import GodCommandDTO
from modules.system.services.command_service import CommandService
from modules.system.api import IGlobalRegistry, IAgentRegistry, OriginType
from simulation.finance.api import ISettlementSystem
from modules.system.server_bridge import CommandQueue
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

    from collections import deque
    # Initialize queues as real objects to allow draining
    world_state.command_queue = CommandQueue()
    world_state.god_command_queue = deque()

    return config_manager, config_module, logger, repository, registry, settlement_system, agent_registry, world_state

def test_simulation_processes_pause_resume(mock_simulation_deps):
    cm, config_module, logger, repo, registry, settlement_system, agent_registry, ws = mock_simulation_deps

    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        # Mocks for new dependencies
        reg = MagicMock(spec=IGlobalRegistry)
        settle = MagicMock(spec=ISettlementSystem)
        agent_reg = MagicMock(spec=IAgentRegistry)
        cmd_service = MagicMock(spec=CommandService)

        sim = Simulation(cm, config_module, logger, repo, registry, settlement_system, agent_registry, cmd_service)
        # Force world_state to be our mock
        sim.world_state = ws

        # Verify initial state
        assert sim.is_paused is False

        # Enqueue PAUSE (using new DTO format)
        cmd = GodCommandDTO(
            command_type="PAUSE_STATE",
            target_domain="System",
            parameter_key="pause",
            new_value=True,
            command_id=uuid4()
        )
        ws.command_queue.put(cmd)

        # Run tick (should process command locally in _process_commands)
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
        ws.command_queue.put(cmd)

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

        cmd_service = MagicMock(spec=CommandService)
        cmd_service.execute_command_batch.return_value = []
        sim = Simulation(cm, config_module, logger, repo, registry, settlement_system, agent_registry, cmd_service)
        sim.world_state = ws

        # Enqueue SET_PARAM central_bank.base_rate
        cmd1 = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="CentralBank",
            parameter_key="central_bank.base_rate",
            new_value=0.15,
            command_id=uuid4()
        )
        ws.command_queue.put(cmd1)

        sim.run_tick()

        # Verify Execution: Queue drained, CommandService called
        assert len(ws.god_command_queue) == 0
        cmd_service.execute_command_batch.assert_called()
        # Verify the batch contained our command
        args, _ = cmd_service.execute_command_batch.call_args
        assert len(args[0]) == 1
        assert args[0][0].parameter_key == "central_bank.base_rate"

        cmd_service.execute_command_batch.reset_mock()

        # Enqueue SET_BASE_RATE via SET_PARAM
        cmd2 = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="CentralBank",
            parameter_key="base_rate",
            new_value=0.15
        )
        ws.command_queue.put(cmd2)

        # Run tick
        sim.run_tick()

        # Verify Execution
        assert len(ws.god_command_queue) == 0
        cmd_service.execute_command_batch.assert_called()
        args, _ = cmd_service.execute_command_batch.call_args
        assert len(args[0]) == 1
        assert args[0][0].new_value == 0.15

def test_simulation_processes_set_tax_rate(mock_simulation_deps):
    cm, config_module, logger, repo, registry, settlement_system, agent_registry, ws = mock_simulation_deps

    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        cmd_service = MagicMock(spec=CommandService)
        cmd_service.execute_command_batch.return_value = []
        sim = Simulation(cm, config_module, logger, repo, registry, settlement_system, agent_registry, cmd_service)
        sim.world_state = ws

        # Enqueue SET_TAX_RATE (Corporate)
        cmd = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="Government",
            parameter_key="corporate_tax_rate",
            new_value=0.25,
            command_id=uuid4()
        )
        ws.command_queue.put(cmd)

        sim.run_tick()

        assert len(ws.god_command_queue) == 0
        cmd_service.execute_command_batch.assert_called()
        args, _ = cmd_service.execute_command_batch.call_args
        assert len(args[0]) == 1
        assert args[0][0].parameter_key == "corporate_tax_rate"

        cmd_service.execute_command_batch.reset_mock()

        # Enqueue SET_TAX_RATE (Income)
        cmd = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="Government",
            parameter_key="income_tax_rate",
            new_value=0.15,
            command_id=uuid4()
        )
        ws.command_queue.put(cmd)

        sim.run_tick()

        assert len(ws.god_command_queue) == 0
        cmd_service.execute_command_batch.assert_called()
        args, _ = cmd_service.execute_command_batch.call_args
        assert len(args[0]) == 1
        assert args[0][0].parameter_key == "income_tax_rate"
