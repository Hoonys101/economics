from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm
from modules.system.api import DEFAULT_CURRENCY
from modules.simulation.api import IInventoryHandler
from modules.finance.api import IFinancialAgent

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

        # Integer Precision: Calculate trade value in pennies
        trade_value = int(tx.quantity * tx.price)

        # 1. Prepare Settlement (Calculate tax intents)
        # Assuming taxation_system is available in context
        intents = context.taxation_system.calculate_tax_intents(tx, buyer, seller, context.government, context.market_data)

        credits: List[Tuple[Any, int, str]] = []

        # 1a. Main Trade Credit (Seller)
        credits.append((seller, trade_value, f"goods_trade:{tx.item_id}"))

        # 1b. Tax Credits (Government)
        # Initialize total_cost (from buyer perspective) with base trade value
        total_cost = trade_value

        for intent in intents:
            # Tax amounts should be int from TaxationSystem
            amount_int = int(intent.amount)
            credits.append((context.government, amount_int, intent.reason))
            if intent.payer_id == buyer.id:
                total_cost += amount_int

        # Ensure total_cost is clean
        total_cost = int(total_cost)

        # Solvency Check (Legacy compatibility)
        if hasattr(buyer, 'check_solvency'):
            tx_currency = getattr(tx, 'currency', DEFAULT_CURRENCY)

            if isinstance(buyer, IFinancialAgent):
                check_val = buyer.get_balance(tx_currency)
            else:
                current_assets = buyer.assets
                # TD-024: Handle multi-currency assets safely
                if isinstance(current_assets, dict):
                     check_val = current_assets.get(tx_currency, 0.0)
                else:
                     check_val = float(current_assets)

            if check_val < total_cost:
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
            if isinstance(seller, IInventoryHandler):
                seller.remove_item(tx.item_id, tx.quantity)
            else:
                 logger.warning(f"GOODS_HANDLER_WARN | Seller {seller.id} does not implement IInventoryHandler")

            # Buyer Inventory
            is_raw_material = tx.item_id in getattr(config, "RAW_MATERIAL_SECTORS", [])
            tx_quality = tx.quality if hasattr(tx, 'quality') else 1.0

            if is_raw_material and isinstance(buyer, Firm):
                buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity
            elif isinstance(buyer, IInventoryHandler):
                buyer.add_item(tx.item_id, tx.quantity, quality=tx_quality)
            else:
                logger.warning(f"GOODS_HANDLER_WARN | Buyer {buyer.id} does not implement IInventoryHandler")

        # 2. Seller Financial Records (Revenue)
        if isinstance(seller, Firm):
            if hasattr(seller, 'record_revenue'):
                seller.record_revenue(trade_value)

            # Service Firms track volume
            if hasattr(seller, 'sales_volume_this_tick'):
                seller.sales_volume_this_tick += tx.quantity

            # WO-157: Record Sale for Velocity Tracking
            if hasattr(seller, 'record_sale'):
                seller.record_sale(tx.item_id, tx.quantity, context.time)

        # 3. Buyer Financial Records (Expense) - WO-124 Fix
        if isinstance(buyer, Firm):
            if hasattr(buyer, 'record_expense'):
                buyer.record_expense(buyer_total_cost)

        # 4. Household Consumption Tracking
        if isinstance(buyer, Household):
            if not is_service:
                # Use encapsulated method to avoid AttributeError on read-only properties
                is_food = (tx.item_id == "basic_food")
                if hasattr(buyer, "record_consumption"):
                    buyer.record_consumption(tx.quantity, is_food=is_food)
