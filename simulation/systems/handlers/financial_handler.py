from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm

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

        if tx_type in ["interest_payment", "loan_interest", "deposit_interest", "deposit", "withdrawal", "bank_profit_remittance"]:
             success = context.settlement_system.transfer(buyer, seller, trade_value, tx_type)

             if success and isinstance(buyer, Firm):
                 buyer.record_expense(int(trade_value), tx.currency)

        elif tx_type == "dividend":
             success = context.settlement_system.transfer(seller, buyer, trade_value, "dividend_payment")

             if success and isinstance(buyer, Household) and hasattr(buyer, "capital_income_this_tick"):
                 # capital_income_this_tick is int in EconStateDTO
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
                 gov.record_revenue({
                         "success": True,
                         "amount_collected": int(trade_value),
                         "tax_type": tx.item_id,
                         "payer_id": buyer.id,
                         "payee_id": gov.id,
                         "error_message": None
                     })

                 # WO-116 Fix: Ensure Firms record tax as expense for accounting integrity
                 if isinstance(buyer, Firm):
                     buyer.record_expense(int(trade_value), tx.currency)

        return success is not None
