from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING
import logging

from simulation.models import Transaction
from simulation.core_agents import Household, Skill
from simulation.firms import Firm

if TYPE_CHECKING:
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class TransactionProcessor:
    """
    Simulation 엔진의 거대한 거래 처리 로직을 담당하는 전용 클래스.
    관심사의 분리(SoC)를 위해 Simulation 클래스에서 추출됨.
    """

    def __init__(self, config_module: Any):
        self.config_module = config_module

    def process(
        self, 
        transactions: List[Transaction], 
        agents: Dict[int, Any], 
        government: Any, 
        current_time: int,
        market_data_callback: Any # To get goods_market_data for survival cost
    ) -> None:
        """발생한 거래들을 처리하여 에이전트의 자산, 재고, 고용 상태 등을 업데이트합니다."""
        for tx in transactions:
            buyer = agents.get(tx.buyer_id)
            seller = agents.get(tx.seller_id)

            if not buyer or not seller:
                continue

            trade_value = tx.quantity * tx.price
            sales_tax_rate = getattr(self.config_module, "SALES_TAX_RATE", 0.05)
            
            tax_amount = 0.0

            # --- 1. 자산 이동 (Asset Transfer) ---
            if tx.transaction_type in ["goods", "stock"]:
                # Stock and Goods move assets directly here
                # Tax calculation is deferred to Step 2
                pass # Logic handled in specific blocks below combined with tax?
                # No, the requirement is to split "Asset Movement" and "Meta/Tax"

                # Let's handle the raw asset transfer first
                buyer.assets -= trade_value
                seller.assets += trade_value

            elif tx.transaction_type in ["labor", "research_labor"]:
                # Labor income/expense handled here
                # Tax is separate
                buyer.assets -= trade_value
                seller.assets += trade_value

            elif tx.item_id == "interest_payment":
                buyer.assets -= trade_value
                seller.assets += trade_value
                if isinstance(buyer, Firm):
                    buyer.finance.record_expense(trade_value)

            elif tx.transaction_type == "dividend":
                seller.assets -= trade_value
                buyer.assets += trade_value
                if isinstance(buyer, Household) and hasattr(buyer, "capital_income_this_tick"):
                    buyer.capital_income_this_tick += trade_value

            else:
                # Fallback for loans etc
                buyer.assets -= trade_value
                seller.assets += trade_value


            # --- 2. 메타 처리 (Meta Processing: Taxes, Checks, Side Effects) ---
            # Independent blocks, no 'elif' chaining with the above.

            # A. Sales Tax & Solvency Check (Goods Only)
            if tx.transaction_type == "goods":
                # Apply Sales Tax
                tax_amount = trade_value * sales_tax_rate
                
                # Check solvency for the tax + trade_value (even though trade_value was already deducted,
                # strictly speaking check_solvency should probably happen before deduction,
                # but to minimize refactor risk we follow the original logic flow's intent but separate the block)
                # Note: Original code deducted (trade_value + tax_amount) at once.
                # Here we deducted trade_value above. Now we deduct tax.

                if hasattr(buyer, 'check_solvency'):
                     # We need to simulate the total hit
                     # buyer.assets is already -trade_value relative to start
                     if buyer.assets < tax_amount:
                         # This is a bit weak check compared to original "assets < trade + tax" before deduction
                         # But since we already deducted trade_value, checking if remaining assets < tax is equivalent
                         buyer.check_solvency(government)

                buyer.assets -= tax_amount # Pay the tax
                government.collect_tax(tax_amount, f"sales_tax_{tx.transaction_type}", buyer.id, current_time)

            # B. Income Tax (Labor)
            if tx.transaction_type in ["labor", "research_labor"]:
                tax_payer = getattr(self.config_module, "INCOME_TAX_PAYER", "HOUSEHOLD")

                # Calculate Survival Cost for Progressive Tax
                goods_market_data = market_data_callback()
                if "basic_food_current_sell_price" in goods_market_data:
                    avg_food_price = goods_market_data["basic_food_current_sell_price"]
                else:
                    avg_food_price = getattr(self.config_module, "GOODS_INITIAL_PRICE", {}).get("basic_food", 5.0)
                
                daily_food_need = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)
                survival_cost = max(avg_food_price * daily_food_need, 10.0)

                tax_amount = government.calculate_income_tax(trade_value, survival_cost)
                
                if tax_payer == "FIRM":
                    # Buyer (Firm) pays tax on top
                    buyer.assets -= tax_amount
                    government.collect_tax(tax_amount, "income_tax_firm", buyer.id, current_time)
                else:
                    # Seller (Household) pays tax from income
                    # Since we already added full trade_value to seller above, we subtract tax now
                    seller.assets -= tax_amount
                    government.collect_tax(tax_amount, "income_tax_household", seller.id, current_time)

            # C. Type-Specific Handlers (Inventory, Employment, etc)
            if tx.transaction_type in ["labor", "research_labor"]:
                self._handle_labor_transaction(tx, buyer, seller, trade_value, tax_amount, agents)

            elif tx.transaction_type == "goods":
                self._handle_goods_transaction(tx, buyer, seller, trade_value, current_time)

            elif tx.transaction_type == "stock":
                # Requirement: No sales tax for stock. We just call the handler.
                # Tax block above was for "goods", so stock was skipped. Correct.
                self._handle_stock_transaction(tx, buyer, seller)

            elif tx.transaction_type == "housing" or (hasattr(tx, "market_id") and tx.market_id == "housing"):
                pass

    def _handle_labor_transaction(self, tx: Transaction, buyer: Any, seller: Any, trade_value: float, tax_amount: float, agents: Dict[int, Any]):
        if isinstance(seller, Household):
            if seller.is_employed and seller.employer_id is not None and seller.employer_id != buyer.id:
                previous_employer = agents.get(seller.employer_id)
                if isinstance(previous_employer, Firm):
                    # SoC Refactor: Use HRDepartment
                    previous_employer.hr.remove_employee(seller)

            seller.is_employed = True
            seller.employer_id = buyer.id
            seller.current_wage = tx.price
            seller.needs["labor_need"] = 0.0
            if hasattr(seller, "labor_income_this_tick"):
                # seller.assets already updated in main loop (trade_value - tax_amount effective)
                # just tracking metric here
                income_net = trade_value
                if getattr(self.config_module, "INCOME_TAX_PAYER", "HOUSEHOLD") == "HOUSEHOLD":
                    income_net -= tax_amount
                seller.labor_income_this_tick += income_net

        if isinstance(buyer, Firm):
            # SoC Refactor: Use HRDepartment and FinanceDepartment
            # Use firm.hr.employees based on memory/context
            if seller not in buyer.hr.employees:
                buyer.hr.hire(seller, tx.price)
            else:
                 buyer.hr.employee_wages[seller.id] = tx.price

            buyer.finance.record_expense(trade_value)

            if tx.transaction_type == "research_labor":
                research_skill = seller.skills.get("research", Skill("research")).value
                buyer.productivity_factor += (research_skill * self.config_module.RND_PRODUCTIVITY_MULTIPLIER)

    def _handle_goods_transaction(self, tx: Transaction, buyer: Any, seller: Any, trade_value: float, current_time: int):
        good_info = self.config_module.GOODS.get(tx.item_id, {})
        is_service = good_info.get("is_service", False)

        if is_service:
            if isinstance(buyer, Household):
                buyer.consume(tx.item_id, tx.quantity, current_time)
        else:
            seller.inventory[tx.item_id] = max(0, seller.inventory.get(tx.item_id, 0) - tx.quantity)
            is_raw_material = tx.item_id in getattr(self.config_module, "RAW_MATERIAL_SECTORS", [])

            if is_raw_material and isinstance(buyer, Firm):
                buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity
            else:
                current_qty = buyer.inventory.get(tx.item_id, 0)
                existing_quality = buyer.inventory_quality.get(tx.item_id, 1.0)
                tx_quality = tx.quality if hasattr(tx, 'quality') else 1.0
                total_new_qty = current_qty + tx.quantity
                new_avg_quality = ((current_qty * existing_quality) + (tx.quantity * tx_quality)) / total_new_qty
                
                buyer.inventory_quality[tx.item_id] = new_avg_quality
                buyer.inventory[tx.item_id] = total_new_qty

        if isinstance(seller, Firm):
            # SoC Refactor: Use FinanceDepartment
            seller.finance.record_revenue(trade_value)
            seller.finance.sales_volume_this_tick += tx.quantity
        
        if isinstance(buyer, Household):
            if not is_service:
                buyer.current_consumption += tx.quantity
                if tx.item_id == "basic_food":
                    buyer.current_food_consumption += tx.quantity

    def _handle_stock_transaction(self, tx: Transaction, buyer: Any, seller: Any):
        firm_id = int(tx.item_id.split("_")[1])
        
        if isinstance(seller, Household):
            current_shares = seller.shares_owned.get(firm_id, 0)
            seller.shares_owned[firm_id] = max(0, current_shares - tx.quantity)
            if seller.shares_owned[firm_id] <= 0 and firm_id in seller.shares_owned:
                del seller.shares_owned[firm_id]
            if hasattr(seller, "portfolio"):
                seller.portfolio.remove(firm_id, tx.quantity)
        elif isinstance(seller, Firm) and seller.id == firm_id:
            seller.treasury_shares = max(0, seller.treasury_shares - tx.quantity)
        
        if isinstance(buyer, Household):
            buyer.shares_owned[firm_id] = buyer.shares_owned.get(firm_id, 0) + tx.quantity
            if hasattr(buyer, "portfolio"):
                buyer.portfolio.add(firm_id, tx.quantity, tx.price)
        elif isinstance(buyer, Firm) and buyer.id == firm_id:
            buyer.treasury_shares += tx.quantity
            buyer.total_shares -= tx.quantity
