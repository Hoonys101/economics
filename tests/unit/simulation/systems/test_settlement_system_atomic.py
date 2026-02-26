import pytest
from unittest.mock import MagicMock, PropertyMock, patch
from simulation.systems.settlement_system import SettlementSystem
from simulation.registries.estate_registry import EstateRegistry
from simulation.models import Transaction
from modules.simulation.api import IAgent
from modules.finance.api import IFinancialEntity, IFinancialAgent
from modules.finance.transaction.api import TransactionResultDTO, TransactionDTO
from modules.system.api import DEFAULT_CURRENCY

class TestSettlementSystemAtomic:

    @pytest.fixture
    def setup_system(self):
        # Create mocks
        mock_agent_registry = MagicMock()
        mock_estate_registry = MagicMock(spec=EstateRegistry)
        mock_metrics_service = MagicMock()

        # Instantiate SettlementSystem
        system = SettlementSystem(
            agent_registry=mock_agent_registry,
            estate_registry=mock_estate_registry,
            metrics_service=mock_metrics_service
        )

        return system, mock_agent_registry, mock_estate_registry

    def test_transaction_to_dead_agent_intercepted(self, setup_system):
        system, mock_agent_registry, mock_estate_registry = setup_system

        # Setup Agents
        alive_agent = MagicMock(spec=IFinancialAgent)
        alive_agent.id = 101
        # Mock balance_pennies property for IFinancialEntity check
        type(alive_agent).balance_pennies = PropertyMock(return_value=1000)
        # Also mock get_balance for IFinancialAgent check fallback
        alive_agent.get_balance.return_value = 1000

        dead_agent = MagicMock(spec=IFinancialAgent)
        dead_agent.id = 666
        type(dead_agent).balance_pennies = PropertyMock(return_value=0)
        dead_agent.get_balance.return_value = 0

        # Dead agent is NOT in active registry (returns None or raises)
        mock_agent_registry.get_agent.side_effect = lambda agent_id: alive_agent if agent_id == 101 else None

        # Dead agent IS in estate registry
        mock_estate_registry.get_agent.side_effect = lambda agent_id: dead_agent if agent_id == 666 else None

        # Mock Engine execution (mock _get_engine)
        mock_engine = MagicMock()

        tx_dto = TransactionDTO(
            transaction_id='tx_123',
            source_account_id=str(alive_agent.id),
            destination_account_id=str(dead_agent.id),
            amount=100,
            currency=DEFAULT_CURRENCY,
            description="Test Transfer to Dead Agent"
        )

        mock_engine.process_transaction.return_value = TransactionResultDTO(
            transaction=tx_dto,
            status='COMPLETED',
            message="Success",
            timestamp=10.0
        )
        system._get_engine = MagicMock(return_value=mock_engine)

        # Execute Transfer
        result = system.transfer(
            debit_agent=alive_agent,
            credit_agent=dead_agent,
            amount=100,
            memo="Test Transfer to Dead Agent",
            tick=10
        )

        # Verification
        # 1. Verify intercept_transaction was called
        assert mock_estate_registry.intercept_transaction.called

        # 2. Verify arguments passed to intercept_transaction
        call_args = mock_estate_registry.intercept_transaction.call_args
        assert call_args is not None
        tx_arg = call_args[0][0] # The 'tx' object
        assert isinstance(tx_arg, Transaction)
        assert tx_arg.buyer_id == alive_agent.id
        assert tx_arg.seller_id == dead_agent.id
        assert tx_arg.total_pennies == 100
