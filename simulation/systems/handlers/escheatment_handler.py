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
        subtype = tx.metadata.get('subtype')

        if subtype == 'ASSET_BUYOUT':
            # Phase A: PublicManager (Buyer) buys assets from Bankrupt Agent (Seller)
            # PM injects liquidity. Soft Budget Constraint applies to PM.
            amount = tx.total_pennies
            if amount <= 0:
                return True

            credits = [(seller, amount, "asset_buyout")]
            # PM pays Seller
            success = context.settlement_system.settle_atomic(buyer, credits, context.time)
            return success

        # Phase C: Residual Escheatment (Cleanup)
        # Buyer: Agent (Deceased/Closed)
        # Seller: Government

        # Get actual balance from SSoT
        balance = context.settlement_system.get_balance(buyer.id, DEFAULT_CURRENCY)

        if balance <= 0:
            return True # No assets to transfer, consider success

        # Use seller (Government) if available, otherwise fallback to context
        gov = seller if seller else context.government

        if gov is None:
            # Should not happen if TransactionProcessor did its job, but safe guard
            logger.error(f"Escheatment failed: No Government agent found. Buyer: {buyer.id}")
            return False

        credits = [(gov, balance, "escheatment")]

        success = context.settlement_system.settle_atomic(buyer, credits, context.time)

        if success:
              gov.record_revenue({
                     "success": True,
                     "amount_collected": balance,
                     "tax_type": "escheatment",
                     "payer_id": buyer.id,
                     "payee_id": gov.id,
                     "error_message": None
                 })

        return success
