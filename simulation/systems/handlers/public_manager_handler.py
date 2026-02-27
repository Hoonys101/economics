from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm
from modules.simulation.api import IInventoryHandler, InventorySlot
from modules.common.interfaces import IInvestor, IPropertyOwner

logger = logging.getLogger(__name__)

class PublicManagerTransactionHandler(ITransactionHandler):
    """
    Handles transactions where the seller is the Public Manager.
    (Phase 3: Public Manager Support)
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        # Seller is Public Manager (passed as 'seller' but usually not in agents dict,
        # so might be None or placeholder if accessed via context.agents["PUBLIC_MANAGER"]).
        # TransactionProcessor dispatch logic should ensure we get here.

        trade_value = tx.total_pennies
        pm = context.public_manager

        if not pm:
            context.logger.error("PublicManagerHandler: PublicManager not found in context.")
            return False

        # 1. Financial Settlement (Atomic)
        # Using SettlementSystem to ensure zero-sum integrity.
        # PublicManager now implements IFinancialEntity.

        success = False
        trade_value = round(trade_value, 2) # Ensure precision

        if tx.transaction_type == "goods" and getattr(context, 'taxation_system', None):
            # TD-233: Calculate Tax Atomically
            intents = context.taxation_system.calculate_tax_intents(tx, buyer, pm, context.government, context.market_data)

            credits: List[Tuple[Any, int, str]] = []
            credits.append((pm, int(trade_value), f"public_sale:{tx.item_id}"))

            # Note: total_cost calculation removed as it's not used here, settle_atomic handles total debit.

            for intent in intents:
                credits.append((context.government, int(intent.amount), intent.reason))

            success = context.settlement_system.settle_atomic(buyer, credits, context.time)

            if success:
                 # Record Revenue
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
        else:
             # Legacy/Non-taxable (e.g. assets)
             success = context.settlement_system.transfer(
                buyer, pm, trade_value, f"public_sale:{tx.item_id}"
             )

        if not success:
            context.logger.error(f"PUBLIC_MANAGER transaction failed: Settlement refused.")
            return False

        # Confirm sale (decrement inventory) on success
        pm.confirm_sale(tx.item_id, tx.quantity)

        # 2. Side-Effects (Ownership/Inventory)
        # We pass seller=None to indicate no seller update is needed (system sale).
        self._apply_pm_effects(tx, buyer, context)

        # 3. Accounting
        # TransactionManager called accounting.record_transaction(tx, buyer, None, trade_value, 0.0).
        # We mimic this.
        if isinstance(buyer, Firm):
             # Record expense?
             # AccountingSystem: "if isinstance(buyer, Firm): ... buyer.finance.record_expense(amount)"
             # for labor/interest. Not strictly for goods in AccountingSystem, but TP fixed it.
             # We should record expense if it's a purchase.
             buyer.record_expense(trade_value, tx.currency)

        return True

    def _apply_pm_effects(self, tx: Transaction, buyer: Any, context: TransactionContext):
        """
        Updates buyer state (Inventory/Ownership) akin to Registry.
        """
        tx_type = tx.transaction_type

        if tx_type == "goods":
             # Inventory / Consumption
            config = context.config_module
            good_info = getattr(config, "GOODS", {}).get(tx.item_id, {})
            is_service = good_info.get("is_service", False)

            if is_service:
                if isinstance(buyer, Household):
                    buyer.consume(tx.item_id, tx.quantity, context.time)
            else:
                is_raw_material = tx.item_id in getattr(config, "RAW_MATERIAL_SECTORS", [])
                if isinstance(buyer, IInventoryHandler):
                     slot = InventorySlot.INPUT if is_raw_material and isinstance(buyer, Firm) else InventorySlot.MAIN
                     buyer.add_item(tx.item_id, tx.quantity, quality=1.0, slot=slot)
                else:
                     logger.warning(f"PUBLIC_MANAGER_WARN | Buyer {buyer.id} does not implement IInventoryHandler")

            if isinstance(buyer, Household):
                if not is_service:
                     buyer.current_consumption += tx.quantity
                     if tx.item_id == "basic_food":
                         buyer.current_food_consumption += tx.quantity

        elif tx.item_id.startswith("real_estate_"):
             # RE update
             try:
                 unit_id = int(tx.item_id.split("_")[2])
                 unit = next((u for u in context.real_estate_units if u.id == unit_id), None)
                 if unit:
                     unit.owner_id = buyer.id
                     if isinstance(buyer, IPropertyOwner):
                         buyer.add_property(unit_id)
             except:
                 pass

        elif tx_type == "stock" or tx.item_id.startswith("stock_"):
             # Stock update
             try:
                 firm_id = int(tx.item_id.split("_")[1])
                 if isinstance(buyer, IInvestor):
                    price_pennies = int(tx.total_pennies / tx.quantity) if tx.quantity > 0 else 0
                    buyer.portfolio.add(firm_id, tx.quantity, price_pennies)
                 # Registry update
                 if context.stock_market:
                     if isinstance(buyer, IInvestor) and firm_id in buyer.portfolio.holdings:
                         context.stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)
             except:
                 pass

    def rollback(self, tx: Transaction, context: TransactionContext) -> bool:
        """
        Reverses a Public Manager sale.
        """
        pm = context.public_manager
        if not pm: return False

        trade_value = tx.total_pennies

        buyer = context.agents.get(tx.buyer_id) or context.inactive_agents.get(tx.buyer_id)
        if not buyer: return False

        # Reverse Money: PM -> Buyer
        success = context.settlement_system.transfer(pm, buyer, int(trade_value), f"rollback_pm_sale:{tx.id}")

        # Reverse Inventory: Buyer -> PM
        # If possible.
        # PM inventory management for 'restock' via rollback is not explicitly exposed.
        # We log warning.
        context.logger.warning(f"Rollback for PM Sale {tx.id} executed (Financial only). Inventory restoration to PM not implemented.")

        return success is not None
