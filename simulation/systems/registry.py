from typing import Any, List, Optional, Dict
import logging
from uuid import UUID
from modules.finance.api import LienDTO
from simulation.systems.api import IRegistry
from simulation.models import Transaction
from simulation.core_agents import Household, Skill
from simulation.firms import Firm
from simulation.dtos.api import SimulationState
from modules.simulation.api import IInventoryHandler
from modules.housing.api import IHousingService
from modules.system.constants import (
    TX_LABOR, TX_RESEARCH_LABOR, TX_GOODS, TX_STOCK,
    TX_EMERGENCY_BUY, TX_ASSET_TRANSFER, TX_HOUSING
)

logger = logging.getLogger(__name__)

class Registry(IRegistry):
    """
    Updates non-financial state: Ownership, Inventory, Employment, Contracts.
    Extracted from TransactionProcessor.
    Refactored to delegate housing logic to HousingService.
    """

    def __init__(self, housing_service: Optional[IHousingService] = None, logger: Optional[logging.Logger] = None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.housing_service = housing_service

    def set_real_estate_units(self, units: List[Any]) -> None:
        if self.housing_service:
            self.housing_service.set_real_estate_units(units)

    def update_ownership(self, transaction: Transaction, buyer: Any, seller: Any, state: SimulationState) -> None:
        """
        Updates the registry based on the transaction type.
        """
        tx_type = transaction.transaction_type

        if tx_type in [TX_LABOR, TX_RESEARCH_LABOR]:
            self._handle_labor_registry(transaction, buyer, seller, state)

        elif tx_type == TX_GOODS:
            self._handle_goods_registry(transaction, buyer, seller, state.time, state.config_module)

        elif tx_type == TX_STOCK:
            self._handle_stock_registry(transaction, buyer, seller, state.stock_market, state.time)

        elif tx_type.startswith("real_estate_") or tx_type == TX_HOUSING:
             if self.housing_service:
                 self.housing_service.process_transaction(transaction, state)
             else:
                 self.logger.error("Registry: HousingService not initialized but housing transaction received.")

        elif tx_type == TX_EMERGENCY_BUY:
             self._handle_emergency_buy(transaction, buyer)

        elif tx_type == TX_ASSET_TRANSFER:
             if transaction.item_id.startswith("stock_"):
                 self._handle_stock_registry(transaction, buyer, seller, state.stock_market, state.time)
             elif transaction.item_id.startswith("real_estate_"):
                 if self.housing_service:
                     self.housing_service.process_transaction(transaction, state)
                 else:
                     self.logger.error("Registry: HousingService not initialized but real_estate transaction received.")

    def _handle_labor_registry(self, tx: Transaction, buyer: Any, seller: Any, state: SimulationState):
        """Updates employment status and employer/employee lists."""
        trade_value = tx.quantity * tx.price

        if isinstance(seller, Household):
            # Change Employer Logic
            if seller.is_employed and seller.employer_id is not None and seller.employer_id != buyer.id:
                previous_employer = state.agents.get(seller.employer_id)
                if isinstance(previous_employer, Firm):
                     previous_employer.hr.remove_employee(seller)

            seller.is_employed = True
            seller.employer_id = buyer.id
            seller.current_wage = tx.price # Contract update
            seller.needs["labor_need"] = 0.0 # Fulfilled need

        if isinstance(buyer, Firm):
            if seller not in buyer.hr.employees:
                buyer.hr.hire(seller, tx.price, state.time)
            else:
                 buyer.hr.employee_wages[seller.id] = tx.price

            # Research Labor Special Effect (Productivity)
            # Is this Registry or TechSystem? It modifies Firm state (productivity_factor).
            # Registry updates "Non-financial state". Productivity is state.
            if tx.transaction_type == TX_RESEARCH_LABOR and isinstance(seller, Household):
                research_skill = seller.skills.get("research", Skill("research")).value
                # Config access via state.config_module
                multiplier = getattr(state.config_module, "RND_PRODUCTIVITY_MULTIPLIER", 0.0)
                buyer.productivity_factor += (research_skill * multiplier)

    def _handle_goods_registry(self, tx: Transaction, buyer: Any, seller: Any, current_time: int, config: Any):
        """Updates inventory and consumption counters."""
        good_info = config.GOODS.get(tx.item_id, {})
        is_service = good_info.get("is_service", False)

        # 1. Buyer Consumption / Inventory
        if is_service:
            if isinstance(buyer, Household):
                buyer.consume(tx.item_id, tx.quantity, current_time)
        else:
            # Physical Goods: Update Inventory
            # Seller Inventory
            if isinstance(seller, IInventoryHandler):
                seller.remove_item(tx.item_id, tx.quantity)
            elif isinstance(seller, Household):
                seller.inventory[tx.item_id] = max(0, seller.inventory.get(tx.item_id, 0) - tx.quantity)
            elif hasattr(seller, "inventory"):
                 seller.inventory[tx.item_id] = max(0, seller.inventory.get(tx.item_id, 0) - tx.quantity)

            # Buyer Inventory
            is_raw_material = tx.item_id in getattr(config, "RAW_MATERIAL_SECTORS", [])

            if is_raw_material and isinstance(buyer, Firm):
                buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity
            elif isinstance(buyer, IInventoryHandler):
                 if hasattr(buyer, "inventory_quality"):
                     current_qty = buyer.get_quantity(tx.item_id)
                     existing_quality = buyer.inventory_quality.get(tx.item_id, 1.0)
                     tx_quality = tx.quality if hasattr(tx, 'quality') else 1.0
                     total_new_qty = current_qty + tx.quantity

                     if total_new_qty > 0:
                         new_avg_quality = ((current_qty * existing_quality) + (tx.quantity * tx_quality)) / total_new_qty
                         buyer.inventory_quality[tx.item_id] = new_avg_quality
                 buyer.add_item(tx.item_id, tx.quantity)

            elif isinstance(buyer, Household):
                current_qty = buyer.inventory.get(tx.item_id, 0)
                existing_quality = buyer.inventory_quality.get(tx.item_id, 1.0)
                tx_quality = tx.quality if hasattr(tx, 'quality') else 1.0
                total_new_qty = current_qty + tx.quantity

                if total_new_qty > 0:
                    new_avg_quality = ((current_qty * existing_quality) + (tx.quantity * tx_quality)) / total_new_qty
                    buyer.inventory_quality[tx.item_id] = new_avg_quality

                buyer.inventory[tx.item_id] = total_new_qty
            elif hasattr(buyer, "inventory"):
                current_qty = buyer.inventory.get(tx.item_id, 0)
                existing_quality = buyer.inventory_quality.get(tx.item_id, 1.0)
                tx_quality = tx.quality if hasattr(tx, 'quality') else 1.0
                total_new_qty = current_qty + tx.quantity

                if total_new_qty > 0:
                    new_avg_quality = ((current_qty * existing_quality) + (tx.quantity * tx_quality)) / total_new_qty
                    buyer.inventory_quality[tx.item_id] = new_avg_quality

                buyer.inventory[tx.item_id] = total_new_qty

        # 2. Household Consumption Counters (Used for Utility/Stats)
        if isinstance(buyer, Household):
            if not is_service:
                is_food = (tx.item_id == "basic_food")
                buyer.record_consumption(tx.quantity, is_food=is_food)

    def _handle_stock_registry(self, tx: Transaction, buyer: Any, seller: Any, stock_market: Any, current_time: int):
        """Updates share holdings and market registry."""
        try:
            firm_id = int(tx.item_id.split("_")[1])
        except (IndexError, ValueError):
            self.logger.error(f"Invalid stock item_id: {tx.item_id}")
            return

        # 1. Seller Holdings
        if isinstance(seller, Household):
            # Use portfolio directly. shares_owned is legacy computed property.
            seller.portfolio.remove(firm_id, tx.quantity)
        elif isinstance(seller, Firm) and seller.id == firm_id:
            seller.treasury_shares = max(0, seller.treasury_shares - tx.quantity)
        elif hasattr(seller, "portfolio"):
            seller.portfolio.remove(firm_id, tx.quantity)

        # 2. Buyer Holdings
        if isinstance(buyer, Household):
            buyer.portfolio.add(firm_id, tx.quantity, tx.price)
        elif isinstance(buyer, Firm) and buyer.id == firm_id:
            buyer.treasury_shares += tx.quantity
            buyer.total_shares -= tx.quantity

        # 3. Market Registry (Shareholder List)
        if stock_market:
            # Sync Buyer
            if isinstance(buyer, Household) and firm_id in buyer.portfolio.holdings:
                 stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)
            elif hasattr(buyer, "portfolio") and firm_id in buyer.portfolio.holdings:
                 stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)

            # Sync Seller
            if isinstance(seller, Household) and firm_id in seller.portfolio.holdings:
                stock_market.update_shareholder(seller.id, firm_id, seller.portfolio.holdings[firm_id].quantity)
            elif hasattr(seller, "portfolio") and firm_id in seller.portfolio.holdings:
                stock_market.update_shareholder(seller.id, firm_id, seller.portfolio.holdings[firm_id].quantity)
            else:
                stock_market.update_shareholder(seller.id, firm_id, 0.0)

    def _handle_emergency_buy(self, tx: Transaction, buyer: Any):
        """Updates inventory for emergency buys."""
        if isinstance(buyer, Household):
            buyer.inventory[tx.item_id] = buyer.inventory.get(tx.item_id, 0.0) + tx.quantity
        elif hasattr(buyer, "inventory"):
            buyer.inventory[tx.item_id] = buyer.inventory.get(tx.item_id, 0.0) + tx.quantity
