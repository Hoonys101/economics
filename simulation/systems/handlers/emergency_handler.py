from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from modules.simulation.api import IInventoryHandler

logger = logging.getLogger(__name__)

class EmergencyTransactionHandler(ITransactionHandler):
    """
    Handles 'emergency_buy' transactions.
    Fast purchase logic with immediate inventory update.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        trade_value = int(tx.quantity * tx.price) # MIGRATION: Int pennies

        credits: List[Tuple[Any, int, str]] = []

        # Seller Credit
        credits.append((seller, trade_value, f"emergency_buy:{tx.item_id}"))

        intents = []
        if context.taxation_system:
            intents = context.taxation_system.calculate_tax_intents(tx, buyer, seller, context.government, context.market_data)
            for intent in intents:
                # Ensure intent.amount is int
                credits.append((context.government, int(intent.amount), intent.reason))

        # 1. Execute Settlement (Atomic)
        success = context.settlement_system.settle_atomic(buyer, credits, context.time)

        # 2. Apply Side-Effects
        if success:
             # Registry logic: buyer.add_item(...)
             if isinstance(buyer, IInventoryHandler):
                 buyer.add_item(tx.item_id, tx.quantity, quality=1.0)
             else:
                 logger.warning(f"EMERGENCY_HANDLER_WARN | Buyer {buyer.id} does not implement IInventoryHandler")

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
