from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction

logger = logging.getLogger(__name__)

class EmergencyTransactionHandler(ITransactionHandler):
    """
    Handles 'emergency_buy' transactions.
    Fast purchase logic with immediate inventory update.
    Refactored to enforce sales tax atomicity (Audit).
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        if not buyer or not seller:
             logger.warning(f"Transaction failed: Buyer ({tx.buyer_id}) or Seller ({tx.seller_id}) not found.")
             return False

        trade_value = round(tx.quantity * tx.price, 2)

        # 1. Prepare Settlement (Calculate tax intents)
        # Note: TaxationSystem must be updated to recognize 'emergency_buy'
        intents = context.taxation_system.calculate_tax_intents(
            tx, buyer, seller, context.government, context.market_data
        )

        credits: List[Tuple[Any, float, str]] = []

        # 1a. Main Trade Credit (Seller)
        credits.append((seller, trade_value, "emergency_buy"))

        # 1b. Tax Credits (Government)
        for intent in intents:
            credits.append((context.government, intent.amount, intent.reason))

        # 2. Execute Settlement (Atomic)
        # This ensures Buyer pays Trade + Tax, or nothing happens.
        settlement_success = context.settlement_system.settle_atomic(buyer, credits, context.time)

        # 3. Apply Side-Effects
        if settlement_success:
             # Record Revenue for Tax Purposes (Government)
             for intent in intents:
                context.government.record_revenue({
                     "success": True,
                     "amount_collected": intent.amount,
                     "tax_type": intent.reason,
                     "payer_id": intent.payer_id,
                     "payee_id": intent.payee_id,
                     "error_message": None
                })

             # Registry logic: buyer.inventory[tx.item_id] += tx.quantity
             if hasattr(buyer, "inventory"):
                 buyer.inventory[tx.item_id] = buyer.inventory.get(tx.item_id, 0.0) + tx.quantity

        return settlement_success
