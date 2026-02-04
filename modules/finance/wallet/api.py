from __future__ import annotations
from typing import Dict, Protocol, runtime_checkable, List
from abc import abstractmethod
from dataclasses import dataclass
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

@dataclass(frozen=True)
class WalletOpLogDTO:
    """A record of a single atomic operation on a wallet."""
    tick: int
    agent_id: int
    currency: CurrencyCode
    delta: float
    memo: str
    resulting_balance: float

@runtime_checkable
class IWallet(Protocol):
    """
    Defines the public interface for a currency wallet.
    It provides methods for atomic balance manipulation and observation.
    """
    owner_id: int

    @abstractmethod
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        """Retrieves the balance for a specific currency."""
        ...

    @abstractmethod
    def get_all_balances(self) -> Dict[CurrencyCode, float]:
        """Returns a copy of all currency balances."""
        ...

    @abstractmethod
    def add(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "", tick: int = -1) -> None:
        """Atomically adds an amount to a currency's balance."""
        ...

    @abstractmethod
    def subtract(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "", tick: int = -1) -> None:
        """Atomically subtracts an amount from a currency's balance."""
        ...

    # --- Operator Overloading Signatures ---
    @abstractmethod
    def __add__(self, other: IWallet) -> IWallet: ...

    @abstractmethod
    def __sub__(self, other: IWallet) -> IWallet: ...

    @abstractmethod
    def __iadd__(self, other: IWallet) -> IWallet: ...

    @abstractmethod
    def __isub__(self, other: IWallet) -> IWallet: ...
