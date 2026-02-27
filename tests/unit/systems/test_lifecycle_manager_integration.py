import pytest
from unittest.mock import MagicMock
from simulation.systems.lifecycle_manager import AgentLifecycleManager
from simulation.dtos.api import SimulationState
from modules.simulation.api import IAgingContext, IBirthContext, IDeathContext

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
        manager.marriage_system.execute = MagicMock(return_value=[])

        transactions = manager.execute(state)

        # Verify delegation
        # Should be called with context adapter, not state directly
        manager.aging_system.execute.assert_called_once()
        args, _ = manager.aging_system.execute.call_args
        assert isinstance(args[0], IAgingContext)
        # Verify the context wraps the correct state (implementation detail of adapter)
        assert args[0]._state == state

        manager.birth_system.execute.assert_called_once()
        args, _ = manager.birth_system.execute.call_args
        assert isinstance(args[0], IBirthContext)
        assert args[0]._state == state

        manager.death_system.execute.assert_called_once()
        args, _ = manager.death_system.execute.call_args
        assert isinstance(args[0], IDeathContext)
        assert args[0]._state == state

        # Verify transaction aggregation
        assert len(transactions) == 2
        assert transactions[0].id == "tx1"
        assert transactions[1].id == "tx2"

        # Verify registry update
        manager.agent_registry.set_state.assert_called_once_with(state)
