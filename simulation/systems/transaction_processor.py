from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING, Optional
import logging

from simulation.models import Transaction
from simulation.core_agents import Household, Skill
from simulation.firms import Firm
from simulation.systems.api import SystemInterface
from simulation.finance.api import PaymentIntentDTO

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
        # NOTE: TaxationSystem is now accessed via state.government.taxation_system

    def execute(self, state: SimulationState) -> None:
        """
        발생한 거래들을 처리하여 에이전트의 자산, 재고, 고용 상태 등을 업데이트합니다.
        Uses SimulationState DTO.
        """
        transactions = state.transactions
        agents = state.agents
        government = state.government
        current_time = state.time

        if not government:
             logger.error("TransactionProcessor: Government agent missing from state.")
             return

        # WO-109: Look up inactive agents
        inactive_agents = getattr(state, "inactive_agents", {})

        # market_data is now in state
        goods_market_data = state.market_data.get("goods_market", {}) if state.market_data else {}

        # WO-125: Enforce SettlementSystem presence (TD-101)
        settlement = state.settlement_system
        if not settlement:
            raise RuntimeError("SettlementSystem is required for TransactionProcessor but is missing in SimulationState.")

        taxation_system = getattr(government, 'taxation_system', None)
        if not taxation_system:
             logger.warning("TransactionProcessor: Government has no taxation_system. Tax logic will be skipped.")

        for tx in transactions:
            # WO-109: Fallback to inactive agents
            buyer = agents.get(tx.buyer_id) or inactive_agents.get(tx.buyer_id)
            seller = agents.get(tx.seller_id) or inactive_agents.get(tx.seller_id)

            if not buyer or not seller:
                continue

            trade_value = tx.quantity * tx.price
            success = False
            
            # ==================================================================
            # 1. Financial Settlement (Asset Transfer & Taxes)
            # ==================================================================

            if tx.transaction_type == "lender_of_last_resort":
                # Special Minting Logic
                success = settlement.transfer(buyer, seller, trade_value, "lender_of_last_resort")
                if success and hasattr(buyer, "total_money_issued"):
                    buyer.total_money_issued += trade_value

            elif tx.transaction_type == "asset_liquidation":
                success = settlement.transfer(buyer, seller, trade_value, "asset_liquidation")
                if success:
                    if hasattr(buyer, "total_money_issued"):
                        buyer.total_money_issued += trade_value
                    self._handle_asset_transfer_logic(tx, buyer, seller, state, current_time)

            elif tx.transaction_type == "asset_transfer":
                 success = settlement.transfer(buyer, seller, trade_value, f"asset_transfer:{tx.item_id}")
                 if success:
                     self._handle_asset_transfer_logic(tx, buyer, seller, state, current_time)

            elif tx.transaction_type == "escheatment":
                 # Atomic settlement to government
                 success = settlement.transfer(buyer, government, trade_value, "escheatment")
                 # We can record this as tax revenue if needed, or rely on SettlementSystem.record_liquidation
                 if success and taxation_system:
                      # Manual record
                      taxation_system.record_revenue({
                             "payer_id": buyer.id,
                             "payee_id": government.id,
                             "amount": trade_value,
                             "tax_type": "escheatment"
                         }, True, current_time)

            elif tx.transaction_type == "inheritance_distribution":
                # Keeps existing logic as it is complex 1-to-many distribution
                success = self._handle_inheritance_distribution(tx, buyer, agents, settlement)

            elif tx.transaction_type == "bond_purchase":
                success = settlement.transfer(buyer, seller, trade_value, "bond_purchase")
                if success and state.central_bank and buyer.id == state.central_bank.id:
                    if hasattr(government, "total_money_issued"):
                        government.total_money_issued += trade_value
                        state.logger.info(
                            f"QUANTITATIVE_EASING | Central Bank purchased bond {trade_value:.2f}. Total Money Issued updated.",
                            extra={"tick": current_time, "tag": "QE"}
                        )

            elif tx.transaction_type == "bond_repayment":
                success = settlement.transfer(buyer, seller, trade_value, "bond_repayment")
                if success and state.central_bank and seller.id == state.central_bank.id:
                    if hasattr(government, "total_money_destroyed"):
                        government.total_money_destroyed += trade_value

            elif tx.transaction_type == "goods" or tx.transaction_type in ["labor", "research_labor"]:
                # === ATOMIC ESCROW SETTLEMENT ===
                payment_intents: List[PaymentIntentDTO] = []
                tax_intents = []

                if taxation_system:
                    tax_intents = taxation_system.generate_tax_intents(tx, state)
                
                # Determine Payee Logic
                # Goods: Buyer -> Seller (Trade Value). Buyer -> Gov (Sales Tax, Add-on).
                # Labor: Buyer -> Seller (Wage). Seller -> Gov (Income Tax, Deduction).

                net_trade_value = trade_value

                # Process Tax Intents
                for ti in tax_intents:
                    # Construct PaymentIntent for Tax
                    # We assume ALL payments in this batch come from the Primary Payer (tx.buyer)
                    # This enables Atomic "Withholding" / "Sales Tax collection" behavior.

                    tax_payee = agents.get(ti['payee_id']) or government
                    payment_intents.append({
                        "payee": tax_payee,
                        "amount": ti['amount'],
                        "memo": ti['tax_type']
                    })

                    # Adjust Net Trade Value if the tax was supposed to be paid by Seller (Deduction)
                    if ti['payer_id'] == seller.id:
                        net_trade_value -= ti['amount']

                    # If payer_id == buyer.id, it's an add-on, so net_trade_value remains same.

                # Add Primary Trade Intent
                payment_intents.append({
                    "payee": seller,
                    "amount": net_trade_value,
                    "memo": f"{tx.transaction_type}_payment:{tx.item_id}"
                })

                # Solvency Check (Optional optimization)
                total_cost = sum(p['amount'] for p in payment_intents)
                if hasattr(buyer, 'check_solvency'):
                    if buyer.assets < total_cost:
                        buyer.check_solvency(government)

                # Execute Atomic Settlement
                success = settlement.settle_escrow(buyer, payment_intents, current_time)

                if success:
                    # Record Revenue
                    if taxation_system:
                        for ti in tax_intents:
                            taxation_system.record_revenue(ti, True, current_time)

                # Store tax_amount for side-effects if needed
                # (Legacy logic used tax_amount in labor side effects)
                tax_amount = sum(ti['amount'] for ti in tax_intents) # Total tax involved

            elif tx.transaction_type == "stock":
                success = settlement.transfer(buyer, seller, trade_value, f"stock_trade:{tx.item_id}")
            
            elif tx.item_id == "interest_payment":
                success = settlement.transfer(buyer, seller, trade_value, "interest_payment")
                if success and isinstance(buyer, Firm):
                    buyer.finance.record_expense(trade_value)

            elif tx.transaction_type == "dividend":
                success = settlement.transfer(seller, buyer, trade_value, "dividend_payment")
                if success and isinstance(buyer, Household) and hasattr(buyer, "capital_income_this_tick"):
                    buyer.capital_income_this_tick += trade_value

            elif tx.transaction_type == "tax":
                # Direct transfer
                success = settlement.transfer(buyer, government, trade_value, tx.item_id)
                if success and taxation_system:
                      taxation_system.record_revenue({
                             "payer_id": buyer.id,
                             "payee_id": government.id,
                             "amount": trade_value,
                             "tax_type": tx.item_id
                         }, True, current_time)

            elif tx.transaction_type == "infrastructure_spending":
                success = settlement.transfer(buyer, seller, trade_value, "infrastructure_spending")

            elif tx.transaction_type == "emergency_buy":
                success = settlement.transfer(buyer, seller, trade_value, "emergency_buy")
                if success:
                    buyer.inventory[tx.item_id] = buyer.inventory.get(tx.item_id, 0.0) + tx.quantity

            elif tx.transaction_type in ["credit_creation", "credit_destruction"]:
                # Symbolic
                success = True

            else:
                # Default
                success = settlement.transfer(buyer, seller, trade_value, f"generic:{tx.transaction_type}")

            # WO-109: Apply Deferred Effects only on Success
            if success and tx.metadata and tx.metadata.get("triggers_effect"):
                state.effects_queue.append(tx.metadata)

            # ==================================================================
            # 2. Meta Logic (Inventory, Employment, Share Registry)
            # ==================================================================
            if success:
                if tx.transaction_type in ["labor", "research_labor"]:
                    # We need tax_amount here. In 'goods/labor' block we calculated it.
                    # If transaction type matched that block, tax_amount is set.
                    # Otherwise (unlikely for labor), default to 0.
                    t_amt = locals().get('tax_amount', 0.0)
                    self._handle_labor_transaction(tx, buyer, seller, trade_value, t_amt, agents)

                elif tx.transaction_type == "goods":
                    self._handle_goods_transaction(tx, buyer, seller, trade_value, current_time)

                elif tx.transaction_type == "stock":
                    self._handle_stock_transaction(tx, buyer, seller, state.stock_market, state.logger, current_time)

    def _handle_asset_transfer_logic(self, tx, buyer, seller, state, current_time):
        if tx.item_id.startswith("stock_"):
            self._handle_stock_transaction(tx, buyer, seller, state.stock_market, state.logger, current_time)
        elif tx.item_id.startswith("real_estate_"):
            self._handle_real_estate_transaction(tx, buyer, seller, state.real_estate_units, state.logger, current_time)

    def _handle_inheritance_distribution(self, tx, buyer, agents, settlement):
        heir_ids = tx.metadata.get("heir_ids", []) if tx.metadata else []
        total_cash = buyer.assets
        if total_cash > 0 and heir_ids:
            import math
            count = len(heir_ids)
            base_amount = math.floor((total_cash / count) * 100) / 100.0
            distributed_sum = 0.0
            all_success = True

            for i in range(count - 1):
                h_id = heir_ids[i]
                heir = agents.get(h_id)
                if heir:
                    if settlement.transfer(buyer, heir, base_amount, "inheritance_distribution"):
                        distributed_sum += base_amount
                    else:
                        all_success = False

            last_heir_id = heir_ids[-1]
            last_heir = agents.get(last_heir_id)
            if last_heir:
                remaining_amount = total_cash - distributed_sum
                if remaining_amount > 0:
                    if not settlement.transfer(buyer, last_heir, remaining_amount, "inheritance_distribution_final"):
                        all_success = False
            return all_success
        return False

    def _handle_labor_transaction(self, tx: Transaction, buyer: Any, seller: Any, trade_value: float, tax_amount: float, agents: Dict[int, Any]):
        if isinstance(seller, Household):
            if seller.is_employed and seller.employer_id is not None and seller.employer_id != buyer.id:
                previous_employer = agents.get(seller.employer_id)
                if isinstance(previous_employer, Firm):
                    previous_employer.hr.remove_employee(seller)

            seller.is_employed = True
            seller.employer_id = buyer.id
            seller.current_wage = tx.price
            seller.needs["labor_need"] = 0.0
            if hasattr(seller, "labor_income_this_tick"):
                # Net income
                seller.labor_income_this_tick += (trade_value - tax_amount)

        if isinstance(buyer, Firm):
            if seller not in buyer.hr.employees:
                buyer.hr.hire(seller, tx.price)
            else:
                 buyer.hr.employee_wages[seller.id] = tx.price

            # Expense is Gross
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
            seller.finance.record_revenue(trade_value)
            seller.finance.sales_volume_this_tick += tx.quantity
            if hasattr(seller, 'record_sale'):
                seller.record_sale(tx.item_id, tx.quantity, current_time)
        
        if isinstance(buyer, Household):
            if not is_service:
                buyer.current_consumption += tx.quantity
                if tx.item_id == "basic_food":
                    buyer.current_food_consumption += tx.quantity

    def _handle_real_estate_transaction(self, tx: Transaction, buyer: Any, seller: Any, real_estate_units: List[Any], logger: Any, current_time: int):
        try:
            unit_id = int(tx.item_id.split("_")[2])
            unit = next((u for u in real_estate_units if u.id == unit_id), None)
            if unit:
                unit.owner_id = buyer.id
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
            seller.portfolio.remove(firm_id, tx.quantity)
        
        if isinstance(buyer, Household):
            buyer.shares_owned[firm_id] = buyer.shares_owned.get(firm_id, 0) + tx.quantity
            if hasattr(buyer, "portfolio"):
                buyer.portfolio.add(firm_id, tx.quantity, tx.price)
                buyer.shares_owned[firm_id] = buyer.portfolio.holdings[firm_id].quantity
        elif isinstance(buyer, Firm) and buyer.id == firm_id:
            buyer.treasury_shares += tx.quantity
            buyer.total_shares -= tx.quantity

        if stock_market:
            if hasattr(buyer, "portfolio") and firm_id in buyer.portfolio.holdings:
                 stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)
            if hasattr(seller, "portfolio") and firm_id in seller.portfolio.holdings:
                stock_market.update_shareholder(seller.id, firm_id, seller.portfolio.holdings[firm_id].quantity)
            else:
                stock_market.update_shareholder(seller.id, firm_id, 0.0)

        if logger:
            logger.info(
                f"STOCK_TX | Buyer: {buyer.id}, Seller: {seller.id}, Firm: {firm_id}, Qty: {tx.quantity}, Price: {tx.price}",
                extra={"tick": current_time, "tags": ["stock_market", "transaction"]}
            )
