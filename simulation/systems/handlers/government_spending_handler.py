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
        trade_value = tx.total_pennies

        # infrastructure_spending: Buyer is Government. Seller is typically System/Reflux or Agent.
        # TransactionProcessor logic: success = settlement.transfer(buyer, seller, trade_value, "infrastructure_spending")

        success = context.settlement_system.transfer(
            buyer, seller, trade_value, tx.transaction_type
        )

        return success is not None

    def rollback(self, tx: Transaction, context: TransactionContext) -> bool:
        """
        Reverses government spending.
        """
        trade_value = tx.total_pennies

        # Original: Gov (Buyer) -> Agent (Seller)
        # Rollback: Agent (Seller) -> Gov (Buyer)

        source = context.agents.get(tx.buyer_id) or context.inactive_agents.get(tx.buyer_id)
        destination = context.agents.get(tx.seller_id) or context.inactive_agents.get(tx.seller_id)

        if not source or not destination:
             return False

        success = context.settlement_system.transfer(destination, source, int(trade_value), f"rollback_gov_spend:{tx.transaction_type}:{tx.id}")
        return success is not None
