
import pytest
from unittest.mock import Mock, MagicMock
from modules.system.services.command_service import CommandService, UndoRecord
from modules.system.registry import GlobalRegistry, RegistryEntry
from modules.system.api import OriginType
from simulation.dtos.commands import GodCommandDTO
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAgentRegistry
from modules.system.constants import ID_CENTRAL_BANK
from modules.finance.api import IFinancialAgent

@pytest.fixture
def mock_registry():
    return GlobalRegistry()

@pytest.fixture
def mock_settlement_system():
    mock = Mock(spec=ISettlementSystem)
    mock.mint_and_distribute = Mock()
    mock.transfer_and_destroy = Mock()
    return mock

@pytest.fixture
def mock_agent_registry():
    registry = Mock(spec=IAgentRegistry)
    central_bank = Mock(spec=IFinancialAgent)
    central_bank.id = ID_CENTRAL_BANK

    def get_agent_side_effect(id):
        if str(id) == str(ID_CENTRAL_BANK):
            return central_bank
        agent = Mock(spec=IFinancialAgent)
        agent.id = id
        return agent

    registry.get_agent.side_effect = get_agent_side_effect
    return registry

@pytest.fixture
def command_service(mock_registry, mock_settlement_system, mock_agent_registry):
    return CommandService(mock_registry, mock_settlement_system, mock_agent_registry)

def test_rollback_set_param_preserves_origin(command_service, mock_registry):
    """Test that rolling back a SET_PARAM command restores the original OriginType and Lock status."""

    # 1. Setup initial state
    key = "test_param"
    initial_value = 100
    initial_origin = OriginType.SYSTEM
    mock_registry.set(key, initial_value, origin=initial_origin)

    # Verify setup
    entry = mock_registry.get_entry(key)
    assert entry.value == initial_value
    assert entry.origin == initial_origin
    assert not entry.is_locked

    # 2. Execute SET_PARAM command
    new_value = 200
    cmd = GodCommandDTO(
        target_domain="System",
        parameter_key=key,
        new_value=new_value,
        command_type="SET_PARAM"
    )

    # Manually execute internal handler to populate undo stack (as execute_command_batch does)
    command_service._handle_set_param(cmd)

    # Verify change
    entry = mock_registry.get_entry(key)
    assert entry.value == new_value
    assert entry.origin == OriginType.GOD_MODE
    assert entry.is_locked # Implicit lock by GOD_MODE

    # 3. Rollback
    result = command_service.rollback_last_tick()
    assert result is True

    # 4. Verify restoration
    entry = mock_registry.get_entry(key)
    assert entry.value == initial_value
    assert entry.origin == initial_origin
    assert not entry.is_locked # Lock should be cleared if it wasn't locked before

def test_rollback_set_param_deletes_new_key(command_service, mock_registry):
    """Test that rolling back a SET_PARAM command deletes a key that didn't exist before."""

    key = "new_param"

    # Execute SET_PARAM command
    cmd = GodCommandDTO(
        target_domain="System",
        parameter_key=key,
        new_value=123,
        command_type="SET_PARAM"
    )

    command_service._handle_set_param(cmd)

    # Verify creation
    assert mock_registry.get(key) == 123

    # Rollback
    command_service.rollback_last_tick()

    # Verify deletion
    assert mock_registry.get_entry(key) is None

def test_rollback_inject_asset(command_service, mock_settlement_system, mock_agent_registry):
    """Test that rolling back INJECT_ASSET calls settlement system to burn money."""

    cmd = GodCommandDTO(
        target_domain="Economy",
        parameter_key="101", # Target Agent ID
        new_value=1000,
        command_type="INJECT_ASSET"
    )

    # Mock successful injection
    mock_settlement_system.mint_and_distribute.return_value = True

    # Execute
    command_service._handle_inject_asset(cmd, tick=1)

    # Mock successful burn
    mock_settlement_system.transfer_and_destroy.return_value = True

    # Rollback
    result = command_service.rollback_last_tick()
    assert result is True

    # Verify transfer_and_destroy called
    mock_settlement_system.transfer_and_destroy.assert_called_once()
    call_args = mock_settlement_system.transfer_and_destroy.call_args
    assert call_args.kwargs['amount'] == 1000
