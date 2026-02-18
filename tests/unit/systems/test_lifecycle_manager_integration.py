import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle_manager import AgentLifecycleManager
from simulation.dtos.api import SimulationState

class TestAgentLifecycleManager:
    @pytest.fixture
    def manager(self):
        config = MagicMock()
        demographic_manager = MagicMock()
        inheritance_manager = MagicMock()
        firm_system = MagicMock()
        settlement_system = MagicMock()
        public_manager = MagicMock()
        logger = MagicMock()
        household_factory = MagicMock()
        hr_service = MagicMock()
        tax_service = MagicMock()
        agent_registry = MagicMock()

        return AgentLifecycleManager(
            config, demographic_manager, inheritance_manager, firm_system,
            settlement_system, public_manager, logger,
            household_factory=household_factory,
            hr_service=hr_service,
            tax_service=tax_service,
            agent_registry=agent_registry
        )

    def test_execute_delegation(self, manager):
        state = MagicMock()

        # Mock sub-systems execution results
        # NOTE: Sub-systems are now required to return lists of Transactions
        manager.aging_system.execute = MagicMock(return_value=[])
        manager.birth_system.execute = MagicMock(return_value=[MagicMock(id="tx1")])
        manager.death_system.execute = MagicMock(return_value=[MagicMock(id="tx2")])

        transactions = manager.execute(state)

        # Verify delegation
        manager.aging_system.execute.assert_called_once_with(state)
        manager.birth_system.execute.assert_called_once_with(state)
        manager.death_system.execute.assert_called_once_with(state)

        # Verify transaction aggregation
        assert len(transactions) == 2
        assert transactions[0].id == "tx1"
        assert transactions[1].id == "tx2"

        # Verify registry update
        manager.agent_registry.set_state.assert_called_once_with(state)
