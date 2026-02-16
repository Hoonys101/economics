"""
modules/agent_framework/components/inventory_component.py

Implementation of the IInventoryComponent.
Manages inventory slots (MAIN, INPUT), quality tracking, and serialization.
"""
from typing import Dict, Any, Optional, List
import logging

from modules.simulation.api import InventorySlot, ItemDTO
from modules.agent_framework.api import IInventoryComponent, ComponentConfigDTO, InventoryStateDTO

logger = logging.getLogger(__name__)

class InventoryComponent(IInventoryComponent):
    """
    Component handling inventory management with quality tracking.
    Supports MAIN and INPUT slots.
    """

    def __init__(self, owner_id: str):
        self.owner_id = owner_id
        # State
        self._main_inventory: Dict[str, float] = {}
        self._main_quality: Dict[str, float] = {}
        self._input_inventory: Dict[str, float] = {}
        self._input_quality: Dict[str, float] = {}

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize with optional starting inventory."""
        # Config might contain 'initial_inventory'
        initial_inv = config.get("initial_inventory")
        if initial_inv and isinstance(initial_inv, dict):
            for item_id, qty in initial_inv.items():
                self.add_item(item_id, float(qty))

    def reset(self) -> None:
        """
        Reset logic if needed.
        Inventory usually persists across ticks, so this might be no-op
        or strictly for tick-based counters if we had any.
        """
        pass

    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        """
        Adds item to the specified slot, updating weighted average quality.
        """
        if quantity < 0:
            return False

        current_qty = self.get_quantity(item_id, slot)
        current_quality = self.get_quality(item_id, slot)

        total_qty = current_qty + quantity

        # Select target references
        if slot == InventorySlot.MAIN:
            inv_ref = self._main_inventory
            qual_ref = self._main_quality
        elif slot == InventorySlot.INPUT:
            inv_ref = self._input_inventory
            qual_ref = self._input_quality
        else:
            return False

        # Update Quality (Weighted Average)
        if total_qty > 0:
            new_avg_quality = ((current_qty * current_quality) + (quantity * quality)) / total_qty
            qual_ref[item_id] = new_avg_quality

        # Update Quantity
        inv_ref[item_id] = total_qty
        return True

    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        """
        Removes item from the specified slot. Returns False if insufficient quantity.
        """
        if quantity < 0:
            return False

        if slot == InventorySlot.MAIN:
            inv_ref = self._main_inventory
        elif slot == InventorySlot.INPUT:
            inv_ref = self._input_inventory
        else:
            return False

        current = inv_ref.get(item_id, 0.0)
        if current < quantity:
            return False

        new_qty = current - quantity
        inv_ref[item_id] = new_qty

        # Cleanup small floating point residuals
        if inv_ref[item_id] <= 1e-9:
            if item_id in inv_ref:
                del inv_ref[item_id]
            # We don't necessarily delete quality info, keeping it for history or future adds is fine,
            # but usually we can clean it up to save memory if needed.
            # Firm implementation didn't seem to explicitly delete quality on empty,
            # but usually it's safer to keep it or let it be overwritten on next add.

        return True

    def get_quantity(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        if slot == InventorySlot.MAIN:
            return self._main_inventory.get(item_id, 0.0)
        elif slot == InventorySlot.INPUT:
            return self._input_inventory.get(item_id, 0.0)
        return 0.0

    def get_quality(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        if slot == InventorySlot.MAIN:
            return self._main_quality.get(item_id, 1.0)
        elif slot == InventorySlot.INPUT:
            return self._input_quality.get(item_id, 1.0)
        return 1.0

    def get_all_items(self, slot: InventorySlot = InventorySlot.MAIN) -> Dict[str, float]:
        if slot == InventorySlot.MAIN:
            return self._main_inventory.copy()
        elif slot == InventorySlot.INPUT:
            return self._input_inventory.copy()
        return {}

    def clear_inventory(self, slot: InventorySlot = InventorySlot.MAIN) -> None:
        if slot == InventorySlot.MAIN:
            self._main_inventory.clear()
            self._main_quality.clear()
        elif slot == InventorySlot.INPUT:
            self._input_inventory.clear()
            self._input_quality.clear()

    def load_from_state(self, inventory_data: Dict[str, Any]) -> None:
        """
        Restores state from a dictionary (typically from AgentStateDTO.inventories or similar).
        The format expected is DTO-like or raw dicts depending on usage.
        For now, assuming generic dict structure compatible with `InventoryStateDTO`.
        """
        # If input is InventoryStateDTO (as dict)
        if "main_slot" in inventory_data:
            self._main_inventory = inventory_data.get("main_slot", {}).copy()
            self._main_quality = inventory_data.get("main_quality", {}).copy()
            self._input_inventory = inventory_data.get("input_slot", {}).copy()
            self._input_quality = inventory_data.get("input_quality", {}).copy()
        else:
            # Fallback or other format handling
            pass

    def snapshot(self) -> Dict[str, Any]:
        """Returns the internal state as a dictionary fitting InventoryStateDTO."""
        return {
            "main_slot": self._main_inventory.copy(),
            "main_quality": self._main_quality.copy(),
            "input_slot": self._input_inventory.copy(),
            "input_quality": self._input_quality.copy()
        }

    def get_inventory_value(self, price_map: Dict[str, int]) -> int:
        """
        Calculates total value of MAIN inventory based on price map (pennies).
        """
        total_val = 0
        for item_id, qty in self._main_inventory.items():
            price = price_map.get(item_id, 0)
            total_val += int(qty * price)
        return total_val
