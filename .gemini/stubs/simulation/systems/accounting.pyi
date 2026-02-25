import logging
from _typeshed import Incomplete
from simulation.models import Transaction as Transaction
from simulation.systems.api import IAccountingSystem as IAccountingSystem
from typing import Any

logger: Incomplete

class AccountingSystem(IAccountingSystem):
    """
    Updates internal financial ledgers: Revenue, Expenses, Income Counters.
    Does NOT move assets.
    Extracted from TransactionProcessor.
    """
    logger: Incomplete
    def __init__(self, logger: logging.Logger | None = None) -> None: ...
    def record_transaction(self, transaction: Transaction, buyer: Any, seller: Any, amount: float, tax_amount: float = 0.0) -> None:
        """
        Updates financial records based on transaction type.
        Uses Duck Typing to avoid circular dependencies with Agent classes.
        """
