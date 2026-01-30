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

        # WO-109: Look up inactive agents
        inactive_agents = getattr(state, "inactive_agents", {})

        # market_data is now in state
        goods_market_data = state.market_data.get("goods_market", {}) if state.market_data else {}

        for tx in transactions:
            # WO-109: Fallback to inactive agents
            buyer = agents.get(tx.buyer_id) or inactive_agents.get(tx.buyer_id)
            seller = agents.get(tx.seller_id) or inactive_agents.get(tx.seller_id)

            if not buyer or not seller:
                continue

            trade_value = tx.quantity * tx.price
            sales_tax_rate = getattr(self.config_module, "SALES_TAX_RATE", 0.05)
            tax_amount = 0.0 # Initialize for scope
            
            # ==================================================================
            # 1. Financial Settlement (Asset Transfer & Taxes)
            # ==================================================================
            # WO-125: Enforce SettlementSystem presence (TD-101)
            settlement = state.settlement_system
            if not settlement:
                raise RuntimeError("SettlementSystem is required for TransactionProcessor but is missing in SimulationState.")

            success = False

            if tx.transaction_type == "lender_of_last_resort":
                # Special Minting Logic (Handled via Settlement)
                # Buyer (Gov) -> Seller (Bank).
                success = settlement.transfer(buyer, seller, trade_value, "lender_of_last_resort")
                if success and hasattr(buyer, "total_money_issued"):
                    buyer.total_money_issued += trade_value

            elif tx.transaction_type == "asset_liquidation":
                # Special Minting Logic + Asset Transfer
                # Buyer (Gov) -> Seller (Agent).
                success = settlement.transfer(buyer, seller, trade_value, "asset_liquidation")
                if success:
                    if hasattr(buyer, "total_money_issued"):
                        buyer.total_money_issued += trade_value

                    # Asset Transfer
                    if tx.item_id.startswith("stock_"):
                        self._handle_stock_transaction(tx, buyer, seller, state.stock_market, state.logger, current_time)
                    elif tx.item_id.startswith("real_estate_"):
                        self._handle_real_estate_transaction(tx, buyer, seller, state.real_estate_units, state.logger, current_time)

            elif tx.transaction_type == "asset_transfer":
                 # Standard Transfer (Zero-Sum)
                 success = settlement.transfer(buyer, seller, trade_value, f"asset_transfer:{tx.item_id}")

                 # Asset Transfer Logic
                 if success:
                     if tx.item_id.startswith("stock_"):
                         self._handle_stock_transaction(tx, buyer, seller, state.stock_market, state.logger, current_time)
                     elif tx.item_id.startswith("real_estate_"):
                         self._handle_real_estate_transaction(tx, buyer, seller, state.real_estate_units, state.logger, current_time)

            elif tx.transaction_type == "escheatment":
                 # Buyer: Agent (Deceased/Closed), Seller: Government
                 # Atomic Collection via Government (handles transfer and confirmed recording)
                 result = government.collect_tax(trade_value, "escheatment", buyer, current_time)
                 success = result['success']

            elif tx.transaction_type == "inheritance_distribution":
                heir_ids = tx.metadata.get("heir_ids", []) if tx.metadata else []
                total_cash = buyer.assets
                if total_cash > 0 and heir_ids:
                    import math
                    count = len(heir_ids)
                    # Calculate amount per heir, avoiding float precision issues (floor to cent)
                    base_amount = math.floor((total_cash / count) * 100) / 100.0

                    distributed_sum = 0.0
                    all_success = True

                    # Distribute to all but the last heir
                    for i in range(count - 1):
                        h_id = heir_ids[i]
                        heir = agents.get(h_id)
                        if heir:
                            if settlement.transfer(buyer, heir, base_amount, "inheritance_distribution"):
                                distributed_sum += base_amount
                            else:
                                all_success = False

                    # Last heir gets the remainder to ensure zero-sum
                    last_heir_id = heir_ids[-1]
                    last_heir = agents.get(last_heir_id)
                    if last_heir:
                        remaining_amount = total_cash - distributed_sum
                        # Ensure we don't transfer negative amounts or dust if something went wrong
                        if remaining_amount > 0:
                            if not settlement.transfer(buyer, last_heir, remaining_amount, "inheritance_distribution_final"):
                                all_success = False

                    success = all_success

            elif tx.transaction_type == "goods":
                # Goods: Apply Sales Tax
                tax_amount = trade_value * sales_tax_rate
                
                # Solvency Check
                if hasattr(buyer, 'check_solvency'):
                    if buyer.assets < (trade_value + tax_amount):
                        buyer.check_solvency(government)

                success = settlement.transfer(buyer, seller, trade_value, f"goods_trade:{tx.item_id}")
                if success and tax_amount > 0:
                    # Atomic collection from buyer
                    government.collect_tax(tax_amount, f"sales_tax_{tx.transaction_type}", buyer, current_time)

            elif tx.transaction_type == "stock":
                # Stock: NO Sales Tax
                success = settlement.transfer(buyer, seller, trade_value, f"stock_trade:{tx.item_id}")
            
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
                    success = settlement.transfer(buyer, seller, trade_value, f"labor_wage:{tx.transaction_type}")
                    if success and tax_amount > 0:
                        # Atomic collection from Firm
                        government.collect_tax(tax_amount, "income_tax_firm", buyer, current_time)
                else:
                    # Household pays tax
                    # Pay GROSS wage to household, then collect tax from household
                    success = settlement.transfer(buyer, seller, trade_value, f"labor_wage_gross:{tx.transaction_type}")
                    if success and tax_amount > 0:
                        # Atomic collection from Household (Withholding model)
                        government.collect_tax(tax_amount, "income_tax_household", seller, current_time)
            
            elif tx.item_id == "interest_payment":
                success = settlement.transfer(buyer, seller, trade_value, "interest_payment")

                if success and isinstance(buyer, Firm):
                    buyer.finance.record_expense(trade_value)

            elif tx.transaction_type == "dividend":
                success = settlement.transfer(seller, buyer, trade_value, "dividend_payment")

                if success and isinstance(buyer, Household) and hasattr(buyer, "capital_income_this_tick"):
                    buyer.capital_income_this_tick += trade_value
            elif tx.transaction_type == "tax":
                # Atomic Collection via Government
                result = government.collect_tax(trade_value, tx.item_id, buyer, current_time)
                success = result['success']
            elif tx.transaction_type == "infrastructure_spending":
                # Standard Transfer (Gov -> Reflux)
                success = settlement.transfer(buyer, seller, trade_value, "infrastructure_spending")

            elif tx.transaction_type == "emergency_buy":
                # Fast Purchase (Buyer -> Reflux/System)
                # No Sales Tax, Immediate Inventory Update
                success = settlement.transfer(buyer, seller, trade_value, "emergency_buy")

                if success:
                    buyer.inventory[tx.item_id] = buyer.inventory.get(tx.item_id, 0.0) + tx.quantity

            else:
                # Default / Other
                success = settlement.transfer(buyer, seller, trade_value, f"generic:{tx.transaction_type}")

            # WO-109: Apply Deferred Effects only on Success
            if success and tx.metadata and tx.metadata.get("triggers_effect"):
                state.effects_queue.append(tx.metadata)

            # ==================================================================
            # 2. Meta Logic (Inventory, Employment, Share Registry)
            # ==================================================================
            if success:
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

            # WO-157: Record Sale for Velocity Tracking
            if hasattr(seller, 'record_sale'):
                seller.record_sale(tx.item_id, tx.quantity, current_time)
        
        if isinstance(buyer, Household):
            if not is_service:
                buyer.current_consumption += tx.quantity
                if tx.item_id == "basic_food":
                    buyer.current_food_consumption += tx.quantity

    def _handle_real_estate_transaction(self, tx: Transaction, buyer: Any, seller: Any, real_estate_units: List[Any], logger: Any, current_time: int):
        # item_id = "real_estate_{id}"
        try:
            unit_id = int(tx.item_id.split("_")[2])
            unit = next((u for u in real_estate_units if u.id == unit_id), None)
            if unit:
                unit.owner_id = buyer.id
                # Update seller/buyer lists if they exist
                if hasattr(seller, "owned_properties") and unit_id in seller.owned_properties:
                    seller.owned_properties.remove(unit_id)
                if hasattr(buyer, "owned_properties"):
                    buyer.owned_properties.append(unit_id)

                if logger:
                    logger.info(f"RE_TX | Unit {unit_id} transferred from {seller.id} to {buyer.id}")
        except (IndexError, ValueError) as e:
            if logger:
                logger.error(f"RE_TX_FAIL | Invalid item_id format: {tx.item_id}. Error: {e}")

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
