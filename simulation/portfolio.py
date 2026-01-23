from typing import Dict, Optional, List
from simulation.models import Share
import copy


class Portfolio:
    """
    Manages a collection of Shares with Average Cost Basis logic.
    Supports atomic merge and synchronization with legacy dictionaries.
    """

    def __init__(self, owner_id: int):
        self.owner_id = owner_id
        self.holdings: Dict[int, Share] = {}  # firm_id -> Share

    def add(self, firm_id: int, quantity: float, price: float):
        """
        Adds shares to the portfolio, updating Weighted Average Cost (WAC).
        """
        if quantity <= 0:
            return

        if firm_id in self.holdings:
            share = self.holdings[firm_id]
            total_cost = (share.quantity * share.acquisition_price) + (quantity * price)
            total_qty = share.quantity + quantity

            share.quantity = total_qty
            share.acquisition_price = total_cost / total_qty
        else:
            self.holdings[firm_id] = Share(
                firm_id=firm_id,
                holder_id=self.owner_id,
                quantity=quantity,
                acquisition_price=price,
            )

    def remove(self, firm_id: int, quantity: float):
        """
        Removes shares. WAC does not change on sell.
        """
        if firm_id not in self.holdings:
            return

        share = self.holdings[firm_id]
        if share.quantity <= quantity:
            # Full liquidation
            del self.holdings[firm_id]
        else:
            share.quantity -= quantity

    def merge(self, other_portfolio: "Portfolio", fraction: float = 1.0):
        """
        Merges a fraction of another portfolio into this one.
        Recalculates WAC for incoming shares.
        """
        for firm_id, share in other_portfolio.holdings.items():
            qty_to_transfer = share.quantity * fraction
            if qty_to_transfer > 0:
                self.add(firm_id, qty_to_transfer, share.acquisition_price)

    def get_valuation(self, current_prices: Dict[int, float]) -> float:
        """
        Calculates total market value based on current prices.
        """
        total_value = 0.0
        for firm_id, share in self.holdings.items():
            price = current_prices.get(firm_id, 0.0)
            total_value += share.quantity * price
        return total_value

    def to_legacy_dict(self) -> Dict[int, float]:
        """
        Returns {firm_id: quantity} for legacy compatibility.
        """
        return {fid: share.quantity for fid, share in self.holdings.items()}

    def sync_from_legacy(
        self, legacy_dict: Dict[int, float], default_price: float = 1.0
    ):
        """
        One-time sync from legacy dict (lossy: assumes default price if missing).
        """
        self.holdings.clear()
        for firm_id, qty in legacy_dict.items():
            self.add(firm_id, qty, default_price)
