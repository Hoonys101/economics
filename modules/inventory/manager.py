from typing import Dict, Optional, TYPE_CHECKING
import logging
from modules.simulation.api import IInventoryHandler

logger = logging.getLogger(__name__)

class InventoryManager(IInventoryHandler):
    """
    Component for managing inventory with quality tracking.
    Composition replacement for BaseAgent inventory logic.
    """

    def __init__(self, owner_id: int, inventory: Optional[Dict[str, float]] = None, quality: Optional[Dict[str, float]] = None):
        self.owner_id = owner_id
        self._inventory: Dict[str, float] = inventory if inventory is not None else {}
        self._inventory_quality: Dict[str, float] = quality if quality is not None else {} # Weighted average quality

    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0) -> bool:
        if quantity < 0:
            logger.warning(f"INVENTORY_FAIL | Agent {self.owner_id} attempt to add negative quantity {quantity} of {item_id}")
            return False

        current_qty = self._inventory.get(item_id, 0.0)
        current_quality = self._inventory_quality.get(item_id, 1.0)

        total_qty = current_qty + quantity
        if total_qty > 0:
            # Weighted average quality
            new_quality = ((current_qty * current_quality) + (quantity * quality)) / total_qty
            self._inventory_quality[item_id] = new_quality

        self._inventory[item_id] = total_qty
        return True

    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool:
        if quantity < 0:
            logger.warning(f"INVENTORY_FAIL | Agent {self.owner_id} attempt to remove negative quantity {quantity} of {item_id}")
            return False

        current = self._inventory.get(item_id, 0.0)
        if current < quantity - 1e-9: # Tolerance
            logger.warning(f"INVENTORY_FAIL | Agent {self.owner_id} insufficient {item_id}. Have {current}, Need {quantity}")
            return False

        self._inventory[item_id] = max(0.0, current - quantity)
        if self._inventory[item_id] <= 1e-9:
             if item_id in self._inventory: del self._inventory[item_id]
             if item_id in self._inventory_quality: del self._inventory_quality[item_id]

        return True

    def get_quantity(self, item_id: str) -> float:
        return self._inventory.get(item_id, 0.0)

    def get_quality(self, item_id: str) -> float:
        return self._inventory_quality.get(item_id, 1.0)

    def get_all_items(self) -> Dict[str, float]:
        return self._inventory.copy()

    def clear_inventory(self) -> None:
        self._inventory.clear()
        self._inventory_quality.clear()
