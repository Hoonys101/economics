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

    def add(self, firm_id: int, quantity: float, acquisition_price_pennies: int):
        """
        Adds shares to the portfolio, updating Weighted Average Cost (WAC).
        acquisition_price_pennies: Cost per share in pennies.
        """
        if quantity <= 0:
            return

        if firm_id in self.holdings:
            share = self.holdings[firm_id]
            # Calculate total cost in pennies (may be float due to fractional shares)
            total_cost_pennies = (share.quantity * share.acquisition_price) + (quantity * acquisition_price_pennies)
            total_qty = share.quantity + quantity

            share.quantity = total_qty
            # Update WAC (pennies per share), cast to int
            if total_qty > 0:
                share.acquisition_price = int(total_cost_pennies / total_qty)
        else:
            self.holdings[firm_id] = Share(
                firm_id=firm_id,
                holder_id=self.owner_id,
                quantity=quantity,
                acquisition_price=acquisition_price_pennies
            )

    def get_stock_quantity(self, firm_id: int) -> float:
        """
        Returns the quantity of shares held for a given firm.
        Replacing direct access to holdings for LoD compliance (TD-233).
        """
        share = self.holdings.get(firm_id)
        return share.quantity if share else 0.0

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

    def merge(self, other_portfolio: 'Portfolio', fraction: float = 1.0):
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

    def sync_from_legacy(self, legacy_dict: Dict[int, float], default_price_pennies: int = 100):
        """
        One-time sync from legacy dict (lossy: assumes default price if missing).
        """
        self.holdings.clear()
        for firm_id, qty in legacy_dict.items():
            self.add(firm_id, qty, default_price_pennies)
