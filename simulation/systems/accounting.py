from typing import Any, Optional
import logging
from simulation.systems.api import IAccountingSystem
from simulation.models import Transaction

logger = logging.getLogger(__name__)

class AccountingSystem(IAccountingSystem):
    """
    Updates internal financial ledgers: Revenue, Expenses, Income Counters.
    Does NOT move assets.
    Extracted from TransactionProcessor.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger if logger else logging.getLogger(__name__)

    def record_transaction(self, transaction: Transaction, buyer: Any, seller: Any, amount: float, tax_amount: float = 0.0) -> None:
        """
        Updates financial records based on transaction type.
        Uses Duck Typing to avoid circular dependencies with Agent classes.
        """
        tx_type = transaction.transaction_type

        # 1. Seller Revenue / Income
        if hasattr(seller, 'record_revenue'):
            # Firm-like entity
            if tx_type in ["goods", "service", "export"]: # Generic sales
                seller.record_revenue(amount, transaction.currency)

                # Update sales volume if applicable (Legacy support)
                if tx_type == "goods":
                    # Check for finance_state.sales_volume_this_tick
                    if hasattr(seller, 'finance_state') and hasattr(seller.finance_state, 'sales_volume_this_tick'):
                        seller.finance_state.sales_volume_this_tick += transaction.quantity
                    # Or instance level (New Architecture)
                    elif hasattr(seller, 'sales_volume_this_tick'):
                        seller.sales_volume_this_tick += transaction.quantity

        elif hasattr(seller, 'labor_income_this_tick'):
            # Household-like entity (Labor Provider)
            if tx_type in ["labor", "research_labor"]:
                # Gross Income (before tax) or Net depending on where tax is handled.
                # TransactionProcessor logic implies labor_income_this_tick tracks NET income if tax_amount passed.
                net_income = amount - tax_amount
                try:
                    seller.labor_income_this_tick += net_income
                except TypeError:
                    # Handle case where it might be None or method
                    pass

        # 2. Buyer Expenses
        if hasattr(buyer, 'record_expense'):
            # Firm-like entity
            if tx_type in ["labor", "research_labor", "interest_payment", "service"]:
                buyer.record_expense(amount, transaction.currency)
            # WO-LIQUIDATE-FINANCE: Reciprocal expense for goods (Inputs)
            elif tx_type == "goods":
                buyer.record_expense(amount, transaction.currency)

        elif hasattr(buyer, 'add_consumption_expenditure'):
             # Household-like entity
             if tx_type in ["goods", "service", "housing", "food", "luxury_goods", "basic_goods"]:
                 # Ensure int pennies
                 buyer.add_consumption_expenditure(int(amount), item_id=transaction.item_id)

        # 3. Dividend Income
        if tx_type == "dividend":
             if hasattr(buyer, "capital_income_this_tick"):
                 try:
                     buyer.capital_income_this_tick += amount
                 except TypeError:
                     pass
