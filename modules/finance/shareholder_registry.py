from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Optional
from modules.finance.api import IShareholderRegistry, ShareholderData

class ShareholderRegistry:
    """
    Centralized service for tracking corporate share ownership.
    Implements IShareholderRegistry protocol.
    Single source of truth for stock ownership, replacing scattered dictionaries.
    """

    def __init__(self):
        # firm_id -> agent_id -> quantity
        self._registry: Dict[int, Dict[int, float]] = defaultdict(lambda: defaultdict(float))

    def register_shares(self, firm_id: int, agent_id: int, quantity: float) -> None:
        """
        Updates the share registry.
        If quantity is <= 0, the entry is removed to keep the registry clean.
        """
        if quantity <= 0:
            if firm_id in self._registry and agent_id in self._registry[firm_id]:
                del self._registry[firm_id][agent_id]
                if not self._registry[firm_id]:
                    del self._registry[firm_id]
        else:
            self._registry[firm_id][agent_id] = quantity

    def get_shareholders_of_firm(self, firm_id: int) -> List[ShareholderData]:
        """
        Returns a list of all current shareholders for a given firm.
        """
        if firm_id not in self._registry:
            return []

        return [
            {"agent_id": agent_id, "firm_id": firm_id, "quantity": qty}
            for agent_id, qty in self._registry[firm_id].items()
        ]

    def get_total_shares(self, firm_id: int) -> float:
        """
        Returns the total number of outstanding shares for a firm.
        """
        if firm_id not in self._registry:
            return 0.0
        return sum(self._registry[firm_id].values())

    def clear(self) -> None:
        """Clears the entire registry."""
        self._registry.clear()
