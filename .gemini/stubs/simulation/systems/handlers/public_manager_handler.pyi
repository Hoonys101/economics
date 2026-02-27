from _typeshed import Incomplete
from simulation.core_agents import Household as Household
from simulation.firms import Firm as Firm
from simulation.models import Transaction as Transaction
from simulation.systems.api import ITransactionHandler as ITransactionHandler, TransactionContext as TransactionContext
from typing import Any

logger: Incomplete

class PublicManagerTransactionHandler(ITransactionHandler):
    """
    Handles transactions where the seller is the Public Manager.
    (Phase 3: Public Manager Support)
    """
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool: ...
    def rollback(self, tx: Transaction, context: TransactionContext) -> bool:
        """
        Reverses a Public Manager sale.
        """
