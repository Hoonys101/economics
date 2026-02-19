from typing import Protocol, Dict, List, runtime_checkable, Optional
from simulation.models import Order, Transaction

@runtime_checkable
class IMarket(Protocol):
    """
    Interface for Market objects, exposing only read-only attributes
    safe for agent consumption (Snapshot Pattern).
    """
    id: str
    buy_orders: Dict[str, List[Order]]
    sell_orders: Dict[str, List[Order]]
    matched_transactions: List[Transaction]

    def get_daily_avg_price(self) -> float: ...
    def get_daily_volume(self) -> float: ...

    # Modernized Accessors
    def get_price(self, item_id: str) -> float:
        """Returns the current market price for the given item."""
        ...

    def cancel_orders(self, agent_id: str) -> None:
        """Cancels all orders for the specified agent."""
        ...
