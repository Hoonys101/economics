from typing import Protocol

class IInventoryHandler(Protocol):
    """
    CANONICAL DEFINITION: Interface for managing an agent's inventory of consumable
    or sellable goods. Reflects the de-facto implementation across the codebase.
    """
    def add_item(self, item_id: str, quantity: float, transaction_id: str | None = None, quality: float = 1.0) -> bool:
        """Adds a specified quantity of an item to the inventory."""
    def remove_item(self, item_id: str, quantity: float, transaction_id: str | None = None) -> bool:
        """Removes a specified quantity of an item from the inventory. Returns False on failure."""
    def get_quantity(self, item_id: str) -> float:
        """Gets the current quantity of a specified item."""
    def get_quality(self, item_id: str) -> float:
        """Gets the average quality of a specified item."""
    def get_all_items(self) -> dict[str, float]:
        """Returns a copy of the entire inventory (item_id -> quantity)."""
    def clear_inventory(self) -> None:
        """Removes all items from the inventory."""
