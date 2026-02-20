import pytest
from unittest.mock import Mock, MagicMock
from simulation.orchestration.phases.intercept import Phase0_Intercept
from simulation.dtos.api import SimulationState
from simulation.dtos.commands import GodCommandDTO

@pytest.fixture
def mock_world_state():
    ws = MagicMock()
    ws.global_registry = MagicMock()
    ws.settlement_system = MagicMock()
    # Mock agent_registry on settlement_system
    ws.settlement_system.agent_registry = MagicMock()
    ws.baseline_money_supply = 10000
    return ws

@pytest.fixture
def phase(mock_world_state):
    p = Phase0_Intercept(mock_world_state)
    p.command_service = MagicMock() # Mock service to check calls
    return p

def test_execute_no_commands(phase, mock_world_state):
    state = MagicMock(spec=SimulationState)
    state.god_command_snapshot = []

    new_state = phase.execute(state)

    assert new_state == state
    mock_world_state.settlement_system.audit_total_m2.assert_not_called()

def test_execute_commands_audit_pass(phase, mock_world_state):
    state = MagicMock(spec=SimulationState)
    state.god_command_snapshot = [
        GodCommandDTO(command_type="INJECT_MONEY", target_agent_id=1, amount=100, target_domain="settlement", parameter_key="legacy", new_value=None)
    ]
    state.time = 10

    mock_world_state.settlement_system.mint_and_distribute.return_value = True
    mock_world_state.settlement_system.audit_total_m2.return_value = True

    new_state = phase.execute(state)

    # Verify execute_command_batch called with correct tick and baseline
    args, _ = phase.command_service.execute_command_batch.call_args
    # args[0] is commands list (which is mutated to empty, so we ignore content check)
    assert args[1] == 10
    assert args[2] == 10000

    # Verify commands cleared
    assert len(state.god_command_snapshot) == 0

# Removed test_execute_commands_audit_fail_rollback as Phase0 no longer handles rollback logic directly (delegated to CommandService)
