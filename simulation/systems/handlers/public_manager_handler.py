from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm

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

        trade_value = tx.quantity * tx.price
        pm = context.public_manager

        if not pm:
            context.logger.error("PublicManagerHandler: PublicManager not found in context.")
            return False

        # 1. Financial Settlement
        # Public Manager usually doesn't participate in standard SettlementSystem ledger?
        # TransactionManager logic used direct withdraw/deposit_revenue.

        try:
            # Manually withdraw from buyer
            # We should check if buyer has funds first or handle exception?
            if hasattr(buyer, "withdraw"):
                # Basic check
                assets = getattr(buyer, "assets", 0.0)
                if assets < trade_value:
                     # Attempt seamless? Or fail.
                     # TransactionManager just called withdraw, letting it fail/raise.
                     # We'll rely on withdraw raising error if insufficient.
                     buyer.withdraw(trade_value)

            # Credit PM
            pm.deposit_revenue(trade_value)
            pm.confirm_sale(tx.item_id, tx.quantity)

        except Exception as e:
            context.logger.error(f"PUBLIC_MANAGER transaction failed: {e}")
            return False

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
             buyer.finance.record_expense(trade_value)

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
                if is_raw_material and isinstance(buyer, Firm):
                    buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity
                elif hasattr(buyer, "inventory"):
                     buyer.inventory[tx.item_id] = buyer.inventory.get(tx.item_id, 0.0) + tx.quantity

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
                     if hasattr(buyer, "owned_properties"):
                         buyer.owned_properties.append(unit_id)
             except:
                 pass

        elif tx_type == "stock" or tx.item_id.startswith("stock_"):
             # Stock update
             try:
                 firm_id = int(tx.item_id.split("_")[1])
                 if isinstance(buyer, Household):
                    buyer.shares_owned[firm_id] = buyer.shares_owned.get(firm_id, 0) + tx.quantity
                    if hasattr(buyer, "portfolio"):
                        buyer.portfolio.add(firm_id, tx.quantity, tx.price)
                        buyer.shares_owned[firm_id] = buyer.portfolio.holdings[firm_id].quantity
                 # Registry update
                 if context.stock_market:
                     if hasattr(buyer, "portfolio") and firm_id in buyer.portfolio.holdings:
                         context.stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)
             except:
                 pass
