from _typeshed import Incomplete
from modules.agent_framework.api import ComponentConfigDTO as ComponentConfigDTO, IInventoryComponent as IInventoryComponent, InventoryStateDTO as InventoryStateDTO
from modules.simulation.api import InventorySlot as InventorySlot, ItemDTO as ItemDTO
from typing import Any

logger: Incomplete

class InventoryComponent(IInventoryComponent):
    """
    Component handling inventory management with quality tracking.
    Supports MAIN and INPUT slots.
    """
    owner_id: Incomplete
    def __init__(self, owner_id: str) -> None: ...
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize with optional starting inventory."""
    @property
    def main_inventory(self) -> dict[str, float]:
        """Exposes the main inventory dict (as in Firm legacy)."""
    @property
    def input_inventory(self) -> dict[str, float]:
        """Exposes the input inventory dict (as in Firm legacy)."""
    @property
    def inventory_quality(self) -> dict[str, float]:
        """Exposes the main inventory quality map (as in Firm legacy)."""
    def reset(self) -> None:
        """
        Reset logic if needed.
        Inventory usually persists across ticks, so this might be no-op
        or strictly for tick-based counters if we had any.
        """
    def add_item(self, item_id: str, quantity: float, transaction_id: str | None = None, quality: float = 1.0, slot: InventorySlot = ...) -> bool:
        """
        Adds item to the specified slot, updating weighted average quality.
        """
    def remove_item(self, item_id: str, quantity: float, transaction_id: str | None = None, slot: InventorySlot = ...) -> bool:
        """
        Removes item from the specified slot. Returns False if insufficient quantity.
        """
    def get_quantity(self, item_id: str, slot: InventorySlot = ...) -> float: ...
    def get_quality(self, item_id: str, slot: InventorySlot = ...) -> float: ...
    def get_all_items(self, slot: InventorySlot = ...) -> dict[str, float]: ...
    def clear_inventory(self, slot: InventorySlot = ...) -> None: ...
    def load_from_state(self, inventory_data: dict[str, Any]) -> None:
        """
        Restores state from a dictionary (typically from AgentStateDTO.inventories or similar).
        The format expected is DTO-like or raw dicts depending on usage.
        For now, assuming generic dict structure compatible with `InventoryStateDTO`.
        """
    def snapshot(self) -> dict[str, Any]:
        """Returns the internal state as a dictionary fitting InventoryStateDTO."""
    def get_inventory_value(self, price_map: dict[str, int]) -> int:
        """
        Calculates total value of MAIN inventory based on price map (pennies).
        """
