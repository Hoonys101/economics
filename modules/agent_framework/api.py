"""
modules/agent_framework/api.py

Defines the reusable Component Interfaces for the "Agent Shell" pattern.
This module facilitates the decomposition of God Class Agents (Firm/Household)
into lightweight orchestrators composed of specialized components.
"""
from typing import Protocol, Dict, Any, Optional, List, TypeVar, runtime_checkable
from abc import abstractmethod
from dataclasses import dataclass

from modules.simulation.api import InventorySlot, ItemDTO, IInventoryHandler
from modules.finance.api import CurrencyCode, IFinancialEntity

@dataclass(frozen=True)
class ComponentConfigDTO:
    """Base configuration for agent components."""
    owner_id: str
    debug_mode: bool = False

@runtime_checkable
class IAgentComponent(Protocol):
    """Base protocol for all agent components."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the component with specific config."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset component state for a new tick/cycle."""
        ...

@runtime_checkable
class IInventoryComponent(IInventoryHandler, Protocol):
    """
    Component responsible for managing agent inventory storage and quality.
    Strictly typed to replace ad-hoc dictionary manipulation.
    """

    @abstractmethod
    def load_from_state(self, inventory_data: Dict[str, Any]) -> None:
        """Restores inventory state from a snapshot/DTO."""
        ...

    @abstractmethod
    def snapshot(self) -> Dict[str, Any]:
        """Returns a serializable snapshot of the inventory."""
        ...

    @abstractmethod
    def get_inventory_value(self, price_map: Dict[str, int]) -> int:
        """Calculates total value based on provided prices (pennies)."""
        ...

@runtime_checkable
class IFinancialComponent(IFinancialEntity, Protocol):
    """
    Component responsible for wrapping the Wallet and enforcing financial protocols.
    Handles strict integer arithmetic and currency management.
    """

    @property
    @abstractmethod
    def wallet_balance(self) -> int:
        """Primary currency balance in pennies."""
        ...

    @abstractmethod
    def get_net_worth(self, valuation_func: Optional[Any] = None) -> int:
        """Calculates total agent net worth (assets - liabilities)."""
        ...

@runtime_checkable
class ITransactionOrchestrator(Protocol):
    """
    Encapsulates complex transaction generation logic previously embedded in Agents.
    """

    @abstractmethod
    def orchestrate(self, context: Any) -> List[Any]:
        """
        Executes the transaction generation pipeline.
        Returns a list of Transaction objects (opaque Any for loose coupling here).
        """
        ...

# DTOs for Component State
@dataclass
class InventoryStateDTO:
    main_slot: Dict[str, float]
    main_quality: Dict[str, float]
    input_slot: Dict[str, float]
    input_quality: Dict[str, float]

@dataclass
class FinancialStateDTO:
    balances: Dict[CurrencyCode, int]
    credit_frozen_until: int
