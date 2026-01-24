from typing import Protocol, runtime_checkable, Optional, Dict, Any
from abc import ABC, abstractmethod

@runtime_checkable
class IFinancialEntity(Protocol):
    """
    Protocol for any entity that possesses assets and participates in financial transactions.
    Assets are read-only to the public; state changes must occur via the SettlementSystem
    calling the protected _add_assets / _sub_assets methods (or equivalent internal logic).
    """
    id: int

    @property
    def assets(self) -> float:
        """Current assets (Read-Only)."""
        ...

    def _add_assets(self, amount: float) -> None:
        """
        [PROTECTED] Increase assets.
        Should ONLY be called by SettlementSystem.
        """
        ...

    def _sub_assets(self, amount: float) -> None:
        """
        [PROTECTED] Decrease assets.
        Should ONLY be called by SettlementSystem.
        """
        ...


class ISettlementSystem(ABC):
    """
    Interface for the centralized settlement system.
    Ensures atomicity and zero-sum integrity of all financial transfers.
    """

    @abstractmethod
    def transfer(
        self,
        debit_agent: IFinancialEntity,
        credit_agent: IFinancialEntity,
        amount: float,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Atomically transfers an amount from one financial entity to another.

        This operation MUST be atomic. It checks if the debit_agent has
        sufficient funds. If so, it debits the debit_agent and credits the
        credit_agent. If not, the operation fails and no state is changed.

        Args:
            debit_agent: The entity from which to withdraw funds.
            credit_agent: The entity to which to deposit funds.
            amount: The amount to transfer.
            memo: A description of the transaction.
            debit_context: Optional metadata for the debit side logic.
            credit_context: Optional metadata for the credit side logic.

        Returns:
            True if the transfer was successful, False otherwise.
        """
        ...
