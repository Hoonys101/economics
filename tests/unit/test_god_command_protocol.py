import pytest
from unittest.mock import MagicMock, call
from uuid import uuid4
from simulation.dtos.commands import GodCommandDTO, GodResponseDTO
from modules.system.services.command_service import CommandService
from modules.system.api import IGlobalRegistry, IAgentRegistry, OriginType
from simulation.finance.api import ISettlementSystem, IFinancialAgent
from modules.system.constants import ID_CENTRAL_BANK

class MockRegistry(IGlobalRegistry):
    def __init__(self):
        self.data = {}
    def get(self, key, default=None):
        return self.data.get(key, default)
    def set(self, key, value, origin=None):
        self.data[key] = value
        return True

# Manually mock the interface + extra methods needed
class MockSettlementSystem:
    def audit_total_m2(self, expected_total=None):
        return True
    def mint_and_distribute(self, target_agent_id, amount, tick, reason):
        return True
    def transfer_and_destroy(self, source, sink_authority, amount, reason, tick, currency="USD"):
        return True
    # Add other ISettlementSystem methods if needed by CommandService init or other calls
    def transfer(self, *args, **kwargs): return None
    def create_and_transfer(self, *args, **kwargs): return None
    def record_liquidation(self, *args, **kwargs): return None

class MockAgentRegistry(IAgentRegistry):
    pass

@pytest.fixture
def mock_registry():
    return MockRegistry()

@pytest.fixture
def mock_settlement():
    # We use MagicMock but with our custom class as spec to ensure methods exist
    # OR just use MagicMock and attach methods.
    # The issue before was spec=ISettlementSystem which hid audit_total_m2.
    # Let's just use a plain MagicMock and configure it.
    settlement = MagicMock()
    settlement.audit_total_m2.return_value = True
    settlement.mint_and_distribute.return_value = True
    settlement.transfer_and_destroy.return_value = True
    return settlement

@pytest.fixture
def mock_agent_registry():
    registry = MagicMock(spec=MockAgentRegistry)
    agent = MagicMock(spec=IFinancialAgent)
    agent.id = 101
    registry.get_agent.return_value = agent
    return registry

@pytest.fixture
def command_service(mock_registry, mock_settlement, mock_agent_registry):
    return CommandService(mock_registry, mock_settlement, mock_agent_registry)

def test_set_param_success(command_service, mock_registry):
    mock_registry.data["test_key"] = 50
    cmd = GodCommandDTO(
        target_domain="Test",
        parameter_key="test_key",
        new_value=100,
        command_type="SET_PARAM"
    )

    results = command_service.execute_command_batch([cmd], tick=1, baseline_m2=1000)

    assert len(results) == 1
    assert results[0].success
    assert mock_registry.data["test_key"] == 100
    # Confirm commit cleared stack (accessing private for test)
    assert len(command_service.undo_stack._stack) == 0

def test_inject_asset_success(command_service, mock_settlement):
    cmd = GodCommandDTO(
        target_domain="Economy",
        parameter_key="101",
        new_value=1000,
        command_type="INJECT_ASSET"
    )

    results = command_service.execute_command_batch([cmd], tick=1, baseline_m2=1000)

    assert len(results) == 1
    assert results[0].success
    assert results[0].audit_report["m2_delta"] == 1000
    mock_settlement.mint_and_distribute.assert_called_with(target_agent_id=101, amount=1000, tick=1, reason=f"GodMode_{cmd.command_id}")
    mock_settlement.audit_total_m2.assert_called_with(expected_total=2000)

def test_audit_failure_rollback_money(command_service, mock_settlement, mock_agent_registry):
    # Setup audit failure
    mock_settlement.audit_total_m2.return_value = False

    cmd = GodCommandDTO(
        target_domain="Economy",
        parameter_key="101",
        new_value=1000,
        command_type="INJECT_ASSET"
    )

    results = command_service.execute_command_batch([cmd], tick=1, baseline_m2=1000)

    assert len(results) == 1
    assert not results[0].success
    assert results[0].rollback_performed
    assert results[0].failure_reason == "M2 Integrity Audit Failed"

    # Verify mint was called
    mock_settlement.mint_and_distribute.assert_called()
    # Verify rollback (burn) was called
    mock_settlement.transfer_and_destroy.assert_called()
    # Verify arguments for burn
    args, kwargs = mock_settlement.transfer_and_destroy.call_args
    assert kwargs['amount'] == 1000
    assert kwargs['reason'] == "GodMode_Rollback"

def test_mixed_batch_atomic_rollback(command_service, mock_registry, mock_settlement):
    mock_registry.data["tax_rate"] = 0.1
    mock_settlement.audit_total_m2.return_value = False

    cmd1 = GodCommandDTO(
        target_domain="Gov",
        parameter_key="tax_rate",
        new_value=0.2,
        command_type="SET_PARAM"
    )
    cmd2 = GodCommandDTO(
        target_domain="Eco",
        parameter_key="101",
        new_value=500,
        command_type="INJECT_ASSET"
    )

    results = command_service.execute_command_batch([cmd1, cmd2], tick=1, baseline_m2=1000)

    assert len(results) == 2
    assert not results[0].success
    assert not results[1].success
    assert results[0].rollback_performed

    # Verify Param Rollback
    assert mock_registry.data["tax_rate"] == 0.1 # Reverted

    # Verify Money Rollback
    mock_settlement.transfer_and_destroy.assert_called()

def test_validation_failure_aborts_batch(command_service, mock_registry):
    mock_registry.data["key"] = 1

    # cmd1 valid
    cmd1 = GodCommandDTO(target_domain="T", parameter_key="key", new_value=2, command_type="SET_PARAM")
    # cmd2 invalid (missing key)
    cmd2 = GodCommandDTO(target_domain="T", parameter_key="", new_value=3, command_type="SET_PARAM")

    results = command_service.execute_command_batch([cmd1, cmd2], tick=1, baseline_m2=100)

    # cmd2 fails validation -> exception -> break -> rollback batch
    assert len(results) == 2
    assert not results[0].success
    assert not results[1].success

    # cmd1 should be rolled back
    assert mock_registry.data["key"] == 1
