from typing import Protocol, runtime_checkable, Dict, Any
from modules.simulation.api import AgentID
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

@runtime_checkable
class IFinancialEntity(Protocol):
    """
    Standard interface for any entity capable of holding and transferring financial value.
    Replaces legacy `hasattr` checks and standardizes on integer pennies.
    """
    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
        ...

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits funds into the entity's wallet."""
        ...

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Withdraws funds from the entity's wallet."""
        ...

@runtime_checkable
class IFinancialAgent(IFinancialEntity, Protocol):
    """
    Protocol for agents participating in the financial system.
    """
    id: AgentID

    def get_liquid_assets(self, currency: CurrencyCode = "USD") -> int:
        ...

    def get_total_debt(self) -> int:
        ...

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits a specific amount of a given currency. Internal use only."""
        ...

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws a specific amount of a given currency.
        Raises InsufficientFundsError if funds are insufficient.
        Internal use only.
        """
        ...

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """Returns the current balance for the specified currency."""
        ...

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
        ...

    @property
    def total_wealth(self) -> int:
        """Returns the total wealth in default currency estimation."""
        ...
