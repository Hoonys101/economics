from _typeshed import Incomplete
from simulation.models import Transaction as Transaction
from simulation.systems.api import ITransactionHandler as ITransactionHandler, TransactionContext as TransactionContext
from typing import Any

logger: Incomplete

class EmergencyTransactionHandler(ITransactionHandler):
    """
    Handles 'emergency_buy' transactions.
    Fast purchase logic with immediate inventory update.
    """
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool: ...
    def rollback(self, tx: Transaction, context: TransactionContext) -> bool:
        """
        Reverses the effects of an emergency purchase.
        """
