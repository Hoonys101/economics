from typing import Any, Optional
import logging
from simulation.systems.api import IAccountingSystem
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm

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
        """
        tx_type = transaction.transaction_type

        # 1. Seller Revenue / Income
        if isinstance(seller, Firm):
            # Goods, Service, or any sales revenue
            if tx_type in ["goods", "service", "export"]: # Generic sales
                seller.record_revenue(amount, transaction.currency)
                if tx_type == "goods":
                     seller.finance_state.sales_volume_this_tick += transaction.quantity

        elif isinstance(seller, Household):
            if tx_type in ["labor", "research_labor"]:
                # Gross Income (before tax) or Net depending on where tax is handled.
                # TransactionProcessor logic:
                # "labor_income_this_tick += (trade_value - tax_amount)"
                # This implies labor_income_this_tick tracks NET income.
                net_income = amount - tax_amount
                if hasattr(seller, "labor_income_this_tick"):
                    seller.labor_income_this_tick += net_income

        # 2. Buyer Expenses
        if isinstance(buyer, Firm):
            if tx_type in ["labor", "research_labor"]:
                buyer.record_expense(amount, transaction.currency)
            elif tx_type == "interest_payment":
                 buyer.record_expense(amount, transaction.currency)
            # What about goods (raw materials)?
            # TD-SYS-ACCOUNTING-GAP: Raw material purchases are Asset Swaps (Cash -> Inventory).
            # Expense is recorded upon usage (COGS) in Firm.produce -> FinanceEngine.record_expense.
            # Therefore, we do NOT record expense here for raw materials to avoid double counting.
            pass

        # 3. Dividend Income
        if tx_type == "dividend":
             if isinstance(buyer, Household) and hasattr(buyer, "capital_income_this_tick"):
                 buyer.capital_income_this_tick += amount

        # 4. Interest Payment (Expense handled above)
        # 5. Tax (Expense?) - Usually tax is deducted or collected separately.

        # Note: TransactionProcessor._handle_goods_transaction did:
        # if isinstance(seller, Firm): seller.finance.record_revenue(trade_value) ...
        # It did NOT record expense for buyer (Firm or Household).
        # Household expense is implicit in asset reduction.
        # Firm expense for raw materials? TransactionProcessor checks 'is_raw_material' but only updates input_inventory.
        # This seems to be a legacy gap or handled elsewhere?
        # Actually Firm.produce might handle input costs or they are just assets converted.
        # But 'buying' raw material IS an expense of cash for asset.
        # Standard accounting: Cash Credit, Inventory Debit. No P&L Expense yet. Expense happens when used (COGS).
        # So it is correct not to record_expense on purchase.
