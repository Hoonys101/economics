from typing import Protocol, runtime_checkable, Optional, Dict, Any, TypedDict, Union
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

class ITransaction(TypedDict):
    """
    Represents a financial transaction result.
    Compatible with simulation.models.Transaction fields.
    """
    buyer_id: int
    seller_id: int
    item_id: str
    quantity: float
    price: float
    market_id: str
    transaction_type: str
    time: int
    metadata: Optional[Dict[str, Any]]

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
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0
    ) -> Optional[ITransaction]:
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
            tick: The current simulation tick.

        Returns:
            Transaction object if successful, None otherwise.
        """
        ...

    @abstractmethod
    def create_and_transfer(
        self,
        source_authority: IFinancialEntity,
        destination: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int
    ) -> Optional[ITransaction]:
        """
        Creates new money (or grants) and transfers it to an agent.
        Typically used for Government grants or Central Bank injections.
        """
        ...

    @abstractmethod
    def transfer_and_destroy(
        self,
        source: IFinancialEntity,
        sink_authority: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int
    ) -> Optional[ITransaction]:
        """
        Transfers money from an agent to an authority to be destroyed (or sequestered).
        Typically used for taxes or deflationary shocks.
        """
        ...

    @abstractmethod
    def record_liquidation(
        self,
        agent: IFinancialEntity,
        inventory_value: float,
        capital_value: float,
        recovered_cash: float,
        reason: str,
        tick: int,
        government_agent: Optional[IFinancialEntity] = None
    ) -> None:
        """
        Records the outcome of an asset liquidation.
        The system calculates the net asset destruction (inventory_value + capital_value - recovered_cash)
        and logs it to the money supply ledger.

        If `government_agent` is provided, any remaining assets (cash) in `agent` will be transferred
        to `government_agent` (Escheatment), ensuring zero-sum integrity.
        """
        ...
