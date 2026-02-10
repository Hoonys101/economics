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
    price: float
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
    wallet_balance: float
    government_id: Optional[Union[int, str]]
    current_time: int
