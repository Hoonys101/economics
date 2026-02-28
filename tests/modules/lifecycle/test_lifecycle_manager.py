import pytest
import logging
from unittest.mock import MagicMock
from modules.lifecycle.api import AgentRegistrationDTO, LifecycleEventType
from modules.lifecycle.manager import AgentLifecycleManager, AgentRegistrationException
from modules.system.api import IAgentRegistry, AgentID, IAgent, IAssetRecoverySystem
from modules.finance.api import IMonetaryLedger

def test_atomic_registration_failure_rolls_back_registry():
    # Setup mocks
    registry_mock = MagicMock(spec=IAgentRegistry)
    ledger_mock = MagicMock(spec=IMonetaryLedger)
    saga_mock = MagicMock()
    market_mock = MagicMock()
    recovery_mock = MagicMock(spec=IAssetRecoverySystem)
    logger = logging.getLogger("test")

    manager = AgentLifecycleManager(registry_mock, ledger_mock, saga_mock, market_mock, recovery_mock, logger)

    # Force firm factory to raise exception
    manager.firm_factory = MagicMock()
    manager.firm_factory.create.side_effect = Exception("Factory failed")

    dto = AgentRegistrationDTO(agent_type="firm", initial_assets={"cash": 1000}, metadata={})

    with pytest.raises(AgentRegistrationException):
        manager.register_firm(dto)

    registry_mock.register.assert_not_called()
    ledger_mock.record_monetary_expansion.assert_not_called()


def test_deactivation_clears_sagas_and_orders():
    # Setup mocks
    registry_mock = MagicMock(spec=IAgentRegistry)
    ledger_mock = MagicMock(spec=IMonetaryLedger)
    saga_mock = MagicMock()
    market_mock = MagicMock()
    recovery_mock = MagicMock(spec=IAssetRecoverySystem)
    logger = logging.getLogger("test")

    manager = AgentLifecycleManager(registry_mock, ledger_mock, saga_mock, market_mock, recovery_mock, logger)

    agent_mock = MagicMock(spec=IAgent)
    agent_mock.is_active = True
    registry_mock.get_agent.return_value = agent_mock

    event = manager.deactivate_agent(100, LifecycleEventType.BANKRUPT)

    assert not agent_mock.is_active
    saga_mock.cancel_all_sagas_for_agent.assert_called_once_with(100)
    market_mock.cancel_all_orders_for_agent.assert_called_once_with(100)
    assert event.agent_id == 100
    assert event.reason == LifecycleEventType.BANKRUPT
