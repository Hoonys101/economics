"""
modules/agent_framework/components/financial_component.py

Implementation of the IFinancialComponent.
Wraps the Wallet and enforces strict penny-based arithmetic.
"""
from typing import Dict, Any, Optional
import logging

from modules.finance.api import IFinancialEntity, ICreditFrozen, CurrencyCode, DEFAULT_CURRENCY
from modules.finance.wallet.wallet import Wallet
from modules.agent_framework.api import IFinancialComponent, ComponentConfigDTO

logger = logging.getLogger(__name__)

class FinancialComponent(IFinancialComponent, ICreditFrozen):
    """
    Component handling financial state and operations.
    Delegates storage to Wallet but exposes strict typed interfaces.
    """

    def __init__(self, owner_id: str, allow_negative_balance: bool = False):
        self.owner_id = owner_id
        # Ensure owner_id is int for Wallet as per its type hint, fallback to 0 if not
        wallet_owner_id = int(owner_id) if owner_id.isdigit() else 0
        self._wallet = Wallet(wallet_owner_id, allow_negative_balance=allow_negative_balance)
        self._credit_frozen_until_tick: int = 0

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize wallet with starting balance."""
        initial_balance = config.get("initial_balance", 0)
        if initial_balance > 0:
            self._wallet.add(initial_balance, DEFAULT_CURRENCY, memo="Initial Balance")

    def force_reset_wallet(self) -> None:
        """Resets the wallet state."""
        self._wallet.load_balances({})

    def reset(self) -> None:
        """Reset tick-based counters or caches if any."""
        pass

    @property
    def credit_frozen_until_tick(self) -> int:
        return self._credit_frozen_until_tick

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None:
        self._credit_frozen_until_tick = value

    @property
    def balance_pennies(self) -> int:
        return self._wallet.get_balance(DEFAULT_CURRENCY)

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits funds into the wallet."""
        self._wallet.add(amount_pennies, currency, memo="FinancialComponent Deposit")

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Withdraws funds from the wallet."""
        # Wallet raises InsufficientFundsError if needed
        self._wallet.subtract(amount_pennies, currency, memo="FinancialComponent Withdrawal")

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Internal deposit implementation."""
        self.deposit(amount, currency)

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Internal withdraw implementation."""
        self.withdraw(amount, currency)

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """Returns the current balance for the specified currency."""
        return self._wallet.get_balance(currency)

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
        return self._wallet.get_all_balances()

    @property
    def total_wealth(self) -> int:
        """Returns the total wealth in default currency estimation."""
        balances = self._wallet.get_all_balances()
        return sum(balances.values())

    @property
    def wallet(self) -> Wallet:
        """Exposes the underlying Wallet instance."""
        return self._wallet

    @property
    def wallet_balance(self) -> int:
        return self.balance_pennies

    def get_net_worth(self, valuation_func: Optional[Any] = None) -> int:
        """
        Calculates total net worth.
        If valuation_func is provided, it should return the value of non-cash assets (pennies).
        """
        cash = self.balance_pennies
        non_cash = 0
        if valuation_func:
            non_cash = int(valuation_func())
        return cash + non_cash
