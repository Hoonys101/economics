from _typeshed import Incomplete
from modules.finance.utils.currency_math import round_to_pennies as round_to_pennies
from simulation.core_agents import Household as Household, Skill as Skill
from simulation.firms import Firm as Firm
from simulation.models import Transaction as Transaction
from simulation.systems.api import ITransactionHandler as ITransactionHandler, TransactionContext as TransactionContext
from typing import Any

logger: Incomplete

class LaborTransactionHandler(ITransactionHandler):
    """
    Handles 'labor' and 'research_labor' transactions.
    Enforces atomic settlement (Wage + Income Tax).
    """
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool: ...
    def rollback(self, tx: Transaction, context: TransactionContext) -> bool:
        """
        Reverses labor transactions.
        For wages, it attempts to reverse the payment.
        For hiring, it does not currently fire the employee but logs a warning.
        """
