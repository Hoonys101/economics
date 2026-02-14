from typing import Protocol, runtime_checkable, Optional, Dict, Any, TypedDict, Union, List
from abc import ABC, abstractmethod
from modules.finance.api import IFinancialAgent
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

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

@runtime_checkable
class IMintingSystem(Protocol):
    """
    Protocol for systems capable of minting currency (God Mode / Central Bank Injection).
    This capability is distinct from standard settlement to enforce Zero-Sum integrity elsewhere.
    """
    def mint_and_distribute(self, target_agent_id: int, amount: int, tick: int = 0, reason: str = "god_mode_injection") -> bool:
        ...

class ISettlementSystem(ABC):
    """
    Interface for the centralized settlement system.
    Ensures atomicity and zero-sum integrity of all financial transfers.
    """

    @abstractmethod
    def transfer(
        self,
        debit_agent: IFinancialAgent,
        credit_agent: IFinancialAgent,
        amount: int,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0,
        currency: CurrencyCode = DEFAULT_CURRENCY
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
            currency: The currency of the transfer.

        Returns:
            Transaction object if successful, None otherwise.
        """
        ...

    @abstractmethod
    def create_and_transfer(
        self,
        source_authority: IFinancialAgent,
        destination: IFinancialAgent,
        amount: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """
        Creates new money (or grants) and transfers it to an agent.
        Typically used for Government grants or Central Bank injections.
        """
        ...

    @abstractmethod
    def transfer_and_destroy(
        self,
        source: IFinancialAgent,
        sink_authority: IFinancialAgent,
        amount: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """
        Transfers money from an agent to an authority to be destroyed (or sequestered).
        Typically used for taxes or deflationary shocks.
        """
        ...

    @abstractmethod
    def record_liquidation(
        self,
        agent: IFinancialAgent,
        inventory_value: int,
        capital_value: int,
        recovered_cash: int,
        reason: str,
        tick: int,
        government_agent: Optional[IFinancialAgent] = None
    ) -> None:
        """
        Records the outcome of an asset liquidation.
        The system calculates the net asset destruction (inventory_value + capital_value - recovered_cash)
        and logs it to the money supply ledger.

        If `government_agent` is provided, any remaining assets (cash) in `agent` will be transferred
        to `government_agent` (Escheatment), ensuring zero-sum integrity.
        """
        ...

    @abstractmethod
    def register_account(self, bank_id: int, agent_id: int) -> None:
        """
        Registers an account link between a bank and an agent.
        Used to maintain the reverse index for bank runs.
        """
        ...

    @abstractmethod
    def deregister_account(self, bank_id: int, agent_id: int) -> None:
        """
        Removes an account link between a bank and an agent.
        """
        ...

    @abstractmethod
    def get_account_holders(self, bank_id: int) -> List[int]:
        """
        Returns a list of all agents holding accounts at the specified bank.
        This provides O(1) access to depositors for bank run simulation.
        """
        ...

    @abstractmethod
    def remove_agent_from_all_accounts(self, agent_id: int) -> None:
        """
        Removes an agent from all bank account indices.
        Called upon agent liquidation/deletion.
        """
        ...

    @abstractmethod
    def audit_total_m2(self, expected_total: Optional[int] = None) -> bool:
        """
        Audits the total M2 money supply in the system.
        Returns True if the audit passes (or no expectation set), False otherwise.
        """
        ...
