import pytest
import queue
from unittest.mock import MagicMock
from simulation.engine import Simulation
from simulation.dtos.commands import GodCommandDTO
from modules.system.services.command_service import CommandService
from modules.system.api import IGlobalRegistry, IAgentRegistry, OriginType
from simulation.finance.api import ISettlementSystem
from modules.system.command_pipeline.api import ICommandIngressService
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
    world_state.god_commands = []
    world_state.time = 0
    world_state.baseline_money_supply = 100000.0

    from collections import deque
    # Initialize queues as real objects to allow draining
    world_state.command_queue = CommandQueue()
    world_state.god_commands = []

    # Configure config_manager to return a valid string for database path
    # to avoid sqlite3.OperationalError when DBManager is initialized with a Mock
    def config_get_side_effect(key, default=None):
        if key in ["simulation.database_name", "simulation.db_path"]:
            return ":memory:"
        return default
    config_manager.get.side_effect = config_get_side_effect

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
        command_ingress = MagicMock(spec=ICommandIngressService)

        sim = Simulation(cm, config_module, logger, repo, registry, settlement_system, agent_registry, cmd_service, command_ingress)
        # Force world_state to be our mock
        sim.world_state = ws
        # Configure global_registry mock on world_state
        sim.world_state.global_registry.get.return_value = False

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
        command_ingress.drain_control_commands.return_value = [cmd]

        # Run tick (should process command locally in _process_commands)
        sim.run_tick()

        # Verify CommandService was called
        cmd_service.execute_command_batch.assert_called()
        args, _ = cmd_service.execute_command_batch.call_args
        assert len(args[0]) == 1
        assert args[0][0].command_type == "PAUSE_STATE"
        assert args[0][0].new_value is True

        # Manually simulate state change since CommandService is mocked
        sim.world_state.global_registry.get.return_value = True
        assert sim.is_paused is True

        # Reset mock
        cmd_service.execute_command_batch.reset_mock()

        # Enqueue RESUME
        cmd = GodCommandDTO(
            command_type="PAUSE_STATE",
            target_domain="System",
            parameter_key="pause",
            new_value=False,
            command_id=uuid4()
        )
        command_ingress.drain_control_commands.return_value = [cmd]

        # Run tick
        sim.run_tick()

        # Verify CommandService was called
        cmd_service.execute_command_batch.assert_called()
        args, _ = cmd_service.execute_command_batch.call_args
        assert len(args[0]) == 1
        assert args[0][0].command_type == "PAUSE_STATE"
        assert args[0][0].new_value is False

        # Manually simulate state change
        sim.world_state.global_registry.get.return_value = False
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
        command_ingress = MagicMock(spec=ICommandIngressService)

        sim = Simulation(cm, config_module, logger, repo, registry, settlement_system, agent_registry, cmd_service, command_ingress)
        sim.world_state = ws

        # Enqueue SET_PARAM central_bank.base_rate
        cmd1 = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="CentralBank",
            parameter_key="central_bank.base_rate",
            new_value=0.15,
            command_id=uuid4()
        )
        # We mock drain_control_commands to force Simulation to execute it via command_service
        command_ingress.drain_control_commands.return_value = [cmd1]

        sim.run_tick()

        # Verify Execution: Queue drained, CommandService called
        assert len(ws.god_commands) == 0
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
        command_ingress.drain_control_commands.return_value = [cmd2]

        # Run tick
        sim.run_tick()

        # Verify Execution
        assert len(ws.god_commands) == 0
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
        command_ingress = MagicMock(spec=ICommandIngressService)

        sim = Simulation(cm, config_module, logger, repo, registry, settlement_system, agent_registry, cmd_service, command_ingress)
        sim.world_state = ws

        # Enqueue SET_TAX_RATE (Corporate)
        cmd = GodCommandDTO(
            command_type="SET_PARAM",
            target_domain="Government",
            parameter_key="corporate_tax_rate",
            new_value=0.25,
            command_id=uuid4()
        )
        command_ingress.drain_control_commands.return_value = [cmd]

        sim.run_tick()

        assert len(ws.god_commands) == 0
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
        command_ingress.drain_control_commands.return_value = [cmd]

        sim.run_tick()

        assert len(ws.god_commands) == 0
        cmd_service.execute_command_batch.assert_called()
        args, _ = cmd_service.execute_command_batch.call_args
        assert len(args[0]) == 1
        assert args[0][0].parameter_key == "income_tax_rate"
