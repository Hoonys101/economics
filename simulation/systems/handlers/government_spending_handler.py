from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction

logger = logging.getLogger(__name__)

class GovernmentSpendingHandler(ITransactionHandler):
    """
    Handles 'infrastructure_spending' and other government spending transactions.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        trade_value = tx.quantity * tx.price

        # infrastructure_spending: Buyer is Government. Seller is typically System/Reflux or Agent.
        # TransactionProcessor logic: success = settlement.transfer(buyer, seller, trade_value, "infrastructure_spending")

        success = context.settlement_system.transfer(
            buyer, seller, trade_value, tx.transaction_type
        )

        return success is not None
