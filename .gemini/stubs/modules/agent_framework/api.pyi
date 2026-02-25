from abc import abstractmethod
from dataclasses import dataclass
from modules.finance.api import CurrencyCode as CurrencyCode, IFinancialEntity as IFinancialEntity
from modules.simulation.api import IInventoryHandler as IInventoryHandler, InventorySlot as InventorySlot, ItemDTO as ItemDTO
from typing import Any, Protocol

@dataclass(frozen=True)
class ComponentConfigDTO:
    """Base configuration for agent components."""
    owner_id: str
    debug_mode: bool = ...

class IAgentComponent(Protocol):
    """Base protocol for all agent components."""
    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the component with specific config."""
    @abstractmethod
    def reset(self) -> None:
        """Reset component state for a new tick/cycle."""

class IInventoryComponent(IInventoryHandler, Protocol):
    """
    Component responsible for managing agent inventory storage and quality.
    Strictly typed to replace ad-hoc dictionary manipulation.
    """
    @abstractmethod
    def load_from_state(self, inventory_data: dict[str, Any]) -> None:
        """Restores inventory state from a snapshot/DTO."""
    @abstractmethod
    def snapshot(self) -> dict[str, Any]:
        """Returns a serializable snapshot of the inventory."""
    @abstractmethod
    def get_inventory_value(self, price_map: dict[str, int]) -> int:
        """Calculates total value based on provided prices (pennies)."""

class IFinancialComponent(IFinancialEntity, Protocol):
    """
    Component responsible for wrapping the Wallet and enforcing financial protocols.
    Handles strict integer arithmetic and currency management.
    """
    @property
    @abstractmethod
    def wallet_balance(self) -> int:
        """Primary currency balance in pennies."""
    @abstractmethod
    def get_net_worth(self, valuation_func: Any | None = None) -> int:
        """Calculates total agent net worth (assets - liabilities)."""

class ITransactionOrchestrator(Protocol):
    """
    Encapsulates complex transaction generation logic previously embedded in Agents.
    """
    @abstractmethod
    def orchestrate(self, context: Any) -> list[Any]:
        """
        Executes the transaction generation pipeline.
        Returns a list of Transaction objects (opaque Any for loose coupling here).
        """

@dataclass
class InventoryStateDTO:
    main_slot: dict[str, float]
    main_quality: dict[str, float]
    input_slot: dict[str, float]
    input_quality: dict[str, float]

@dataclass
class FinancialStateDTO:
    balances: dict[CurrencyCode, int]
    credit_frozen_until: int
