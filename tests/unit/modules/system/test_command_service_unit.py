import pytest
from unittest.mock import MagicMock, Mock, call
from modules.system.services.command_service import CommandService, UndoRecord
from simulation.dtos.commands import GodCommandDTO, GodResponseDTO
from modules.system.api import OriginType, RegistryEntry, IRestorableRegistry, IGlobalRegistry
from modules.system.constants import ID_CENTRAL_BANK
from simulation.finance.api import IFinancialAgent
from uuid import uuid4

@pytest.fixture
def mock_registry():
    # By default, mock_registry will be a MagicMock, which does NOT pass isinstance(mock, IRestorableRegistry)
    # unless we specify the spec properly.
    # But MagicMock is tricky with isinstance checks if we don't set spec.
    # However, for default tests we want IGlobalRegistry behavior (fallback).
    # We will create specific fixtures for RestorableRegistry.
    return MagicMock(spec=IGlobalRegistry)

@pytest.fixture
def mock_restorable_registry():
    return MagicMock(spec=IRestorableRegistry)

@pytest.fixture
def mock_settlement():
    # Ensure audit_total_m2 returns True by default
    mock = MagicMock()
    mock.audit_total_m2.return_value = True
    return mock

@pytest.fixture
def mock_agent_registry():
    return MagicMock()

@pytest.fixture
def command_service(mock_registry, mock_settlement, mock_agent_registry):
    return CommandService(mock_registry, mock_settlement, mock_agent_registry)

@pytest.fixture
def restorable_command_service(mock_restorable_registry, mock_settlement, mock_agent_registry):
    return CommandService(mock_restorable_registry, mock_settlement, mock_agent_registry)

def test_dispatch_set_param(command_service, mock_registry):
    cmd = GodCommandDTO(
        command_type="SET_PARAM",
        target_domain="test",
        parameter_key="test_param",
        new_value=100
    )

    # Setup mock to return previous entry
    previous_entry = RegistryEntry(key="test_param", value=50, origin=OriginType.SYSTEM)
    mock_registry.get_entry.return_value = previous_entry
    mock_registry.set.return_value = True

    results = command_service.execute_command_batch([cmd], tick=0, baseline_m2=1000)

    assert len(results) == 1
    assert results[0].success is True
    # Verify get_entry called instead of get
    mock_registry.get_entry.assert_called_with("test_param")
    mock_registry.set.assert_called_with("test_param", 100, origin=OriginType.GOD_MODE)

def test_rollback_set_param_restorable(restorable_command_service, mock_restorable_registry):
    # This test uses IRestorableRegistry
    cmd = GodCommandDTO(
        command_type="SET_PARAM",
        target_domain="test",
        parameter_key="test_param",
        new_value=100
    )
    previous_entry = RegistryEntry(key="test_param", value=50, origin=OriginType.SYSTEM)
    mock_restorable_registry.get_entry.return_value = previous_entry
    mock_restorable_registry.set.return_value = True

    restorable_command_service.execute_command_batch([cmd], tick=0, baseline_m2=1000)

    # Rollback
    success = restorable_command_service.rollback_last_tick()

    assert success
    # Verify restore_entry called
    mock_restorable_registry.restore_entry.assert_called_with("test_param", previous_entry)

def test_rollback_set_param_fallback(command_service, mock_registry):
    # This test uses IGlobalRegistry (not restorable), so it should fallback to set()
    cmd = GodCommandDTO(
        command_type="SET_PARAM",
        target_domain="test",
        parameter_key="test_param",
        new_value=100
    )
    previous_entry = RegistryEntry(key="test_param", value=50, origin=OriginType.SYSTEM)
    mock_registry.get_entry.return_value = previous_entry
    mock_registry.set.return_value = True

    command_service.execute_command_batch([cmd], tick=0, baseline_m2=1000)

    # Reset mock to clear the first set call
    mock_registry.set.reset_mock()
    mock_registry.set.return_value = True # Ensure set still returns True

    # Rollback
    success = command_service.rollback_last_tick()

    assert success
    # Verify fallback to set() was used because mock_registry is not IRestorableRegistry
    mock_registry.set.assert_called_with("test_param", 50, origin=OriginType.SYSTEM)
    # verify restore_entry was NOT called (it shouldn't exist on the mock anyway if spec is IGlobalRegistry)
    # mock_registry.restore_entry.assert_not_called() # Might fail if method doesn't exist on spec

def test_rollback_creation_restorable(restorable_command_service, mock_restorable_registry):
    # Test rollback of a new parameter creation (previous_entry is None)
    cmd = GodCommandDTO(
        command_type="SET_PARAM",
        target_domain="test",
        parameter_key="new_param",
        new_value=100
    )
    # previous_entry is None
    mock_restorable_registry.get_entry.return_value = None
    mock_restorable_registry.set.return_value = True

    restorable_command_service.execute_command_batch([cmd], tick=0, baseline_m2=1000)

    # Rollback
    success = restorable_command_service.rollback_last_tick()

    assert success
    # Verify delete_entry called
    mock_restorable_registry.delete_entry.assert_called_with("new_param")

def test_dispatch_inject_money(command_service, mock_settlement):
    cmd = GodCommandDTO(
        command_type="INJECT_ASSET",
        target_domain="settlement",
        parameter_key="1",
        new_value=1000
    )
    mock_settlement.mint_and_distribute.return_value = True

    results = command_service.execute_command_batch([cmd], tick=0, baseline_m2=1000)

    assert len(results) == 1
    assert results[0].success is True
    # Note: CommandService converts string ID to int if possible
    mock_settlement.mint_and_distribute.assert_called_with(target_agent_id=1, amount=1000, tick=0, reason=f"GodMode_{cmd.command_id}")

def test_rollback_inject_money(command_service, mock_settlement, mock_agent_registry):
    cmd = GodCommandDTO(
        command_type="INJECT_ASSET",
        target_domain="settlement",
        parameter_key="1",
        new_value=1000
    )
    mock_settlement.mint_and_distribute.return_value = True

    # Setup agents for rollback
    target_agent = MagicMock(spec=IFinancialAgent)
    target_agent.id = 1
    central_bank = MagicMock(spec=IFinancialAgent)
    central_bank.id = ID_CENTRAL_BANK

    def get_agent_side_effect(id):
        if str(id) == str(ID_CENTRAL_BANK):
            return central_bank
        if str(id) == "1" or id == 1:
            return target_agent
        return None

    mock_agent_registry.get_agent.side_effect = get_agent_side_effect
    mock_settlement.transfer_and_destroy.return_value = MagicMock() # Return transaction

    command_service.execute_command_batch([cmd], tick=0, baseline_m2=1000)

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

    # Correct instantiation with previous_entry
    previous_entry = RegistryEntry(key="test", value=0, origin=OriginType.SYSTEM)
    record = UndoRecord(
        command_id=uuid4(),
        command_type="SET_PARAM",
        target_domain="test",
        parameter_key="test",
        previous_entry=previous_entry,
        new_value=1
    )
    command_service.undo_stack.push(record)

    assert len(command_service.undo_stack._current_batch) == 1

    # Commit the batch to main stack
    command_service.undo_stack.commit_batch()
    assert len(command_service.undo_stack._stack) == 1
