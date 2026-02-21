from dataclasses import dataclass
from typing import Optional, Dict, Any, Union

@dataclass(frozen=True)
class SalesPostAskContextDTO:
    """
    Context for posting an ask order.
    Groups all necessary information for the SalesEngine to generate an Order.
    """
    firm_id: int
    item_id: str
    price_pennies: int # Changed to int (pennies)
    quantity: float
    market_id: str
    current_tick: int
    inventory_quantity: float
    brand_snapshot: Optional[Dict[str, Any]] = None

@dataclass(frozen=True)
class SalesMarketingContextDTO:
    """
    Context for generating marketing transactions.
    Groups all necessary information for the SalesEngine to generate marketing spend.
    """
    firm_id: int
    wallet_balance: int # Changed to int (pennies)
    government_id: Optional[Union[int, str]]
    current_time: int

@dataclass(frozen=True)
class MarketingAdjustmentResultDTO:
    """Result from a marketing budget calculation."""
    new_budget: int # Changed to int (pennies)
    new_marketing_rate: float
