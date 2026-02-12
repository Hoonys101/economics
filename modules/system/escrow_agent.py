from typing import Dict
from collections import defaultdict
from modules.finance.api import IFinancialAgent, InsufficientFundsError
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class EscrowAgent(IFinancialAgent):
    """
    Acts as a temporary holding account for atomic transactions.
    Ensures funds are secured before distribution to sellers and government.
    """
    def __init__(self, id: int):
        self._id = id
        self._balances: Dict[CurrencyCode, int] = defaultdict(int)

    @property
    def id(self) -> int:
        return self._id

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits funds (internal use)."""
        if amount < 0:
            raise ValueError("Deposit amount must be positive")
        self._balances[currency] += amount

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Withdraws funds (internal use)."""
        if amount < 0:
            raise ValueError("Withdraw amount must be positive")
        if self._balances[currency] < amount:
            raise InsufficientFundsError(f"EscrowAgent {self.id} has insufficient funds for {currency}. Needed: {amount}, Has: {self._balances[currency]}")
        self._balances[currency] -= amount

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self._balances[currency]

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return dict(self._balances)

    @property
    def total_wealth(self) -> int:
        return sum(self._balances.values())
