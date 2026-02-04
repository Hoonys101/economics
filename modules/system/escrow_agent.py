from typing import Dict
from collections import defaultdict
from modules.finance.api import IFinancialEntity, InsufficientFundsError
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class EscrowAgent(IFinancialEntity):
    """
    Acts as a temporary holding account for atomic transactions.
    Ensures funds are secured before distribution to sellers and government.
    """
    def __init__(self, id: int):
        self._id = id
        self._balances: Dict[CurrencyCode, float] = defaultdict(float)

    @property
    def id(self) -> int:
        return self._id

    @property
    def assets(self) -> Dict[CurrencyCode, float]:
        return dict(self._balances)

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if amount < 0:
            raise ValueError("Deposit amount must be positive")
        self._balances[currency] += amount

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if amount < 0:
            raise ValueError("Withdraw amount must be positive")
        if self._balances[currency] < amount:
            raise InsufficientFundsError(f"EscrowAgent {self.id} has insufficient funds for {currency}. Needed: {amount}, Has: {self._balances[currency]}")
        self._balances[currency] -= amount
