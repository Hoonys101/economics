import pytest
from unittest.mock import MagicMock, Mock
from modules.system.services.command_service import CommandService
from simulation.dtos.commands import GodCommandDTO
from modules.system.api import OriginType
from modules.system.constants import ID_CENTRAL_BANK
from modules.finance.api import IFinancialAgent

@pytest.fixture
def mock_registry():
    return MagicMock()

@pytest.fixture
def mock_settlement():
    return MagicMock()

@pytest.fixture
def mock_agent_registry():
    return MagicMock()

@pytest.fixture
def command_service(mock_registry, mock_settlement, mock_agent_registry):
    return CommandService(mock_registry, mock_settlement, mock_agent_registry)

def test_dispatch_set_param(command_service, mock_registry):
    cmd = GodCommandDTO(
        command_type="SET_PARAM",
        target_domain="test",
        parameter_name="test_param",
        new_value=100
    )

    # Setup mock to return previous value
    mock_registry.get.return_value = 50
    mock_registry.set.return_value = True

    results = command_service.dispatch_commands([cmd])

    assert len(results) == 1
    assert "SUCCESS" in results[0]
    mock_registry.get.assert_called_with("test_param", None)
    mock_registry.set.assert_called_with("test_param", 100, origin=OriginType.GOD_MODE)

def test_rollback_set_param(command_service, mock_registry):
    # Dispatch first
    cmd = GodCommandDTO(
        command_type="SET_PARAM",
        target_domain="test",
        parameter_name="test_param",
        new_value=100
    )
    mock_registry.get.return_value = 50
    mock_registry.set.return_value = True
    command_service.dispatch_commands([cmd])

    # Rollback
    success = command_service.rollback_last_tick()

    assert success
    # Verify it set back to previous value (50)
    # The last set call should be 50
    mock_registry.set.assert_called_with("test_param", 50, origin=OriginType.GOD_MODE)

def test_dispatch_inject_money(command_service, mock_settlement):
    cmd = GodCommandDTO(
        command_type="INJECT_MONEY",
        target_domain="settlement",
        target_agent_id=1,
        amount=1000
    )
    mock_settlement.mint_and_distribute.return_value = True

    results = command_service.dispatch_commands([cmd])

    assert len(results) == 1
    assert "SUCCESS" in results[0]
    mock_settlement.mint_and_distribute.assert_called_with(1, 1000, tick=0, reason="GodMode")

def test_rollback_inject_money(command_service, mock_settlement, mock_agent_registry):
    cmd = GodCommandDTO(
        command_type="INJECT_MONEY",
        target_domain="settlement",
        target_agent_id=1,
        amount=1000
    )
    mock_settlement.mint_and_distribute.return_value = True

    # Setup agents for rollback
    target_agent = MagicMock(spec=IFinancialAgent)
    central_bank = MagicMock(spec=IFinancialAgent)

    def get_agent_side_effect(id):
        if str(id) == str(ID_CENTRAL_BANK):
            return central_bank
        if id == 1:
            return target_agent
        return None

    mock_agent_registry.get_agent.side_effect = get_agent_side_effect

    mock_settlement.transfer_and_destroy.return_value = MagicMock() # Return transaction

    command_service.dispatch_commands([cmd])

    success = command_service.rollback_last_tick()

    assert success
    mock_settlement.transfer_and_destroy.assert_called_with(
        source=target_agent,
        sink_authority=central_bank,
        amount=1000,
        reason="GodMode_Rollback",
        tick=0
    )

def test_commit_last_tick_clears_stack(command_service):
    # Simulate a batch
    command_service.undo_stack.start_batch()
    command_service.undo_stack.push(MagicMock())

    assert len(command_service.undo_stack._stack) == 1

    # Commit
    command_service.commit_last_tick()

    # Verify stack is empty
    assert len(command_service.undo_stack._stack) == 0
