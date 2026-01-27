from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging

from simulation.systems.api import (
    SystemInterface,
    IMintingAuthority,
    IAccountingSystem,
    IRegistry,
    ISpecializedTransactionHandler
)
from simulation.dtos.api import SimulationState
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm

logger = logging.getLogger(__name__)

class TransactionManager(SystemInterface):
    """
    Orchestrates the transaction processing pipeline.
    Replaces the monolithic TransactionProcessor.
    Follows the 6-layer architecture (TD-124).
    """

    def __init__(
        self,
        registry: IRegistry,
        accounting_system: IAccountingSystem,
        settlement_system: Any, # ISettlementSystem
        central_bank_system: IMintingAuthority,
        config: Any,
        handlers: Optional[Dict[str, ISpecializedTransactionHandler]] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.registry = registry
        self.accounting = accounting_system
        self.settlement = settlement_system
        self.central_bank = central_bank_system
        self.config = config
        self.handlers = handlers if handlers else {}
        self.logger = logger if logger else logging.getLogger(__name__)

    def execute(self, state: SimulationState) -> None:
        """
        Processes all transactions in the current tick.
        """
        transactions = state.transactions
        agents = state.agents
        government = state.government
        current_time = state.time

        # WO-109: Look up inactive agents
        inactive_agents = getattr(state, "inactive_agents", {})

        # market_data is now in state (if needed for pricing context)
        goods_market_data = state.market_data.get("goods_market", {}) if state.market_data else {}

        for tx in transactions:
            buyer = agents.get(tx.buyer_id) or inactive_agents.get(tx.buyer_id)
            seller = agents.get(tx.seller_id) or inactive_agents.get(tx.seller_id)

            if not buyer and not seller:
                continue

            trade_value = tx.quantity * tx.price
            tax_amount = 0.0
            success = False

            # ==================================================================
            # 1. Specialized Handlers (Sagas)
            # ==================================================================
            if tx.transaction_type in self.handlers:
                success = self.handlers[tx.transaction_type].handle(tx, buyer, seller, state)

            # ==================================================================
            # 2. Financial Layer (Routing)
            # ==================================================================
            elif tx.transaction_type == "lender_of_last_resort":
                # Minting: Central Bank -> Bank
                # Note: 'buyer' is typically Government/System, 'seller' is Bank receiving funds.
                success = self.central_bank.mint_and_transfer(seller, trade_value, "lender_of_last_resort")
                if success and hasattr(buyer, "total_money_issued"):
                    buyer.total_money_issued += trade_value

            elif tx.transaction_type == "asset_liquidation":
                # Minting: Central Bank -> Agent (Liquidation)
                success = self.central_bank.mint_and_transfer(seller, trade_value, "asset_liquidation")
                # Registry handles asset transfer/destruction implicitly or explicitly via update_ownership
                # if needed. TransactionProcessor handled asset transfer for stock/real_estate here.
                # If success, we should update ownership (Registry) in the State Commitment phase.

            elif tx.transaction_type == "inheritance_distribution":
                 # Handled by handlers['inheritance_distribution'] usually.
                 # If handler is missing, log error?
                 if "inheritance_distribution" not in self.handlers:
                     self.logger.error("TransactionManager: Missing handler for inheritance_distribution")
                 continue

            elif tx.transaction_type == "escheatment":
                 # Buyer: Agent (Deceased/Closed), Seller: Government
                 # Atomic Collection via Government (handles transfer and confirmed recording)
                 result = government.collect_tax(trade_value, "escheatment", buyer, current_time)
                 success = result['success']

            elif tx.transaction_type == "goods":
                # Sales Tax Logic
                sales_tax_rate = getattr(self.config, "SALES_TAX_RATE", 0.05)
                tax_amount = trade_value * sales_tax_rate

                # Solvency Check (Legacy compatibility)
                if hasattr(buyer, 'check_solvency'):
                    if buyer.assets < (trade_value + tax_amount):
                        buyer.check_solvency(government)

                # Standard Transfer
                success = self.settlement.transfer(buyer, seller, trade_value, f"goods_trade:{tx.item_id}")

                if success and tax_amount > 0:
                    # Atomic Tax Collection
                    government.collect_tax(tax_amount, f"sales_tax_{tx.transaction_type}", buyer, current_time)

            elif tx.transaction_type in ["labor", "research_labor"]:
                # Income Tax Logic
                tax_payer = getattr(self.config, "INCOME_TAX_PAYER", "HOUSEHOLD")

                if "basic_food_current_sell_price" in goods_market_data:
                    avg_food_price = goods_market_data["basic_food_current_sell_price"]
                else:
                    avg_food_price = getattr(self.config, "GOODS_INITIAL_PRICE", {}).get("basic_food", 5.0)

                daily_food_need = getattr(self.config, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)
                survival_cost = max(avg_food_price * daily_food_need, 10.0)

                # Calculate Tax (Standardized method call on Gov)
                # Note: calculate_income_tax is on Government agent.
                tax_amount = government.calculate_income_tax(trade_value, survival_cost)

                if tax_payer == "FIRM":
                    # Firm pays Wage to Household
                    success = self.settlement.transfer(buyer, seller, trade_value, f"labor_wage:{tx.transaction_type}")
                    if success and tax_amount > 0:
                         # Then Firm pays Tax to Gov
                        government.collect_tax(tax_amount, "income_tax_firm", buyer, current_time)
                else:
                    # Household pays tax (Withholding model)
                    # Pay GROSS wage to household
                    success = self.settlement.transfer(buyer, seller, trade_value, f"labor_wage_gross:{tx.transaction_type}")
                    if success and tax_amount > 0:
                        # Then collect tax from household
                        government.collect_tax(tax_amount, "income_tax_household", seller, current_time)

            elif tx.transaction_type == "dividend":
                success = self.settlement.transfer(seller, buyer, trade_value, "dividend_payment")

            elif tx.transaction_type == "tax":
                 # Atomic Collection via Government
                 result = government.collect_tax(trade_value, tx.item_id, buyer, current_time)
                 success = result['success']

            elif tx.transaction_type == "interest_payment":
                 success = self.settlement.transfer(buyer, seller, trade_value, "interest_payment")

            elif tx.transaction_type == "infrastructure_spending":
                 success = self.settlement.transfer(buyer, seller, trade_value, "infrastructure_spending")

            elif tx.transaction_type == "emergency_buy":
                 success = self.settlement.transfer(buyer, seller, trade_value, "emergency_buy")

            else:
                # Default Transfer (Zero-Sum)
                memo_id = tx.item_id if tx.item_id else tx.transaction_type
                success = self.settlement.transfer(buyer, seller, trade_value, f"generic:{tx.transaction_type}:{memo_id}")

            # ==================================================================
            # 3. State Commitment (Registry & Accounting)
            # ==================================================================
            if success:
                # Update Non-Financial State (Ownership, Inventory, Employment)
                # Registry handles logic based on transaction type
                self.registry.update_ownership(tx, buyer, seller, state)

                # Update Ledgers (Revenue, Expenses, Income Counters)
                self.accounting.record_transaction(tx, buyer, seller, trade_value, tax_amount)

                # WO-109: Deferred Effects
                if tx.metadata and tx.metadata.get("triggers_effect"):
                    state.effects_queue.append(tx.metadata)
