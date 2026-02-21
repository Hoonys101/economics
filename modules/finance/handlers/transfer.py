from typing import Any
from modules.finance.api import ITransactionHandler
from modules.finance.transaction.api import ILedgerEngine, TransactionDTO, TransactionResultDTO

class TransferHandler(ITransactionHandler):
    """
    Handler for basic financial transfers (TransactionType.TRANSFER).
    Wraps the low-level LedgerEngine.
    """
    def __init__(self, ledger_engine: ILedgerEngine):
        self.ledger_engine = ledger_engine

    def validate(self, request: Any, context: Any) -> bool:
        if not isinstance(request, TransactionDTO):
            return False
        return True

    def execute(self, request: Any, context: Any) -> TransactionResultDTO:
        if not isinstance(request, TransactionDTO):
             raise ValueError("Invalid request type for TransferHandler. Expected TransactionDTO.")

        # Delegate to LedgerEngine
        return self.ledger_engine.process_transaction(
            source_account_id=request.source_account_id,
            destination_account_id=request.destination_account_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description
        )

    def rollback(self, transaction_id: str, context: Any) -> bool:
        # TODO: Implement rollback
        return False
