from typing import Any, List, Optional
import logging
from simulation.systems.api import IRegistry
from simulation.models import Transaction
from simulation.core_agents import Household, Skill
from simulation.firms import Firm
from simulation.dtos.api import SimulationState

logger = logging.getLogger(__name__)

class Registry(IRegistry):
    """
    Updates non-financial state: Ownership, Inventory, Employment, Contracts.
    Extracted from TransactionProcessor.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger if logger else logging.getLogger(__name__)

    def update_ownership(self, transaction: Transaction, buyer: Any, seller: Any, state: SimulationState) -> None:
        """
        Updates the registry based on the transaction type.
        """
        tx_type = transaction.transaction_type

        if tx_type in ["labor", "research_labor"]:
            self._handle_labor_registry(transaction, buyer, seller, state)

        elif tx_type == "goods":
            self._handle_goods_registry(transaction, buyer, seller, state.time, state.config_module)

        elif tx_type == "stock":
            self._handle_stock_registry(transaction, buyer, seller, state.stock_market, state.time)

        elif tx_type.startswith("real_estate_") or tx_type == "housing": # transaction_type might be 'asset_transfer' or 'housing'
            # Check item_id for real_estate prefix if type is generic asset_transfer
            if transaction.item_id.startswith("real_estate_"):
                self._handle_real_estate_registry(transaction, buyer, seller, state.real_estate_units, state.time)
            elif tx_type == "housing":
                self._handle_housing_registry(transaction, buyer, seller, state.real_estate_units, state.time)

        elif tx_type == "emergency_buy":
             self._handle_emergency_buy(transaction, buyer)

        elif tx_type == "asset_transfer":
             if transaction.item_id.startswith("stock_"):
                 self._handle_stock_registry(transaction, buyer, seller, state.stock_market, state.time)
             elif transaction.item_id.startswith("real_estate_"):
                 self._handle_real_estate_registry(transaction, buyer, seller, state.real_estate_units, state.time)

    def _handle_labor_registry(self, tx: Transaction, buyer: Any, seller: Any, state: SimulationState):
        """Updates employment status and employer/employee lists."""
        trade_value = tx.quantity * tx.price

        if isinstance(seller, Household):
            # Change Employer Logic
            if seller._econ_state.is_employed and seller._econ_state.employer_id is not None and seller._econ_state.employer_id != buyer.id:
                previous_employer = state.agents.get(seller._econ_state.employer_id)
                if isinstance(previous_employer, Firm):
                     previous_employer.hr.remove_employee(seller)

            seller._econ_state.is_employed = True
            seller._econ_state.employer_id = buyer.id
            seller._econ_state.current_wage = tx.price # Contract update
            seller._bio_state.needs["labor_need"] = 0.0 # Fulfilled need

        if isinstance(buyer, Firm):
            if seller not in buyer.hr.employees:
                buyer.hr.hire(seller, tx.price)
            else:
                 buyer.hr.employee_wages[seller.id] = tx.price

            # Research Labor Special Effect (Productivity)
            # Is this Registry or TechSystem? It modifies Firm state (productivity_factor).
            # Registry updates "Non-financial state". Productivity is state.
            if tx.transaction_type == "research_labor" and isinstance(seller, Household):
                research_skill = seller._econ_state.skills.get("research", Skill("research")).value
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
            if isinstance(seller, Household):
                seller._econ_state.inventory[tx.item_id] = max(0, seller._econ_state.inventory.get(tx.item_id, 0) - tx.quantity)
            elif hasattr(seller, "inventory"):
                 seller.inventory[tx.item_id] = max(0, seller.inventory.get(tx.item_id, 0) - tx.quantity)

            # Buyer Inventory
            is_raw_material = tx.item_id in getattr(config, "RAW_MATERIAL_SECTORS", [])

            if is_raw_material and isinstance(buyer, Firm):
                buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity
            elif isinstance(buyer, Household):
                current_qty = buyer._econ_state.inventory.get(tx.item_id, 0)
                existing_quality = buyer._econ_state.inventory_quality.get(tx.item_id, 1.0)
                tx_quality = tx.quality if hasattr(tx, 'quality') else 1.0
                total_new_qty = current_qty + tx.quantity

                if total_new_qty > 0:
                    new_avg_quality = ((current_qty * existing_quality) + (tx.quantity * tx_quality)) / total_new_qty
                    buyer._econ_state.inventory_quality[tx.item_id] = new_avg_quality

                buyer._econ_state.inventory[tx.item_id] = total_new_qty
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
            seller._econ_state.portfolio.remove(firm_id, tx.quantity)
        elif isinstance(seller, Firm) and seller.id == firm_id:
            seller.treasury_shares = max(0, seller.treasury_shares - tx.quantity)
        elif hasattr(seller, "portfolio"):
            seller.portfolio.remove(firm_id, tx.quantity)

        # 2. Buyer Holdings
        if isinstance(buyer, Household):
            buyer._econ_state.portfolio.add(firm_id, tx.quantity, tx.price)
        elif isinstance(buyer, Firm) and buyer.id == firm_id:
            buyer.treasury_shares += tx.quantity
            buyer.total_shares -= tx.quantity

        # 3. Market Registry (Shareholder List)
        if stock_market:
            # Sync Buyer
            if isinstance(buyer, Household) and firm_id in buyer._econ_state.portfolio.holdings:
                 stock_market.update_shareholder(buyer.id, firm_id, buyer._econ_state.portfolio.holdings[firm_id].quantity)
            elif hasattr(buyer, "portfolio") and firm_id in buyer.portfolio.holdings:
                 stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)

            # Sync Seller
            if isinstance(seller, Household) and firm_id in seller._econ_state.portfolio.holdings:
                stock_market.update_shareholder(seller.id, firm_id, seller._econ_state.portfolio.holdings[firm_id].quantity)
            elif hasattr(seller, "portfolio") and firm_id in seller.portfolio.holdings:
                stock_market.update_shareholder(seller.id, firm_id, seller.portfolio.holdings[firm_id].quantity)
            else:
                stock_market.update_shareholder(seller.id, firm_id, 0.0)

    def _handle_real_estate_registry(self, tx: Transaction, buyer: Any, seller: Any, real_estate_units: List[Any], current_time: int):
        """Updates real estate ownership."""
        try:
            unit_id = int(tx.item_id.split("_")[2])
            unit = next((u for u in real_estate_units if u.id == unit_id), None)
            if unit:
                unit.owner_id = buyer.id
                # Update seller/buyer lists if they exist
                if isinstance(seller, Household):
                    if unit_id in seller._econ_state.owned_properties:
                        seller._econ_state.owned_properties.remove(unit_id)
                elif hasattr(seller, "owned_properties") and unit_id in seller.owned_properties:
                    seller.owned_properties.remove(unit_id)

                if isinstance(buyer, Household):
                    buyer._econ_state.owned_properties.append(unit_id)
                elif hasattr(buyer, "owned_properties"):
                    buyer.owned_properties.append(unit_id)

                self.logger.info(f"RE_TX | Unit {unit_id} transferred from {seller.id} to {buyer.id}")
        except (IndexError, ValueError) as e:
            self.logger.error(f"RE_TX_FAIL | Invalid item_id format: {tx.item_id}. Error: {e}")

    def _handle_housing_registry(self, tx: Transaction, buyer: Any, seller: Any, real_estate_units: List[Any], current_time: int):
        """
        Updates housing ownership, handling 'unit_{id}' format.
        Also updates 'is_homeless' status and 'residing_property_id'.
        """
        try:
            # item_id format: "unit_{id}"
            unit_id = int(tx.item_id.split("_")[1])
            unit = next((u for u in real_estate_units if u.id == unit_id), None)

            if not unit:
                self.logger.warning(f"HOUSING_REGISTRY | Unit {unit_id} not found.")
                return

            # Update Unit
            unit.owner_id = buyer.id
            if tx.metadata and "mortgage_id" in tx.metadata:
                unit.mortgage_id = tx.metadata["mortgage_id"]
            else:
                unit.mortgage_id = None

            # Update Seller (if not None/Govt)
            if seller:
                if isinstance(seller, Household):
                     if unit_id in seller._econ_state.owned_properties:
                        seller._econ_state.owned_properties.remove(unit_id)
                elif hasattr(seller, "owned_properties"):
                    if unit_id in seller.owned_properties:
                        seller.owned_properties.remove(unit_id)

            # Update Buyer
            if isinstance(buyer, Household):
                if unit_id not in buyer._econ_state.owned_properties:
                    buyer._econ_state.owned_properties.append(unit_id)

                # Housing System Logic: Auto-move-in if homeless
                if buyer._econ_state.residing_property_id is None:
                    unit.occupant_id = buyer.id
                    buyer._econ_state.residing_property_id = unit_id
                    buyer._econ_state.is_homeless = False
            elif hasattr(buyer, "owned_properties"):
                if unit_id not in buyer.owned_properties:
                    buyer.owned_properties.append(unit_id)

                # Housing System Logic: Auto-move-in if homeless
                if getattr(buyer, "residing_property_id", None) is None:
                    unit.occupant_id = buyer.id
                    buyer.residing_property_id = unit_id
                    buyer.is_homeless = False

            self.logger.info(f"HOUSING_REGISTRY | Unit {unit_id} transferred from {tx.seller_id} to {buyer.id}")

        except (IndexError, ValueError) as e:
            self.logger.error(f"HOUSING_REGISTRY_FAIL | Invalid item_id format: {tx.item_id}. Error: {e}")

    def _handle_emergency_buy(self, tx: Transaction, buyer: Any):
        """Updates inventory for emergency buys."""
        if isinstance(buyer, Household):
            buyer._econ_state.inventory[tx.item_id] = buyer._econ_state.inventory.get(tx.item_id, 0.0) + tx.quantity
        elif hasattr(buyer, "inventory"):
            buyer.inventory[tx.item_id] = buyer.inventory.get(tx.item_id, 0.0) + tx.quantity
