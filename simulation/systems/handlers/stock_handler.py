from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm

logger = logging.getLogger(__name__)

class StockTransactionHandler(ITransactionHandler):
    """
    Handles 'stock' transactions.
    Direct transfer and Share Registry updates.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        # SSoT: Use total_pennies directly (Strict Schema Enforced)
        trade_value = tx.total_pennies

        # 1. Execute Settlement (Direct Transfer)
        # Stock trades typically don't have sales tax in this simulation model yet.
        settlement_success = context.settlement_system.transfer(buyer, seller, trade_value, f"stock_trade:{tx.item_id}")

        # 2. Apply Side-Effects
        if settlement_success:
            self._apply_stock_effects(tx, buyer, seller, context)

        return settlement_success is not None

    def _apply_stock_effects(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext):
        """
        Updates portfolios and shareholder registries.
        """
        try:
            # item_id format: "stock_{firm_id}"
            firm_id = int(tx.item_id.split("_")[1])
        except (IndexError, ValueError):
            context.logger.error(f"Invalid stock item_id: {tx.item_id}")
            return

        # 1. Seller Holdings
        if hasattr(seller, "portfolio"):
            seller.portfolio.remove(firm_id, tx.quantity)
        elif isinstance(seller, Household) and hasattr(seller, "shares_owned"):
             # Legacy Fallback
            current_shares = seller.shares_owned.get(firm_id, 0)
            seller.shares_owned[firm_id] = max(0, current_shares - tx.quantity)
            if seller.shares_owned[firm_id] <= 0 and firm_id in seller.shares_owned:
                del seller.shares_owned[firm_id]
        elif isinstance(seller, Firm) and seller.id == firm_id:
            # Firm selling its own treasury shares
            seller.treasury_shares = max(0, seller.treasury_shares - tx.quantity)

        # 2. Buyer Holdings
        if hasattr(buyer, "portfolio"):
            # MIGRATION: Calculate acquisition price in pennies from total_pennies
            price_pennies = int(tx.total_pennies / tx.quantity) if tx.quantity > 0 else 0
            buyer.portfolio.add(firm_id, tx.quantity, price_pennies)
        elif isinstance(buyer, Household) and hasattr(buyer, "shares_owned"):
            # Legacy Fallback
            buyer.shares_owned[firm_id] = buyer.shares_owned.get(firm_id, 0) + tx.quantity
        elif isinstance(buyer, Firm) and buyer.id == firm_id:
            # Firm buying back shares (Treasury)
            buyer.treasury_shares += tx.quantity
            buyer.total_shares -= tx.quantity

        # 3. Market Registry (Shareholder List)
        if context.stock_market:
            # Sync Buyer
            if hasattr(buyer, "portfolio") and firm_id in buyer.portfolio.holdings:
                 context.stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)

            # Sync Seller
            if hasattr(seller, "portfolio") and firm_id in seller.portfolio.holdings:
                context.stock_market.update_shareholder(seller.id, firm_id, seller.portfolio.holdings[firm_id].quantity)
            else:
                context.stock_market.update_shareholder(seller.id, firm_id, 0.0)

        context.logger.info(
            f"STOCK_TX | Buyer: {buyer.id}, Seller: {seller.id}, Firm: {firm_id}, Qty: {tx.quantity}, Price: {tx.price}",
            extra={"tick": context.time, "tags": ["stock_market", "transaction"]}
        )
