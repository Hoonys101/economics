from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm
from modules.system.api import DEFAULT_CURRENCY
from modules.simulation.api import IInventoryHandler, InventorySlot
from modules.finance.api import IFinancialAgent, ISolvencyChecker, ISalesTracker, IRevenueTracker, IExpenseTracker, IConsumer, IConsumptionTracker
from modules.finance.utils.currency_math import round_to_pennies

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

        # SSoT: Use total_pennies directly (Strict Schema Enforced)
        trade_value = tx.total_pennies


        # 1. Prepare Settlement (Calculate tax intents)
        # Assuming taxation_system is available in context
        intents = context.taxation_system.calculate_tax_intents(tx, buyer, seller, context.government, context.market_data)

        credits: List[Tuple[Any, int, str]] = []

        # Calculate Adjustments
        seller_net_proceeds = trade_value
        buyer_total_cost = trade_value

        gov_credits = []

        for intent in intents:
            amount_int = int(intent.amount)
            if amount_int <= 0:
                continue

            # Add to Government Credit List
            gov_credits.append((context.government, amount_int, intent.reason))

            # Adjust Payer side
            if intent.payer_id == buyer.id:
                # Sales Tax (Buyer pays on top)
                buyer_total_cost += amount_int
            elif intent.payer_id == seller.id:
                # VAT / Withholding (Seller pays from proceeds)
                seller_net_proceeds -= amount_int
            else:
                # Default to Buyer if unknown (safe fallback or log warning?)
                # For now, we assume buyer pays extraneous taxes to avoid seller loss
                logger.warning(f"Unknown payer_id {intent.payer_id} in tax intent. Defaulting to Buyer charge.")
                buyer_total_cost += amount_int

        # Safety Check: Seller proceeds cannot be negative
        if seller_net_proceeds < 0:
             logger.error(f"Transaction aborted: Seller tax exceeds trade value. Net: {seller_net_proceeds}")
             return False

        # Construct Final Credits List
        # 1. Seller Credit (Net)
        if seller_net_proceeds > 0:
            credits.append((seller, seller_net_proceeds, f"goods_trade:{tx.item_id}"))

        # 2. Government Credits
        credits.extend(gov_credits)

        # Total Credits sum should equal Buyer's total debit (buyer_total_cost) if seller_net_proceeds calculation is consistent.
        # Check: (Trade - SellerTax) + SellerTax + BuyerTax = Trade + BuyerTax = BuyerCost. Correct.

        # Solvency Check (Legacy compatibility)
        if isinstance(buyer, ISolvencyChecker):
            tx_currency = getattr(tx, 'currency', DEFAULT_CURRENCY)

            if isinstance(buyer, IFinancialAgent):
                check_val = buyer.get_balance(tx_currency)
            else:
                current_assets = buyer.assets
                # TD-024: Handle multi-currency assets safely
                if isinstance(current_assets, dict):
                     check_val = current_assets.get(tx_currency, 0)
                else:
                     check_val = int(current_assets)

            if check_val < buyer_total_cost:
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
            self._apply_goods_effects(tx, buyer, seller, trade_value, buyer_total_cost, context)

        return settlement_success

    def _apply_goods_effects(self, tx: Transaction, buyer: Any, seller: Any, trade_value: int, buyer_total_cost: int, context: TransactionContext):
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
            # Service consumption usually immediate
            if isinstance(buyer, IConsumer):
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

            if isinstance(buyer, IInventoryHandler):
                slot = InventorySlot.INPUT if is_raw_material and isinstance(buyer, Firm) else InventorySlot.MAIN
                buyer.add_item(tx.item_id, tx.quantity, quality=tx_quality, slot=slot)
            else:
                logger.warning(f"GOODS_HANDLER_WARN | Buyer {buyer.id} does not implement IInventoryHandler")

        # 2. Seller Financial Records (Revenue)
        if isinstance(seller, IRevenueTracker):
            seller.record_revenue(trade_value)

        # Service Firms and Firms track volume
        if isinstance(seller, ISalesTracker):
            seller.sales_volume_this_tick += tx.quantity
            # WO-157: Record Sale for Velocity Tracking
            seller.record_sale(tx.item_id, tx.quantity, context.time)

        # 3. Buyer Financial Records (Expense) - WO-124 Fix
        if isinstance(buyer, IExpenseTracker):
            buyer.record_expense(buyer_total_cost)

        # 4. Household Consumption Tracking
        if isinstance(buyer, Household):
            if not is_service:
                is_food = (tx.item_id == "basic_food")
                if isinstance(buyer, IConsumer):
                    buyer.record_consumption(tx.quantity, is_food=is_food)

            # Track Consumption Expenditure (Financial)
            if isinstance(buyer, IConsumptionTracker):
                buyer.add_consumption_expenditure(buyer_total_cost, item_id=tx.item_id)
