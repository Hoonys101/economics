from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction

logger = logging.getLogger(__name__)

class EmergencyTransactionHandler(ITransactionHandler):
    """
    Handles 'emergency_buy' transactions.
    Fast purchase logic with immediate inventory update.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        trade_value = tx.quantity * tx.price

        # 1. Execute Settlement (Transfer)
        success = context.settlement_system.transfer(
            buyer, seller, trade_value, "emergency_buy"
        )

        # 2. Apply Side-Effects
        if success:
             # Registry logic: buyer.inventory[tx.item_id] += tx.quantity
             if hasattr(buyer, "inventory"):
                 buyer.inventory[tx.item_id] = buyer.inventory.get(tx.item_id, 0.0) + tx.quantity

        return success is not None
