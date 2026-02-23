from abc import abstractmethod
from dataclasses import dataclass
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from typing import Protocol

@dataclass(frozen=True)
class WalletOpLogDTO:
    """A record of a single atomic operation on a wallet."""
    tick: int
    agent_id: int
    currency: CurrencyCode
    delta: int
    memo: str
    resulting_balance: int

class IWallet(Protocol):
    """
    Defines the public interface for a currency wallet.
    It provides methods for atomic balance manipulation and observation.
    MIGRATION: All monetary values are integers (pennies).
    """
    owner_id: int
    @abstractmethod
    def get_balance(self, currency: CurrencyCode = ...) -> int:
        """Retrieves the balance for a specific currency."""
    @abstractmethod
    def get_all_balances(self) -> dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
    @abstractmethod
    def add(self, amount: int, currency: CurrencyCode = ..., memo: str = '', tick: int = -1) -> None:
        """Atomically adds an amount to a currency's balance."""
    @abstractmethod
    def subtract(self, amount: int, currency: CurrencyCode = ..., memo: str = '', tick: int = -1) -> None:
        """Atomically subtracts an amount from a currency's balance."""
    @abstractmethod
    def __add__(self, other: IWallet) -> IWallet: ...
    @abstractmethod
    def __sub__(self, other: IWallet) -> IWallet: ...
    @abstractmethod
    def __iadd__(self, other: IWallet) -> IWallet: ...
    @abstractmethod
    def __isub__(self, other: IWallet) -> IWallet: ...
