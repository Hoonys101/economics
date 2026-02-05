from typing import Any, List, Tuple, Dict
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class EscheatmentHandler(ITransactionHandler):
    """
    Handles 'escheatment' transactions.
    Transfers all remaining assets from a deceased/liquidated agent to the Government.
    Enforces zero-sum integrity.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        # Buyer: Agent (Deceased/Closed)
        # Seller: Government (usually)

        # TD-171: Use dynamic asset balance instead of static transaction price
        escheatment_amount_raw = buyer.assets
        escheatment_amount = 0.0

        if isinstance(escheatment_amount_raw, dict):
            escheatment_amount = escheatment_amount_raw.get(DEFAULT_CURRENCY, 0.0)
        else:
            try:
                escheatment_amount = float(escheatment_amount_raw)
            except (ValueError, TypeError):
                escheatment_amount = 0.0

        if escheatment_amount <= 0:
            return True # No assets to transfer, consider success

        gov = context.government
        credits = [(gov, escheatment_amount, "escheatment")]

        success = context.settlement_system.settle_atomic(buyer, credits, context.time)

        if success:
              gov.record_revenue({
                     "success": True,
                     "amount_collected": escheatment_amount,
                     "tax_type": "escheatment",
                     "payer_id": buyer.id,
                     "payee_id": gov.id,
                     "error_message": None
                 })

        return success
