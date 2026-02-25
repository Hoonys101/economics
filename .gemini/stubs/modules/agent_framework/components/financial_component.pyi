from _typeshed import Incomplete
from modules.agent_framework.api import ComponentConfigDTO as ComponentConfigDTO, IFinancialComponent as IFinancialComponent
from modules.finance.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY, ICreditFrozen as ICreditFrozen, IFinancialEntity as IFinancialEntity
from modules.finance.wallet.wallet import Wallet as Wallet
from typing import Any

logger: Incomplete

class FinancialComponent(IFinancialComponent, ICreditFrozen):
    """
    Component handling financial state and operations.
    Delegates storage to Wallet but exposes strict typed interfaces.
    """
    owner_id: Incomplete
    def __init__(self, owner_id: str, allow_negative_balance: bool = False) -> None: ...
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize wallet with starting balance."""
    def force_reset_wallet(self) -> None:
        """Resets the wallet state."""
    def reset(self) -> None:
        """Reset tick-based counters or caches if any."""
    @property
    def credit_frozen_until_tick(self) -> int: ...
    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None: ...
    @property
    def balance_pennies(self) -> int: ...
    def deposit(self, amount_pennies: int, currency: CurrencyCode = ...) -> None:
        """Deposits funds into the wallet."""
    def withdraw(self, amount_pennies: int, currency: CurrencyCode = ...) -> None:
        """Withdraws funds from the wallet."""
    def get_balance(self, currency: CurrencyCode = ...) -> int:
        """Returns the current balance for the specified currency."""
    def get_all_balances(self) -> dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
    @property
    def total_wealth(self) -> int:
        """Returns the total wealth in default currency estimation."""
    @property
    def wallet(self) -> Wallet:
        """Exposes the underlying Wallet instance."""
    @property
    def wallet_balance(self) -> int: ...
    def get_net_worth(self, valuation_func: Any | None = None) -> int:
        """
        Calculates total net worth.
        If valuation_func is provided, it should return the value of non-cash assets (pennies).
        """
