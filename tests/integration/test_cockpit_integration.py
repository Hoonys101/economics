import pytest
from unittest.mock import MagicMock
from simulation.engine import Simulation
# from modules.governance.cockpit.api import CockpitCommand # Deprecated/Replaced
from simulation.dtos.commands import GodCommandDTO
from modules.system.services.command_service import CommandService
from modules.system.server_bridge import CommandQueue

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

    # Initialize command_queue for the test
    world_state.command_queue = CommandQueue()
    world_state.god_command_queue = [] # Initialize list

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

        # FIX: Inject all required dependencies
        mock_registry = MagicMock()
        mock_settlement = MagicMock()
        mock_agent_registry = MagicMock()

        sim = Simulation(cm, config_module, logger, repo, mock_registry, mock_settlement, mock_agent_registry)

        # Verify initial state
        assert sim.is_paused is False

        # Enqueue PAUSE via GodCommandDTO (PAUSE_STATE, new_value=True)
        cmd = GodCommandDTO(
            target_domain="System",
            parameter_key="PAUSE",
            command_type="PAUSE_STATE",
            new_value=True
        )
        sim.world_state.command_queue.put(cmd)

        # Run tick (should process command)
        sim.run_tick()
        assert sim.is_paused is True

        # Enqueue RESUME (PAUSE_STATE, new_value=False)
        cmd = GodCommandDTO(
            target_domain="System",
            parameter_key="RESUME",
            command_type="PAUSE_STATE",
            new_value=False
        )
        sim.world_state.command_queue.put(cmd)

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

        mock_registry = MagicMock()
        mock_settlement = MagicMock()
        mock_agent_registry = MagicMock()

        sim = Simulation(cm, config_module, logger, repo, mock_registry, mock_settlement, mock_agent_registry)

        # Enqueue SET_BASE_RATE (Actually SET_PARAM now via CommandService, but test checked manual handling?)
        # Wait, the old test expected ws.central_bank.base_rate to be updated.
        # My refactored _process_commands pushes to god_command_queue.
        # TickOrchestrator executes god_command_queue.
        # Since we mocked TickOrchestrator, the command will NOT be executed by logic inside TickOrchestrator.
        # So this test relies on Simulation._process_commands executing it?
        # But I removed execution logic from Simulation._process_commands!
        #
        # If I want this test to pass with Mock TickOrchestrator, I must verify that the command
        # was pushed to god_command_queue, OR I must rely on TickOrchestrator (which is mocked).
        #
        # The test asserts `ws.central_bank.base_rate == 0.15`.
        # This implies execution.
        # Since I moved execution to TickOrchestrator (Phase0_Intercept), and TickOrchestrator is mocked,
        # this assertion will FAIL unless I mock TickOrchestrator to execute commands or check the queue.
        #
        # I should probably update the test to assert that command was pushed to god_command_queue.

        cmd = GodCommandDTO(
            target_domain="Economy",
            parameter_key="base_rate", # Not "rate" as in legacy
            command_type="SET_PARAM",
            new_value=0.15
        )
        sim.world_state.command_queue.put(cmd)

        sim.run_tick()

        # Verify it's in god_command_queue
        assert len(ws.god_command_queue) == 1
        assert ws.god_command_queue[0].new_value == 0.15

        # We cannot assert actual state change because logic is moved to Orchestrator which is mocked.
        # Legacy test asserted state change because Simulation._process_commands did it.
        # Architecture shift means Simulation is no longer responsible for this.

def test_simulation_processes_set_tax_rate(mock_simulation_deps):
    cm, config_module, logger, repo, ws = mock_simulation_deps

    with pytest.MonkeyPatch.context() as m:
        m.setattr("simulation.engine.WorldState", MagicMock(return_value=ws))
        m.setattr("simulation.engine.ActionProcessor", MagicMock())
        m.setattr("simulation.engine.TickOrchestrator", MagicMock())
        m.setattr("simulation.engine.SimulationLogger", MagicMock())

        mock_registry = MagicMock()
        mock_settlement = MagicMock()
        mock_agent_registry = MagicMock()

        sim = Simulation(cm, config_module, logger, repo, mock_registry, mock_settlement, mock_agent_registry)

        # Enqueue SET_TAX_RATE (Corporate) -> SET_PARAM
        cmd = GodCommandDTO(
            target_domain="Government",
            parameter_key="corporate_tax_rate",
            command_type="SET_PARAM",
            new_value=0.25
        )
        sim.world_state.command_queue.put(cmd)

        sim.run_tick()

        assert len(ws.god_command_queue) == 1
        assert ws.god_command_queue[0].parameter_key == "corporate_tax_rate"

        # Clear queue for next check
        ws.god_command_queue.clear()

        # Enqueue SET_TAX_RATE (Income)
        cmd = GodCommandDTO(
            target_domain="Government",
            parameter_key="income_tax_rate",
            command_type="SET_PARAM",
            new_value=0.15
        )
        sim.world_state.command_queue.put(cmd)

        sim.run_tick()
        assert len(ws.god_command_queue) == 1
        assert ws.god_command_queue[0].parameter_key == "income_tax_rate"
