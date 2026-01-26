"""
Implements the MarketComponent which handles utility-based seller selection.
"""
from typing import Any, Dict, Optional, Tuple
from simulation.systems.api import IMarketComponent, MarketInteractionContext

class MarketComponent(IMarketComponent):
    """
    Handles market interactions for the Household, specifically choosing the best seller.
    """

    def __init__(self, owner: Any, config: Any):
        self.owner = owner # Household
        self.config = config

    def choose_best_seller(self, item_id: str, context: MarketInteractionContext) -> Tuple[Optional[int], float]:
        """
        Selects the best seller based on Utility = (Quality^alpha * (1+Awareness)^beta * Loyalty) / Price.
        """
        market_snapshot = context["market_snapshot"]
        asks = market_snapshot.asks.get(item_id, [])
        if not asks:
            return None, 0.0

        best_u = -float('inf')
        best_seller = None
        best_price = 0.0

        beta = getattr(self.config, "BRAND_SENSITIVITY_BETA", 0.5)

        for ask in asks:
            price = ask.price
            seller_id = ask.agent_id

            # Metadata
            brand_data = getattr(ask, 'brand_info', {}) or {}
            quality = brand_data.get("perceived_quality", 1.0)
            awareness = brand_data.get("brand_awareness", 0.0)

            loyalty = self.owner.brand_loyalty.get(seller_id, 1.0)
            quality_pref = getattr(self.owner, 'quality_preference', 0.5)

            # Utility Calculation
            numerator = (quality ** quality_pref) * ((1.0 + awareness) ** beta)
            utility = (numerator * loyalty) / max(0.01, price)

            if utility > best_u:
                best_u = utility
                best_seller = seller_id
                best_price = price

        return best_seller, best_price
