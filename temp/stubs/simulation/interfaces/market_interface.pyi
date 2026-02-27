from simulation.models import Order as Order, Transaction as Transaction
from typing import Protocol

class IMarket(Protocol):
    """
    Interface for Market objects, exposing only read-only attributes
    safe for agent consumption (Snapshot Pattern).
    """
    id: str
    @property
    def buy_orders(self) -> dict[str, list[Order]]: ...
    @property
    def sell_orders(self) -> dict[str, list[Order]]: ...
    @property
    def matched_transactions(self) -> list[Transaction]: ...
    def get_daily_avg_price(self) -> float: ...
    def get_daily_volume(self) -> float: ...
    def get_price(self, item_id: str) -> float:
        """Returns the current market price for the given item."""
    def cancel_orders(self, agent_id: str) -> None:
        """Cancels all orders for the specified agent."""
