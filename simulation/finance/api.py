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
        Executes an atomic transfer from debit_agent to credit_agent.

        Args:
            debit_agent: The sender (assets will decrease).
            credit_agent: The receiver (assets will increase).
            amount: The amount to transfer (must be positive).
            memo: Description of the transaction for audit logging.
            debit_context: Optional metadata for the debit side logic.
            credit_context: Optional metadata for the credit side logic.

        Returns:
            bool: True if transfer succeeded, False otherwise (e.g., insufficient funds).
        """
        ...
