from _typeshed import Incomplete
from simulation.core_agents import Household as Household
from simulation.firms import Firm as Firm
from simulation.models import Transaction as Transaction
from simulation.systems.api import ITransactionHandler as ITransactionHandler, TransactionContext as TransactionContext
from typing import Any

logger: Incomplete

class StockTransactionHandler(ITransactionHandler):
    """
    Handles 'stock' transactions.
    Direct transfer and Share Registry updates.
    """
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool: ...
