from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class SalesPostAskContextDTO:
    """
    Context for posting an ask order.
    Groups all necessary information for the SalesEngine to generate an Order.
    """
    firm_id: int
    item_id: str
    price_pennies: int
    quantity: float
    market_id: str
    current_tick: int
    inventory_quantity: float
    brand_snapshot: dict[str, Any] | None = ...

@dataclass(frozen=True)
class SalesMarketingContextDTO:
    """
    Context for generating marketing transactions.
    Groups all necessary information for the SalesEngine to generate marketing spend.
    """
    firm_id: int
    wallet_balance: int
    government_id: int | str | None
    current_time: int

@dataclass(frozen=True)
class MarketingAdjustmentResultDTO:
    """Result from a marketing budget calculation."""
    new_budget: int
    new_marketing_rate: float
