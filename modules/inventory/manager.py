from typing import Dict, Optional, TYPE_CHECKING
import logging
from modules.simulation.api import IInventoryHandler, InventorySlot
from modules.common.protocol import enforce_purity

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

    @enforce_purity()
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        if slot != InventorySlot.MAIN:
            # TODO: Support other slots if needed, for now just log warning or ignore
            # logger.warning(f"InventoryManager only supports MAIN slot currently. Requested: {slot}")
            pass

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

    @enforce_purity()
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        if slot != InventorySlot.MAIN:
             return False

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

    def get_quantity(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        if slot != InventorySlot.MAIN:
            return 0.0
        return self._inventory.get(item_id, 0.0)

    def get_quality(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        if slot != InventorySlot.MAIN:
            return 1.0
        return self._inventory_quality.get(item_id, 1.0)

    def get_all_items(self, slot: InventorySlot = InventorySlot.MAIN) -> Dict[str, float]:
        if slot != InventorySlot.MAIN:
            return {}
        return self._inventory.copy()

    def clear_inventory(self, slot: InventorySlot = InventorySlot.MAIN) -> None:
        if slot == InventorySlot.MAIN:
            self._inventory.clear()
            self._inventory_quality.clear()
