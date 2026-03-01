import pytest
from unittest.mock import MagicMock
from modules.finance.handlers.transfer import TransferHandler
from modules.finance.transaction.api import TransactionDTO, TransactionResultDTO

class TestTransferHandler:
    def test_rollback_with_valid_context(self):
        # Setup
        mock_ledger_engine = MagicMock()
        handler = TransferHandler(mock_ledger_engine)

        tx_dto = TransactionDTO(
            transaction_id="orig_tx_123",
            source_account_id="source_1",
            destination_account_id="dest_1",
            amount=1000,
            currency="USD",
            description="Original Transfer"
        )

        # Mock successful rollback transaction
        mock_result = TransactionResultDTO(
            transaction=MagicMock(),
            status='COMPLETED',
            message="Rollback successful",
            timestamp=123.0
        )
        mock_ledger_engine.process_transaction.return_value = mock_result

        # Execute
        result = handler.rollback(transaction_id="rollback_tx_123", context=tx_dto)

        # Verify
        assert result is True
        mock_ledger_engine.process_transaction.assert_called_once_with(
            source_account_id="dest_1",
            destination_account_id="source_1",
            amount=1000,
            currency="USD",
            description="ROLLBACK of rollback_tx_123"
        )

    def test_rollback_with_failed_ledger(self):
        # Setup
        mock_ledger_engine = MagicMock()
        handler = TransferHandler(mock_ledger_engine)

        tx_dto = TransactionDTO(
            transaction_id="orig_tx_123",
            source_account_id="source_1",
            destination_account_id="dest_1",
            amount=1000,
            currency="USD",
            description="Original Transfer"
        )

        # Mock failed rollback transaction
        mock_result = TransactionResultDTO(
            transaction=MagicMock(),
            status='FAILED',
            message="Rollback failed",
            timestamp=123.0
        )
        mock_ledger_engine.process_transaction.return_value = mock_result

        # Execute
        result = handler.rollback(transaction_id="rollback_tx_123", context=tx_dto)

        # Verify
        assert result is False
        mock_ledger_engine.process_transaction.assert_called_once()

    def test_rollback_with_invalid_context(self):
        # Setup
        mock_ledger_engine = MagicMock()
        handler = TransferHandler(mock_ledger_engine)

        # Execute with non-TransactionDTO context
        result = handler.rollback(transaction_id="rollback_tx_123", context={"some": "dict"})

        # Verify
        assert result is False
        mock_ledger_engine.process_transaction.assert_not_called()

    def test_rollback_with_exception(self):
        # Setup
        mock_ledger_engine = MagicMock()
        handler = TransferHandler(mock_ledger_engine)

        tx_dto = TransactionDTO(
            transaction_id="orig_tx_123",
            source_account_id="source_1",
            destination_account_id="dest_1",
            amount=1000,
            currency="USD",
            description="Original Transfer"
        )

        # Mock exception during rollback
        mock_ledger_engine.process_transaction.side_effect = Exception("DB error")

        # Execute
        result = handler.rollback(transaction_id="rollback_tx_123", context=tx_dto)

        # Verify
        assert result is False
        mock_ledger_engine.process_transaction.assert_called_once()
