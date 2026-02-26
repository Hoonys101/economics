from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm
from modules.finance.api import ILoanRepayer, IExpenseTracker

logger = logging.getLogger(__name__)

class FinancialTransactionHandler(ITransactionHandler):
    """
    Handles financial transactions:
    - interest_payment (Expense)
    - dividend (Capital Income)
    - tax (Atomic Payment)
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        tx_type = tx.transaction_type
        trade_value = tx.total_pennies

        success = False

        if tx_type in ["interest_payment", "loan_interest", "deposit_interest", "deposit", "withdrawal", "bank_profit_remittance", "holding_cost"]:
             success = context.settlement_system.transfer(buyer, seller, trade_value, tx_type)

             if success and isinstance(buyer, IExpenseTracker):
                 buyer.record_expense(int(trade_value), tx.currency)

        elif tx_type == "dividend":
             success = context.settlement_system.transfer(seller, buyer, trade_value, "dividend_payment")

             if success and isinstance(buyer, Household):
                 # Household capital income tracking
                 # We assume Household implements this attribute. Ideally Protocol but attribute access is messy.
                 # Keeping hasattr check for now or just direct access if we trust type.
                 # Using direct access since Household is concrete here.
                 if hasattr(buyer, "capital_income_this_tick"):
                     buyer.capital_income_this_tick += int(trade_value)

        elif tx_type == "tax":
            # Atomic Settlement to Government
            # Buyer pays, Seller is typically None or Gov (transaction target).
            # We assume 'buyer' is the tax payer. 'seller' might be Gov or None.
            # TransactionProcessor logic: settle_atomic(buyer, [(gov, amount, item_id)])

            gov = context.government
            credits = [(gov, int(trade_value), tx.item_id)]

            success = context.settlement_system.settle_atomic(buyer, credits, context.time)

            if success:
                 # Gov record_revenue is complex (takes dict), not IRevenueTracker (takes int)
                 # Keeping as is for Gov
                 from modules.finance.dtos import TaxCollectionResult
                 gov.record_revenue(TaxCollectionResult(
                         success=True,
                         amount_collected=int(trade_value),
                         tax_type=tx.item_id,
                         payer_id=buyer.id,
                         payee_id=gov.id,
                         error_message=None
                     ))

                 # WO-116 Fix: Ensure Firms record tax as expense for accounting integrity
                 if isinstance(buyer, IExpenseTracker):
                     buyer.record_expense(int(trade_value), tx.currency)

        elif tx_type in ["repayment", "loan_repayment"]:
             # Transfer Only. No Expense Recording (Principal Repayment).
             success = context.settlement_system.transfer(buyer, seller, trade_value, tx_type)

             # Atomic Ledger Update (Phase 4.1)
             if success and tx_type == "loan_repayment":
                 # Update Ledger via Bank Interface
                 if isinstance(seller, ILoanRepayer):
                      seller.repay_loan(tx.item_id, int(trade_value))
                 elif hasattr(context, 'bank') and context.bank and isinstance(context.bank, ILoanRepayer):
                      # Fallback if seller isn't the bank object (e.g. ID mismatch or proxy)
                      context.bank.repay_loan(tx.item_id, int(trade_value))

        elif tx_type in ["investment"]:
             # Transfer + Expense Recording (CAPEX treated as expense for consistency)
             success = context.settlement_system.transfer(buyer, seller, trade_value, tx_type)
             if success and isinstance(buyer, IExpenseTracker):
                 buyer.record_expense(int(trade_value), tx.currency)

        return success is not None

    def rollback(self, tx: Transaction, context: TransactionContext) -> bool:
        """
        Reverses financial transactions by transferring funds back.
        """
        tx_type = tx.transaction_type
        trade_value = tx.total_pennies

        # Determine original Source (Buyer) and Destination (Seller/Gov)
        # Rollback: Destination pays Source

        source = context.agents.get(tx.buyer_id) or context.inactive_agents.get(tx.buyer_id)
        destination = context.agents.get(tx.seller_id) or context.inactive_agents.get(tx.seller_id)

        if tx_type == "tax":
            destination = context.government

        if not source or not destination:
            context.logger.error(f"Rollback failed for {tx.id}: Agent missing. Source: {tx.buyer_id}, Dest: {tx.seller_id}")
            return False

        success = context.settlement_system.transfer(destination, source, int(trade_value), f"rollback:{tx_type}:{tx.id}")

        if success and tx_type == "loan_repayment":
            context.logger.warning(f"Rollback for loan_repayment {tx.id} executed (money returned), but loan ledger NOT updated (principal not restored).")

        return success is not None
