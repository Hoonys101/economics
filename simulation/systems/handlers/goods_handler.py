from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm

logger = logging.getLogger(__name__)

class GoodsTransactionHandler(ITransactionHandler):
    """
    Handles 'goods' transactions (Purchases & Sales).
    Enforces atomic settlement (Trade + Sales Tax).
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        if not buyer or not seller:
            logger.warning(f"Transaction failed: Buyer ({tx.buyer_id}) or Seller ({tx.seller_id}) not found.")
            return False

        # Prevent floating point pollution by rounding to 2 decimal places (cents)
        trade_value = round(tx.quantity * tx.price, 2)

        # 1. Prepare Settlement (Calculate tax intents)
        # Assuming taxation_system is available in context
        intents = context.taxation_system.calculate_tax_intents(tx, buyer, seller, context.government, context.market_data)

        credits: List[Tuple[Any, float, str]] = []

        # 1a. Main Trade Credit (Seller)
        credits.append((seller, trade_value, f"goods_trade:{tx.item_id}"))

        # 1b. Tax Credits (Government)
        # Initialize total_cost (from buyer perspective) with base trade value
        total_cost = trade_value

        for intent in intents:
            # Tax amounts are already rounded by TaxationSystem
            credits.append((context.government, intent.amount, intent.reason))
            if intent.payer_id == buyer.id:
                total_cost += intent.amount

        # Ensure total_cost is clean (though sum of rounded values should be okay, float sum can drift)
        total_cost = round(total_cost, 2)

        # Solvency Check (Legacy compatibility)
        if hasattr(buyer, 'check_solvency'):
            if buyer.assets < total_cost:
                buyer.check_solvency(context.government)

        # 2. Execute Settlement (Atomic)
        # SettlementSystem.settle_atomic(debit_agent, credits_list, tick)
        settlement_success = context.settlement_system.settle_atomic(buyer, credits, context.time)

        # 3. Apply Side-Effects (Only on success)
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

            # Update Inventories, Consumption, etc. (Migrated from TransactionProcessor & Registry)
            self._apply_goods_effects(tx, buyer, seller, trade_value, total_cost, context)

        return settlement_success

    def _apply_goods_effects(self, tx: Transaction, buyer: Any, seller: Any, trade_value: float, buyer_total_cost: float, context: TransactionContext):
        """
        Applies non-financial side effects after successful settlement.
        """
        # Retrieve Good Info
        # context.config_module likely has GOODS dict directly or via property
        config = context.config_module
        good_info = getattr(config, "GOODS", {}).get(tx.item_id, {})
        is_service = good_info.get("is_service", False)

        # 1. Buyer Logic
        if is_service:
            if isinstance(buyer, Household):
                buyer.consume(tx.item_id, tx.quantity, context.time)
        else:
            # Physical Goods: Update Inventory
            # Seller Inventory
            if hasattr(seller, "inventory"):
                 seller.inventory[tx.item_id] = max(0, seller.inventory.get(tx.item_id, 0) - tx.quantity)

            # Buyer Inventory
            is_raw_material = tx.item_id in getattr(config, "RAW_MATERIAL_SECTORS", [])

            if is_raw_material and isinstance(buyer, Firm):
                buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity
            elif hasattr(buyer, "inventory"):
                current_qty = buyer.inventory.get(tx.item_id, 0)
                existing_quality = buyer.inventory_quality.get(tx.item_id, 1.0)
                tx_quality = tx.quality if hasattr(tx, 'quality') else 1.0
                total_new_qty = current_qty + tx.quantity

                if total_new_qty > 0:
                    new_avg_quality = ((current_qty * existing_quality) + (tx.quantity * tx_quality)) / total_new_qty
                    buyer.inventory_quality[tx.item_id] = new_avg_quality

                buyer.inventory[tx.item_id] = total_new_qty

        # 2. Seller Financial Records (Revenue)
        if isinstance(seller, Firm):
            seller.finance.record_revenue(trade_value)
            seller.finance.sales_volume_this_tick += tx.quantity

            # WO-157: Record Sale for Velocity Tracking
            if hasattr(seller, 'record_sale'):
                seller.record_sale(tx.item_id, tx.quantity, context.time)

        # 3. Buyer Financial Records (Expense) - WO-124 Fix
        if isinstance(buyer, Firm):
            buyer.finance.record_expense(buyer_total_cost)

        # 4. Household Consumption Tracking
        if isinstance(buyer, Household):
            if not is_service:
                # Use encapsulated method to avoid AttributeError on read-only properties
                is_food = (tx.item_id == "basic_food")
                if hasattr(buyer, "record_consumption"):
                    buyer.record_consumption(tx.quantity, is_food=is_food)
