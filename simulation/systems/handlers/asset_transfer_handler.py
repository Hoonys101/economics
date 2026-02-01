from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction, RealEstateUnit
from simulation.firms import Firm
from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class AssetTransferHandler(ITransactionHandler):
    """
    Handles 'asset_transfer' transactions (Real Estate, Stock, etc.).
    Updates ownership.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        trade_value = tx.quantity * tx.price

        # 1. Execute Settlement (Direct Transfer)
        settlement_success = context.settlement_system.transfer(
            buyer, seller, trade_value, f"asset_transfer:{tx.item_id}"
        )

        # 2. Apply Side-Effects
        if settlement_success:
            self._apply_asset_effects(tx, buyer, seller, context)

        return settlement_success is not None

    def _apply_asset_effects(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext):
        """
        Updates asset ownership based on item_id.
        """
        if tx.item_id.startswith("real_estate_"):
            self._handle_real_estate(tx, buyer, seller, context)
        elif tx.item_id.startswith("stock_"):
            self._handle_stock(tx, buyer, seller, context)

    def _handle_real_estate(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext):
        try:
            # item_id format: "real_estate_{id}"
            unit_id_str = tx.item_id.split("_")[2]
            unit_id = int(unit_id_str)
            unit = next((u for u in context.real_estate_units if u.id == unit_id), None)

            if unit:
                unit.owner_id = buyer.id
                if hasattr(seller, "owned_properties") and unit_id in seller.owned_properties:
                    seller.owned_properties.remove(unit_id)
                if hasattr(buyer, "owned_properties"):
                    buyer.owned_properties.append(unit_id)

                context.logger.info(f"RE_TX | Unit {unit_id} transferred from {seller.id} to {buyer.id}")
            else:
                context.logger.warning(f"RE_TX_FAIL | Unit {unit_id} not found.")

        except (IndexError, ValueError) as e:
            context.logger.error(f"RE_TX_FAIL | Invalid item_id format: {tx.item_id}. Error: {e}")

    def _handle_stock(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext):
        try:
            firm_id = int(tx.item_id.split("_")[1])
        except (IndexError, ValueError):
            return

        # 1. Seller Holdings
        if isinstance(seller, Household):
            current_shares = seller.shares_owned.get(firm_id, 0)
            seller.shares_owned[firm_id] = max(0, current_shares - tx.quantity)
            if seller.shares_owned[firm_id] <= 0 and firm_id in seller.shares_owned:
                del seller.shares_owned[firm_id]
            if hasattr(seller, "portfolio"):
                seller.portfolio.remove(firm_id, tx.quantity)
        elif isinstance(seller, Firm) and seller.id == firm_id:
            seller.treasury_shares = max(0, seller.treasury_shares - tx.quantity)
        elif hasattr(seller, "portfolio"):
            seller.portfolio.remove(firm_id, tx.quantity)

        # 2. Buyer Holdings
        if isinstance(buyer, Household):
            buyer.shares_owned[firm_id] = buyer.shares_owned.get(firm_id, 0) + tx.quantity
            if hasattr(buyer, "portfolio"):
                buyer.portfolio.add(firm_id, tx.quantity, tx.price)
                buyer.shares_owned[firm_id] = buyer.portfolio.holdings[firm_id].quantity
        elif isinstance(buyer, Firm) and buyer.id == firm_id:
            buyer.treasury_shares += tx.quantity
            buyer.total_shares -= tx.quantity

        # 3. Market Registry
        if context.stock_market:
            if hasattr(buyer, "portfolio") and firm_id in buyer.portfolio.holdings:
                 context.stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)
            if hasattr(seller, "portfolio") and firm_id in seller.portfolio.holdings:
                context.stock_market.update_shareholder(seller.id, firm_id, seller.portfolio.holdings[firm_id].quantity)
            else:
                context.stock_market.update_shareholder(seller.id, firm_id, 0.0)
