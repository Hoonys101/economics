import pytest
from unittest.mock import MagicMock, Mock
from modules.finance.kernel.ledger import MonetaryLedger, SettlementFailError
from modules.finance.api import ISettlementSystem, IFinancialAgent, IMonetaryAuthority
from simulation.dtos.api import CommandBatchDTO, FinancialTransferDTO, SystemLedgerMutationDTO
from modules.system.api import DEFAULT_CURRENCY
from modules.system.constants import ID_CENTRAL_BANK

class TestMonetaryLedgerBatchExecution:

    @pytest.fixture
    def mock_settlement(self):
        # Use IMonetaryAuthority to allow mint_and_distribute / transfer_and_destroy
        mock = MagicMock(spec=IMonetaryAuthority)
        # Mock agent_registry since it's accessed via hasattr in implementation
        mock.agent_registry = MagicMock()
        return mock

    @pytest.fixture
    def mock_time_provider(self):
        tp = MagicMock()
        tp.time = 100
        # Mock agents dict fallback
        tp.agents = {}
        # Ensure get_agent doesn't exist or returns None to prevent accidental fallback resolution
        del tp.get_agent
        return tp

    @pytest.fixture
    def ledger(self, mock_settlement, mock_time_provider):
        return MonetaryLedger(
            transaction_log=[],
            time_provider=mock_time_provider,
            settlement_system=mock_settlement
        )

    def test_execute_batch_transfer_success(self, ledger, mock_settlement, mock_time_provider):
        # Setup Agents
        agent_a = MagicMock(spec=IFinancialAgent)
        agent_b = MagicMock(spec=IFinancialAgent)

        # Setup Registry Resolution
        mock_registry = mock_settlement.agent_registry
        mock_registry.get_agent.side_effect = lambda id: {1: agent_a, 2: agent_b}.get(id)

        # Setup Batch
        transfer = FinancialTransferDTO(
            source_id=1,
            target_id=2,
            amount_pennies=1000,
            currency=DEFAULT_CURRENCY,
            reason="test_transfer"
        )
        batch = CommandBatchDTO(tick=100, transfers=[transfer])

        # Mock successful transfer
        mock_settlement.transfer.return_value = True

        # Execute
        ledger.execute_batch(batch)

        # Verify
        mock_settlement.transfer.assert_called_once_with(
            debit_agent=agent_a,
            credit_agent=agent_b,
            amount=1000,
            memo="test_transfer",
            tick=100,
            currency=DEFAULT_CURRENCY
        )

    def test_execute_batch_transfer_float_failure(self, ledger):
        # Should fail at DTO construction
        try:
            FinancialTransferDTO(1, 2, 100.5)
            assert False, "Should have raised TypeError"
        except TypeError:
            pass

    def test_execute_batch_mint_success(self, ledger, mock_settlement):
        # Setup Batch
        mutation = SystemLedgerMutationDTO(
            target_id=3,
            amount_pennies=5000,
            reason="stimulus"
        )
        batch = CommandBatchDTO(tick=100, mutations=[mutation])

        # Mock success
        mock_settlement.mint_and_distribute.return_value = True

        # Execute
        ledger.execute_batch(batch)

        # Verify (ID passed directly)
        mock_settlement.mint_and_distribute.assert_called_once_with(
            target_agent_id=3,
            amount=5000,
            tick=100,
            reason="stimulus"
        )

    def test_execute_batch_burn_success(self, ledger, mock_settlement):
        # Setup Agents
        agent_target = MagicMock(spec=IFinancialAgent)
        central_bank = MagicMock(spec=IFinancialAgent)

        # Setup Registry
        mock_registry = mock_settlement.agent_registry
        mock_registry.get_agent.side_effect = lambda id: {4: agent_target, ID_CENTRAL_BANK: central_bank}.get(id)

        # Setup Batch
        mutation = SystemLedgerMutationDTO(
            target_id=4,
            amount_pennies=-2000,
            reason="tax_burn"
        )
        batch = CommandBatchDTO(tick=100, mutations=[mutation])

        # Mock success
        mock_settlement.transfer_and_destroy.return_value = True

        # Execute
        ledger.execute_batch(batch)

        # Verify
        mock_settlement.transfer_and_destroy.assert_called_once_with(
            source=agent_target,
            sink_authority=central_bank,
            amount=2000, # Absolute value
            reason="tax_burn",
            tick=100,
            currency=DEFAULT_CURRENCY
        )

    def test_execute_batch_agent_not_found(self, ledger, mock_settlement):
        # Setup Registry to return None
        mock_registry = mock_settlement.agent_registry
        mock_registry.get_agent.return_value = None

        transfer = FinancialTransferDTO(1, 2, 100)
        batch = CommandBatchDTO(tick=100, transfers=[transfer])

        with pytest.raises(SettlementFailError, match="Agent lookup failed"):
            ledger.execute_batch(batch)
