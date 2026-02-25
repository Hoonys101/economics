from _typeshed import Incomplete
from simulation.models import Share as Share

class Portfolio:
    """
    Manages a collection of Shares with Average Cost Basis logic.
    Supports atomic merge and synchronization with legacy dictionaries.
    """
    owner_id: Incomplete
    holdings: dict[int, Share]
    def __init__(self, owner_id: int) -> None: ...
    def add(self, firm_id: int, quantity: float, acquisition_price_pennies: int):
        """
        Adds shares to the portfolio, updating Weighted Average Cost (WAC).
        Price must be in pennies (int).
        """
    def get_stock_quantity(self, firm_id: int) -> float:
        """
        Returns the quantity of shares held for a given firm.
        Replacing direct access to holdings for LoD compliance (TD-233).
        """
    def remove(self, firm_id: int, quantity: float):
        """
        Removes shares. WAC does not change on sell.
        """
    def merge(self, other_portfolio: Portfolio, fraction: float = 1.0):
        """
        Merges a fraction of another portfolio into this one.
        Recalculates WAC for incoming shares.
        """
    def get_valuation(self, current_prices: dict[int, float]) -> float:
        """
        Calculates total market value based on current prices.
        """
    def to_legacy_dict(self) -> dict[int, float]:
        """
        Returns {firm_id: quantity} for legacy compatibility.
        """
    def sync_from_legacy(self, legacy_dict: dict[int, float], default_price_pennies: int = 100):
        """
        One-time sync from legacy dict (lossy: assumes default price if missing).
        """
