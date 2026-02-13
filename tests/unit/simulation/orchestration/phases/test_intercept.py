import pytest
from unittest.mock import MagicMock, Mock
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
    return Phase0_Intercept(mock_world_state)

def test_execute_no_commands(phase, mock_world_state):
    state = MagicMock(spec=SimulationState)
    state.god_commands = []

    new_state = phase.execute(state)

    assert new_state == state
    mock_world_state.settlement_system.audit_total_m2.assert_not_called()

def test_execute_commands_audit_pass(phase, mock_world_state):
    state = MagicMock(spec=SimulationState)
    state.god_commands = [
        GodCommandDTO(command_type="INJECT_MONEY", target_agent_id=1, amount=100, target_domain="settlement")
    ]
    state.time = 10

    mock_world_state.settlement_system.mint_and_distribute.return_value = True
    mock_world_state.settlement_system.audit_total_m2.return_value = True

    new_state = phase.execute(state)

    # Verify dispatch called (via settlement system mock inside command service)
    mock_world_state.settlement_system.mint_and_distribute.assert_called()

    # Verify audit called with correct expectation
    # Baseline 10000 + 100 = 10100
    mock_world_state.settlement_system.audit_total_m2.assert_called_with(expected_total=10100)

    # Verify baseline updated
    assert mock_world_state.baseline_money_supply == 10100

    # Verify commands cleared
    assert len(state.god_commands) == 0

def test_execute_commands_audit_fail_rollback(phase, mock_world_state):
    state = MagicMock(spec=SimulationState)
    state.god_commands = [
        GodCommandDTO(command_type="INJECT_MONEY", target_agent_id=1, amount=100, target_domain="settlement")
    ]
    state.time = 10

    mock_world_state.settlement_system.mint_and_distribute.return_value = True
    # Audit fails
    mock_world_state.settlement_system.audit_total_m2.return_value = False

    # Mock command_service.rollback_last_tick
    phase.command_service.rollback_last_tick = MagicMock(return_value=True)

    new_state = phase.execute(state)

    # Verify rollback called
    phase.command_service.rollback_last_tick.assert_called()

    # Verify baseline NOT updated (since we rolled back)
    assert mock_world_state.baseline_money_supply == 10000
