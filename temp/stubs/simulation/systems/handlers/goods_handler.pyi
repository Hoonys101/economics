from _typeshed import Incomplete
from modules.finance.utils.currency_math import round_to_pennies as round_to_pennies
from simulation.core_agents import Household as Household
from simulation.firms import Firm as Firm
from simulation.models import Transaction as Transaction
from simulation.systems.api import ITransactionHandler as ITransactionHandler, TransactionContext as TransactionContext
from typing import Any

logger: Incomplete

class GoodsTransactionHandler(ITransactionHandler):
    """
    Handles 'goods' transactions (Purchases & Sales).
    Enforces atomic settlement (Trade + Sales Tax).
    """
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool: ...
    def rollback(self, tx: Transaction, context: TransactionContext) -> bool:
        """
        Reverses a goods transaction.
        Attempts to reverse money flow and inventory.
        """
