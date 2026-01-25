from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING
import logging

from simulation.models import Transaction
from simulation.core_agents import Household, Skill
from simulation.firms import Firm
from simulation.systems.api import SystemInterface

if TYPE_CHECKING:
    from simulation.agents.government import Government
    from simulation.dtos.api import SimulationState

logger = logging.getLogger(__name__)

class TransactionProcessor(SystemInterface):
    """
    Simulation 엔진의 거대한 거래 처리 로직을 담당하는 전용 클래스.
    관심사의 분리(SoC)를 위해 Simulation 클래스에서 추출됨.
    WO-103: Implements SystemInterface to enforce Sacred Sequence.
    """

    def __init__(self, config_module: Any):
        self.config_module = config_module

    def execute(self, state: SimulationState) -> None:
        """
        발생한 거래들을 처리하여 에이전트의 자산, 재고, 고용 상태 등을 업데이트합니다.
        Uses SimulationState DTO.
        """
        transactions = state.transactions
        agents = state.agents
        government = state.government
        current_time = state.time

        # market_data is now in state
        goods_market_data = state.market_data.get("goods_market", {}) if state.market_data else {}

        for tx in transactions:
            buyer = agents.get(tx.buyer_id)
            seller = agents.get(tx.seller_id)

            if not buyer or not seller:
                continue

            trade_value = tx.quantity * tx.price
            sales_tax_rate = getattr(self.config_module, "SALES_TAX_RATE", 0.05)
            tax_amount = 0.0 # Initialize for scope
            
            # ==================================================================
            # 1. Financial Settlement (Asset Transfer & Taxes)
            # ==================================================================
            settlement = getattr(state, 'settlement_system', None)

            if tx.transaction_type == "goods":
                # Goods: Apply Sales Tax
                tax_amount = trade_value * sales_tax_rate
                
                # Solvency Check
                if hasattr(buyer, 'check_solvency'):
                    if buyer.assets < (trade_value + tax_amount):
                        buyer.check_solvency(government)

                if settlement:
                    settlement.transfer(buyer, seller, trade_value, f"goods_trade:{tx.item_id}")
                    # Tax collection is now handled via government.collect_tax
                else:
                    buyer.withdraw(trade_value + tax_amount)
                    seller.deposit(trade_value)
                    government.deposit(tax_amount)

                # Fix: Pass buyer object, not ID, to collect_tax
                government.collect_tax(tax_amount, f"sales_tax_{tx.transaction_type}", buyer, current_time)

            elif tx.transaction_type == "stock":
                # Stock: NO Sales Tax
                if settlement:
                    settlement.transfer(buyer, seller, trade_value, f"stock_trade:{tx.item_id}")
                else:
                    buyer.withdraw(trade_value)
                    seller.deposit(trade_value)
            
            elif tx.transaction_type in ["labor", "research_labor"]:
                # Labor: Apply Income Tax
                tax_payer = getattr(self.config_module, "INCOME_TAX_PAYER", "HOUSEHOLD")

                if "basic_food_current_sell_price" in goods_market_data:
                    avg_food_price = goods_market_data["basic_food_current_sell_price"]
                else:
                    avg_food_price = getattr(self.config_module, "GOODS_INITIAL_PRICE", {}).get("basic_food", 5.0)
                
                daily_food_need = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)
                survival_cost = max(avg_food_price * daily_food_need, 10.0)

                tax_amount = government.calculate_income_tax(trade_value, survival_cost)
                
                if tax_payer == "FIRM":
                    if settlement:
                        settlement.transfer(buyer, seller, trade_value, f"labor_wage:{tx.transaction_type}")
                        # Tax collection is now handled via government.collect_tax
                    else:
                        buyer.withdraw(trade_value + tax_amount)
                        seller.deposit(trade_value)
                        government.deposit(tax_amount)

                    # Fix: Pass buyer object (Firm) to collect_tax
                    government.collect_tax(tax_amount, "income_tax_firm", buyer, current_time)
                else:
                    # Household pays tax (Withholding model)
                    net_wage = trade_value - tax_amount
                    if settlement:
                        # Refactor: Pay GROSS wage to household, then collect tax from household
                        settlement.transfer(buyer, seller, trade_value, f"labor_wage_gross:{tx.transaction_type}")
                        # Tax collection is now handled via government.collect_tax (debited from household)
                    else:
                        buyer.withdraw(trade_value) # Buyer pays full (net + tax split dest)
                        seller.deposit(net_wage)
                        government.deposit(tax_amount)

                    # Fix: Pass seller object (Household) to collect_tax
                    government.collect_tax(tax_amount, "income_tax_household", seller, current_time)
            
            elif tx.item_id == "interest_payment":
                if settlement:
                    settlement.transfer(buyer, seller, trade_value, "interest_payment")
                else:
                    buyer.withdraw(trade_value)
                    seller.deposit(trade_value)

                if isinstance(buyer, Firm):
                    buyer.finance.record_expense(trade_value)

            elif tx.transaction_type == "dividend":
                if settlement:
                    settlement.transfer(seller, buyer, trade_value, "dividend_payment")
                else:
                    seller.withdraw(trade_value)
                    buyer.deposit(trade_value)

                if isinstance(buyer, Household) and hasattr(buyer, "capital_income_this_tick"):
                    buyer.capital_income_this_tick += trade_value
            else:
                # Default / Other
                if settlement:
                    settlement.transfer(buyer, seller, trade_value, f"generic:{tx.transaction_type}")
                else:
                    buyer.withdraw(trade_value)
                    seller.deposit(trade_value)

            # ==================================================================
            # 2. Meta Logic (Inventory, Employment, Share Registry)
            # ==================================================================
            if tx.transaction_type in ["labor", "research_labor"]:
                self._handle_labor_transaction(tx, buyer, seller, trade_value, tax_amount, agents)

            elif tx.transaction_type == "goods":
                self._handle_goods_transaction(tx, buyer, seller, trade_value, current_time)

            elif tx.transaction_type == "stock":
                self._handle_stock_transaction(tx, buyer, seller, state.stock_market, state.logger, current_time)

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
                seller.labor_income_this_tick += (trade_value - tax_amount)

        if isinstance(buyer, Firm):
            # SoC Refactor: Use HRDepartment and FinanceDepartment
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

    def _handle_stock_transaction(self, tx: Transaction, buyer: Any, seller: Any, stock_market: Any, logger: Any, current_time: int):
        firm_id = int(tx.item_id.split("_")[1])
        
        # 1. Update Holdings
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
            # Secondary market trade for Firms/Institutions if they have portfolio
            seller.portfolio.remove(firm_id, tx.quantity)
        
        if isinstance(buyer, Household):
            buyer.shares_owned[firm_id] = buyer.shares_owned.get(firm_id, 0) + tx.quantity
            if hasattr(buyer, "portfolio"):
                buyer.portfolio.add(firm_id, tx.quantity, tx.price)
                # Sync legacy dict
                buyer.shares_owned[firm_id] = buyer.portfolio.holdings[firm_id].quantity
        elif isinstance(buyer, Firm) and buyer.id == firm_id:
            buyer.treasury_shares += tx.quantity
            buyer.total_shares -= tx.quantity

        # 2. Sync Market Shareholder Registry (CRITICAL for Dividends)
        if stock_market:
            # Sync Buyer
            if hasattr(buyer, "portfolio") and firm_id in buyer.portfolio.holdings:
                 stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)

            # Sync Seller
            if hasattr(seller, "portfolio") and firm_id in seller.portfolio.holdings:
                stock_market.update_shareholder(seller.id, firm_id, seller.portfolio.holdings[firm_id].quantity)
            else:
                stock_market.update_shareholder(seller.id, firm_id, 0.0)

        if logger:
            logger.info(
                f"STOCK_TX | Buyer: {buyer.id}, Seller: {seller.id}, Firm: {firm_id}, Qty: {tx.quantity}, Price: {tx.price}",
                extra={"tick": current_time, "tags": ["stock_market", "transaction"]}
            )
