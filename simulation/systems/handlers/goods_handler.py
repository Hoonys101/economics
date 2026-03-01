from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm
from modules.system.api import DEFAULT_CURRENCY
from modules.simulation.api import IInventoryHandler, InventorySlot
from modules.finance.api import IFinancialAgent, ISolvencyChecker, ISalesTracker, IRevenueTracker, IExpenseTracker, IConsumer, IConsumptionTracker, FloatIncursionError
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
        if isinstance(tx.total_pennies, float):
            raise FloatIncursionError(f"Settlement integrity violation: amount must be int, got float: {tx.total_pennies}.")

        if not isinstance(tx.total_pennies, int):
            raise TypeError(f"Settlement integrity violation: amount must be int, got {type(tx.total_pennies)}.")

        trade_value = tx.total_pennies


        # 1. Prepare Settlement (Calculate tax intents)
        # Assuming taxation_system is available in context
        intents = context.taxation_system.calculate_tax_intents(tx, buyer, seller, context.government, context.market_data)

        credits: List[Tuple[Any, int, str]] = []

        # 1a. Main Trade Credit (Seller)
        credits.append((seller, int(trade_value), f"goods_trade:{tx.item_id}"))

        # 1b. Tax Credits (Government)
        # Initialize total_cost (from buyer perspective) with base trade value
        total_cost = int(trade_value)

        for intent in intents:
            # Tax amounts are already rounded by TaxationSystem and are ints
            amount_int = int(intent.amount)
            credits.append((context.government, amount_int, intent.reason))

            if intent.payer_id == buyer.id:
                total_cost += amount_int

        # Total cost is already clean int sum


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

            if check_val < total_cost:
                buyer.check_solvency(context.government)

        # 2. Execute Settlement (Atomic)
        # SettlementSystem.settle_atomic(debit_agent, credits_list, tick)
        settlement_success = context.settlement_system.settle_atomic(buyer, credits, context.time)

        # 3. Apply Side-Effects (Only on success)
        if settlement_success:
            # Record Revenue for Tax Purposes (Government)
            from modules.finance.dtos import TaxCollectionResult
            for intent in intents:
                context.government.record_revenue(TaxCollectionResult(
                     success=True,
                     amount_collected=intent.amount,
                     tax_type=intent.reason,
                     payer_id=intent.payer_id,
                     payee_id=intent.payee_id,
                     error_message=None
                ))

            # WO-IMPL-LEDGER-HARDENING: Generate Tax Transactions for visibility/exhaustion
            # Since settlement is atomic, we mark these as executed.
            if hasattr(context, "transaction_queue"):
                for intent in intents:
                    tax_tx = Transaction(
                        buyer_id=intent.payer_id,
                        seller_id=intent.payee_id,
                        item_id=f"tax_{intent.reason}",
                        quantity=1,
                        price=intent.amount / 100.0, # Just for display/compat
                        market_id="system",
                        transaction_type="tax",
                        time=context.time,
                        total_pennies=int(intent.amount),
                        metadata={"executed": True, "tax_type": intent.reason}
                    )
                    context.transaction_queue.append(tax_tx)

            # Update Inventories, Consumption, etc. (Migrated from TransactionProcessor & Registry)
            self._apply_goods_effects(tx, buyer, seller, trade_value, total_cost, context)

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
            from simulation.systems.settlement_system import InventorySentry
            with InventorySentry.unlocked():
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
        # TD-SYS-ACCOUNTING-GAP: Skip expense recording for raw materials (Inventory Asset Swap)
        # Expense is recorded upon usage (COGS) in ProductionEngine/FinanceEngine.
        is_raw_material = tx.item_id in getattr(config, "RAW_MATERIAL_SECTORS", [])
        should_record_expense = True

        # Check if buyer is a Firm (has sector) and item is raw material
        if is_raw_material and hasattr(buyer, "sector"):
             should_record_expense = False

        if should_record_expense and isinstance(buyer, IExpenseTracker):
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

    def rollback(self, tx: Transaction, context: TransactionContext) -> bool:
        """
        Reverses a goods transaction.
        Attempts to reverse money flow and inventory.
        """
        trade_value = tx.total_pennies

        source = context.agents.get(tx.buyer_id) or context.inactive_agents.get(tx.buyer_id)
        destination = context.agents.get(tx.seller_id) or context.inactive_agents.get(tx.seller_id)

        if not source or not destination:
            return False

        # 1. Reverse Money (Seller -> Buyer)
        success = context.settlement_system.transfer(destination, source, int(trade_value), f"rollback_goods:{tx.item_id}:{tx.id}")

        # 2. Reverse Tax (Gov -> Buyer)
        # Note: We need to know how much tax was paid. This information is ideally in metadata or recalculated.
        # Recalculating intents:
        if context.taxation_system:
             intents = context.taxation_system.calculate_tax_intents(tx, source, destination, context.government, context.market_data)
             for intent in intents:
                 context.settlement_system.transfer(context.government, source, int(intent.amount), f"rollback_tax:{intent.reason}:{tx.id}")

        # 3. Reverse Inventory (Buyer -> Seller)
        # Only if physical good
        # Assuming we can just move it back.
        # This part is risky if buyer consumed it.
        # For now, we only reverse money as "Goods" rollback is usually for failed atomic sets before consumption triggers.
        # If consumption triggered, we might need to "un-consume" which is hard.

        context.logger.info(f"Rollback for Goods {tx.id} executed (Financial only). Inventory reversal skipped.")

        return success is not None
