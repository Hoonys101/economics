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
        mock_logger = MagicMock()

        # Instantiate SettlementSystem
        system = SettlementSystem(
            agent_registry=mock_agent_registry,
            estate_registry=mock_estate_registry,
            metrics_service=mock_metrics_service,
            logger=mock_logger
        )

        return system, mock_agent_registry, mock_estate_registry, mock_logger

    def test_transaction_to_dead_agent_triggers_post_distribution(self, setup_system):
        system, mock_agent_registry, mock_estate_registry, mock_logger = setup_system

        # Setup Agents
        alive_agent = MagicMock(spec=IFinancialAgent)
        alive_agent.id = 101
        type(alive_agent).balance_pennies = PropertyMock(return_value=1000)
        alive_agent.get_balance.return_value = 1000

        dead_agent = MagicMock(spec=IFinancialAgent)
        dead_agent.id = 666
        type(dead_agent).balance_pennies = PropertyMock(return_value=0)
        dead_agent.get_balance.return_value = 0

        # Dead agent IS in estate registry
        mock_estate_registry.get_agent.side_effect = lambda agent_id: dead_agent if agent_id == 666 else None

        # Mock Distribution Return (Ghost Transactions)
        # Assuming we return 1 transaction (inheritance)
        ghost_tx = MagicMock(spec=Transaction)
        mock_estate_registry.process_estate_distribution.return_value = [ghost_tx]

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

        # Engine execution MUST succeed for post-hook to run
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

        # 1. Verify Transaction was PROCESSED normally (Success)
        assert result is not None
        mock_engine.process_transaction.assert_called_once()

        # 2. Verify Post-Hook: process_estate_distribution was called
        assert mock_estate_registry.process_estate_distribution.called

        # 3. Verify arguments (including TICK)
        call_args = mock_estate_registry.process_estate_distribution.call_args
        assert call_args is not None
        # Args: (agent, settlement_system, tick)
        agent_arg = call_args[0][0]
        sys_arg = call_args[0][1]
        tick_arg = call_args[0][2]

        assert agent_arg == dead_agent
        assert sys_arg == system
        assert tick_arg == 10 # Verify tick propagation

        # 4. Verify Ghost Transaction Logging (Interim Fix)
        mock_logger.info.assert_any_call("ESTATE_DISTRIBUTION_EFFECT: Generated 1 side-effect transactions.")
