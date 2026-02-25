from modules.simulation.api import AgentID as AgentID
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from typing import Protocol

class IFinancialEntity(Protocol):
    """
    Standard interface for any entity capable of holding and transferring financial value.
    Replaces legacy `hasattr` checks and standardizes on integer pennies.
    """
    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
    def deposit(self, amount_pennies: int, currency: CurrencyCode = ...) -> None:
        """Deposits funds into the entity's wallet."""
    def withdraw(self, amount_pennies: int, currency: CurrencyCode = ...) -> None:
        """Withdraws funds from the entity's wallet."""

class IFinancialAgent(IFinancialEntity, Protocol):
    """
    Protocol for agents participating in the financial system.
    """
    id: AgentID
    def get_liquid_assets(self, currency: CurrencyCode = 'USD') -> int: ...
    def get_total_debt(self) -> int: ...
    def get_balance(self, currency: CurrencyCode = ...) -> int:
        """Returns the current balance for the specified currency."""
    def get_all_balances(self) -> dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
    @property
    def total_wealth(self) -> int:
        """Returns the total wealth in default currency estimation."""
