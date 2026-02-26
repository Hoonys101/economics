import pytest
from unittest.mock import MagicMock
from simulation.registries.estate_registry import EstateRegistry
from simulation.models import Transaction
from modules.simulation.api import IAgent
from modules.finance.api import IFinancialAgent
from modules.finance.transaction.api import TransactionResultDTO
from modules.system.api import DEFAULT_CURRENCY

class TestEstateRegistry:

    def test_intercept_transaction_executes_transfer(self):
        registry = EstateRegistry()

        # Mock Settlement System
        mock_settlement_system = MagicMock()
        mock_engine = MagicMock()
        mock_settlement_system._get_engine.return_value = mock_engine

        # Mock Transaction Result
        mock_engine.process_transaction.return_value = TransactionResultDTO(
            transaction=MagicMock(),
            status='COMPLETED',
            message="Success",
            timestamp=10.0
        )

        # Setup Dead Agent
        dead_agent = MagicMock(spec=IFinancialAgent)
        dead_agent.id = 666
        # Set balance to 0 to skip distribution but verify interception
        dead_agent.balance_pennies = 0
        dead_agent.get_balance.return_value = 0
        registry.add_to_estate(dead_agent)

        # Setup Transaction
        tx = Transaction(
            buyer_id=101,
            seller_id=666,
            item_id="currency",
            quantity=1.0,
            price=1.0,
            total_pennies=100,
            market_id="settlement",
            transaction_type="transfer",
            time=10,
            currency=DEFAULT_CURRENCY
        )

        # Execute Interception
        result_tx = registry.intercept_transaction(tx, mock_settlement_system)

        # Verify
        assert result_tx is not None
        assert result_tx.metadata['intercepted'] is True

        # Verify Engine Call (Transfer Execution)
        mock_engine.process_transaction.assert_called_once()
        args, kwargs = mock_engine.process_transaction.call_args
        assert kwargs['destination_account_id'] == '666'
        assert kwargs['amount'] == 100

    def test_intercept_transaction_triggers_distribution_to_heir(self):
        registry = EstateRegistry()

        # Mock Settlement System
        mock_settlement_system = MagicMock()
        mock_engine = MagicMock()
        mock_settlement_system._get_engine.return_value = mock_engine
        mock_engine.process_transaction.return_value = TransactionResultDTO(
            transaction=MagicMock(),
            status='COMPLETED',
            message="Success",
            timestamp=10.0
        )

        # Setup Dead Agent with Balance and Heir
        dead_agent = MagicMock(spec=IFinancialAgent)
        dead_agent.id = 666
        dead_agent.balance_pennies = 500
        dead_agent.get_balance.return_value = 500
        dead_agent.children_ids = [777] # Heir ID
        registry.add_to_estate(dead_agent)

        # Setup Heir Agent in Registry
        heir_agent = MagicMock(spec=IFinancialAgent)
        heir_agent.id = 777
        mock_settlement_system.agent_registry.get_agent.return_value = heir_agent

        # Setup Transaction (Incoming 100)
        tx = Transaction(
            buyer_id=101,
            seller_id=666,
            item_id="currency",
            quantity=1.0,
            price=1.0,
            total_pennies=100,
            market_id="settlement",
            transaction_type="transfer",
            time=10,
            currency=DEFAULT_CURRENCY
        )

        # Execute Interception
        registry.intercept_transaction(tx, mock_settlement_system)

        # Verify Distribution Call
        # EstateRegistry should call settlement_system.transfer to move funds to heir
        # It transfers the CURRENT balance (500)
        mock_settlement_system.transfer.assert_called_once()
        args, kwargs = mock_settlement_system.transfer.call_args
        assert kwargs['debit_agent'] == dead_agent
        assert kwargs['credit_agent'] == heir_agent
        assert kwargs['amount'] == 500
        assert kwargs['memo'] == "inheritance_distribution"
