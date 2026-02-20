import pytest
from unittest.mock import MagicMock, patch
from modules.governance.cockpit.api import CockpitCommand
from modules.governance.api import SystemCommandType
from simulation.engine import Simulation
from modules.system.services.command_service import CommandService
from modules.system.registry import GlobalRegistry, AgentRegistry
from simulation.systems.settlement_system import SettlementSystem
from simulation.world_state import WorldState
from simulation.dtos.api import SimulationState
from simulation.agents.government import Government
from modules.government.dtos import FiscalPolicyDTO

@pytest.fixture
def mock_deps():
    # Mock SchemaLoader to avoid file system dependency issues during test
    with patch('modules.system.services.schema_loader.SchemaLoader.load_schema', return_value=[]):
        registry = GlobalRegistry()
    settlement = MagicMock(spec=SettlementSystem)
    agent_registry = AgentRegistry()
    return registry, settlement, agent_registry

def test_cockpit_command_flow_tax_rate(mock_deps):
    registry, settlement, agent_registry = mock_deps

    # Create CommandService
    command_service = CommandService(registry, settlement, agent_registry)

    # Mock Simulation Config and Logger
    config_manager = MagicMock()
    config_manager.get.return_value = ":memory:" # Valid sqlite path

    config_module = MagicMock()
    logger = MagicMock()
    repository = MagicMock()

    # Instantiate Simulation
    sim = Simulation(
        config_manager=config_manager,
        config_module=config_module,
        logger=logger,
        repository=repository,
        registry=registry,
        settlement_system=settlement,
        agent_registry=agent_registry,
        command_service=command_service
    )

    # Setup World State
    # Use spec=Government to prevent Mock Drift and ensure Protocol Fidelity
    sim.world_state.government = MagicMock(spec=Government)
    sim.world_state.government.corporate_tax_rate = 0.2
    sim.world_state.government.income_tax_rate = 0.1
    sim.world_state.governments = [sim.world_state.government] # Align DTO

    # Use spec=FiscalPolicyDTO for nested object
    sim.world_state.government.fiscal_policy = MagicMock(spec=FiscalPolicyDTO)
    sim.world_state.government.fiscal_policy.corporate_tax_rate = 0.2
    sim.world_state.government.fiscal_policy.income_tax_rate = 0.1 # Ensure all required fields are present if needed

    sim.world_state.time = 1

    # Test Enqueue
    cockpit_cmd = CockpitCommand(
        type="SET_TAX_RATE",
        payload={"tax_type": "corporate", "rate": 0.35}
    )

    sim.command_service.enqueue_command(cockpit_cmd)

    # Run _process_commands (part of run_tick)
    sim._process_commands()

    # Verify it moved to world_state.system_commands
    assert len(sim.world_state.system_commands) == 1
    cmd = sim.world_state.system_commands[0]
    assert cmd.command_type == SystemCommandType.SET_TAX_RATE
    assert cmd.new_rate == 0.35

    # Instantiate Phase_SystemCommands
    from simulation.orchestration.phases.system_commands import Phase_SystemCommands
    phase = Phase_SystemCommands(sim.world_state)

    # Create Mock SimulationState
    # TD-TEST-COCKPIT-MOCK: Ensure we pass SimulationState, not WorldState
    mock_sim_state = MagicMock(spec=SimulationState)
    mock_sim_state.time = sim.world_state.time
    mock_sim_state.system_commands = sim.world_state.system_commands
    mock_sim_state.primary_government = sim.world_state.government

    # Execute Phase
    phase.execute(mock_sim_state)

    # Verify State Change
    assert sim.world_state.government.corporate_tax_rate == 0.35
    assert sim.world_state.system_commands == [] # Should be cleared

def test_cockpit_command_flow_pause(mock_deps):
    registry, settlement, agent_registry = mock_deps
    command_service = CommandService(registry, settlement, agent_registry)

    config_manager = MagicMock()
    config_manager.get.return_value = ":memory:"

    sim = Simulation(
        config_manager=config_manager,
        config_module=MagicMock(),
        logger=MagicMock(),
        repository=MagicMock(),
        registry=registry,
        settlement_system=settlement,
        agent_registry=agent_registry,
        command_service=command_service
    )

    sim.is_paused = False

    # Enqueue PAUSE
    cockpit_cmd = CockpitCommand(type="PAUSE")
    sim.command_service.enqueue_command(cockpit_cmd)

    # Verify queue
    assert len(sim.command_service._command_queue) == 1

    # Process
    sim._process_commands()

    # Verify Simulation is paused
    assert sim.is_paused == True

    # Verify queue drained
    assert len(sim.command_service._command_queue) == 0
