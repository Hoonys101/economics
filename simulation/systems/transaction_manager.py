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
from modules.finance.utils.currency_math import round_to_pennies

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
        escrow_agent: Any, # IFinancialEntity
        handlers: Optional[Dict[str, ISpecializedTransactionHandler]] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.registry = registry
        self.accounting = accounting_system
        self.settlement = settlement_system
        self.central_bank = central_bank_system
        self.config = config
        self.escrow_agent = escrow_agent
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
            # Phase 3: Public Manager Support
            if tx.seller_id == "PUBLIC_MANAGER" or tx.seller_id == -1:
                buyer = agents.get(tx.buyer_id) or inactive_agents.get(tx.buyer_id)
                if not buyer:
                    continue

                trade_value = tx.quantity * tx.price

                # Debit Buyer & Credit Public Manager
                try:
                    # Manually withdraw from buyer (simulating payment to system)
                    buyer.withdraw(trade_value)

                    # Credit Public Manager Treasury
                    if hasattr(state, "public_manager") and state.public_manager:
                        state.public_manager.deposit_revenue(trade_value)
                        state.public_manager.confirm_sale(tx.item_id, tx.quantity)

                    # Trigger state updates (Ownership, etc.)
                    # Pass seller as None (Registry handles None seller safely by skipping seller updates)
                    self.registry.update_ownership(tx, buyer, None, state)

                    # Record for accounting (Seller=None)
                    self.accounting.record_transaction(tx, buyer, None, trade_value, 0.0)

                except Exception as e:
                    import traceback
                    self.logger.error(f"PUBLIC_MANAGER transaction failed: {e}\n{traceback.format_exc()}")

                continue

            buyer = agents.get(tx.buyer_id) or inactive_agents.get(tx.buyer_id)
            seller = agents.get(tx.seller_id) or inactive_agents.get(tx.seller_id)

            if not buyer and not seller:
                continue

            trade_value = round_to_pennies(tx.quantity * tx.price)
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

            elif tx.transaction_type == "omo_purchase":
                 # OMO Purchase: CB buys from Agent. Minting.
                 # Buyer: CentralBank (ID=-2), Seller: Agent
                 success = self.central_bank.mint_and_transfer(seller, trade_value, "omo_purchase")
                 if success:
                     if hasattr(government, "total_money_issued"):
                         government.total_money_issued += trade_value
                     # Notify CentralBankSystem for logging
                     self.central_bank.process_omo_settlement(tx)

            elif tx.transaction_type == "omo_sale":
                 # OMO Sale: Agent buys from CB. Burning.
                 # Buyer: Agent, Seller: CentralBank
                 success = self.central_bank.transfer_and_burn(buyer, trade_value, "omo_sale")
                 if success:
                     if hasattr(government, "total_money_destroyed"):
                         government.total_money_destroyed += trade_value
                     # Notify CentralBankSystem for logging
                     self.central_bank.process_omo_settlement(tx)

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
                total_cost = trade_value + tax_amount

                # Solvency Check (Legacy compatibility)
                if hasattr(buyer, 'check_solvency'):
                    if buyer.assets < total_cost:
                        buyer.check_solvency(government)

                # --- 3-Step Escrow Logic (Atomic) ---
                # 1. Secure Total Amount in Escrow
                memo_escrow = f"escrow_hold:{tx.item_id}"
                escrow_success = self.settlement.transfer(
                    buyer,
                    self.escrow_agent,
                    total_cost,
                    memo_escrow
                )

                if not escrow_success:
                    success = False
                else:
                    # 2. Distribute Funds from Escrow
                    try:
                        # 2a. Pay Seller
                        memo_trade = f"goods_trade:{tx.item_id}"
                        trade_success = self.settlement.transfer(
                            self.escrow_agent,
                            seller,
                            trade_value,
                            memo_trade
                        )

                        if not trade_success:
                            # Critical Failure: Funds stuck in escrow. Rollback buyer.
                            self.logger.critical(f"ESCROW_FAIL | Trade transfer to seller failed. Rolling back {total_cost} to buyer {buyer.id}.")
                            self.settlement.transfer(self.escrow_agent, buyer, total_cost, "escrow_reversal:trade_failure")
                            success = False
                        else:
                            # 2b. Pay Tax to Government
                            if tax_amount > 0:
                                memo_tax = f"sales_tax:{tx.item_id}"
                                # Push tax to Government via Settlement
                                tax_success = self.settlement.transfer(
                                    self.escrow_agent,
                                    government,
                                    tax_amount,
                                    memo_tax
                                )

                                if not tax_success:
                                    # Critical Failure: Tax transfer failed. Rollback everything.
                                    self.logger.critical(f"ESCROW_FAIL | Tax transfer to government failed. Rolling back trade and escrow.")
                                    # Revert seller payment
                                    self.settlement.transfer(seller, self.escrow_agent, trade_value, "reversal:tax_failure")
                                    # Return all to buyer
                                    self.settlement.transfer(self.escrow_agent, buyer, total_cost, "escrow_reversal:tax_failure")
                                    success = False
                                else:
                                    success = True
                                    # Explicitly record tax revenue since we bypassed collect_tax
                                    # Using a mock result as record_revenue expects TaxCollectionResult
                                    if hasattr(government, 'record_revenue'):
                                        government.record_revenue({
                                            "success": True,
                                            "amount_collected": tax_amount,
                                            "tax_type": f"sales_tax_{tx.transaction_type}",
                                            "payer_id": buyer.id,
                                            "payee_id": government.id,
                                            "error_message": None
                                        })
                            else:
                                success = True

                    except Exception as e:
                        self.logger.exception(f"ESCROW_EXCEPTION | Unexpected error during distribution: {e}")
                        success = False

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
                # TaxService logic likely expects dollars (float)
                tax_amount_float = government.calculate_income_tax(trade_value / 100.0, survival_cost)
                tax_amount = round_to_pennies(tax_amount_float * 100)

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
