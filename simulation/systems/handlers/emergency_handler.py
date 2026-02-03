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
        trade_value = round(tx.quantity * tx.price, 2)

        credits: List[Tuple[Any, float, str]] = []

        # Seller Credit
        credits.append((seller, trade_value, f"emergency_buy:{tx.item_id}"))

        intents = []
        if context.taxation_system:
            intents = context.taxation_system.calculate_tax_intents(tx, buyer, seller, context.government, context.market_data)
            for intent in intents:
                credits.append((context.government, intent.amount, intent.reason))

        # 1. Execute Settlement (Atomic)
        success = context.settlement_system.settle_atomic(buyer, credits, context.time)

        # 2. Apply Side-Effects
        if success:
             # Registry logic: buyer.inventory[tx.item_id] += tx.quantity
             if hasattr(buyer, "inventory"):
                 buyer.inventory[tx.item_id] = buyer.inventory.get(tx.item_id, 0.0) + tx.quantity

             # Record Revenue (Tax)
             if context.government:
                 for intent in intents:
                    context.government.record_revenue({
                         "success": True,
                         "amount_collected": intent.amount,
                         "tax_type": intent.reason,
                         "payer_id": intent.payer_id,
                         "payee_id": intent.payee_id,
                         "error_message": None
                    })

        return success
