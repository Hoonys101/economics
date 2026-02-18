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
from modules.government.constants import DEFAULT_BASIC_FOOD_PRICE
from modules.finance.transaction.handlers import GoodsTransactionHandler, LaborTransactionHandler

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

        # Default Handlers
        if "goods" not in self.handlers:
            self.handlers["goods"] = GoodsTransactionHandler()
        if "labor" not in self.handlers:
            self.handlers["labor"] = LaborTransactionHandler()
        if "research_labor" not in self.handlers:
            self.handlers["research_labor"] = LaborTransactionHandler()

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

        for tx in transactions:
            # Phase 3: Public Manager Support
            if tx.seller_id == "PUBLIC_MANAGER" or tx.seller_id == -1:
                buyer = agents.get(tx.buyer_id) or inactive_agents.get(tx.buyer_id)
                if not buyer:
                    continue

                trade_value = int(tx.quantity * tx.price)

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

            trade_value = int(tx.quantity * tx.price)
            if tx.total_pennies > 0:
                 trade_value = tx.total_pennies

            tax_amount = 0
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
