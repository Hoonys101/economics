from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import uuid

@dataclass(frozen=True)
class OrderDTO:
    """Standardized Market Order Data Transfer Object.
    Replaces legacy dictionary/tuple usage in decision engines.
    Immutable to prevent side-effects during processing.
    """
    agent_id: int | str
    side: str  # "BUY" or "SELL" (formerly order_type)
    item_id: str
    quantity: float
    price_limit: float # (formerly price) - Max for BUY, Min for SELL
    market_id: str

    # Phase 6/7 Extensions
    target_agent_id: Optional[int] = None  # Brand Loyalty / Supply Chain
    brand_info: Optional[Dict[str, Any]] = None # Quality, Awareness
    metadata: Optional[Dict[str, Any]] = None # Side-effects (e.g. Loans)

    # Auto-generated ID
    id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)

    @property
    def price(self) -> float:
        """Alias for legacy compatibility during migration."""
        return self.price_limit

    @property
    def order_type(self) -> str:
        """Alias for legacy compatibility during migration."""
        return self.side
