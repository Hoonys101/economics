from __future__ import annotations
from typing import Optional, Dict, Any, Tuple, TYPE_CHECKING
import logging

from simulation.systems.api import IMarketComponent, MarketInteractionContext
# Avoid circular import for Household type hint by using TYPE_CHECKING
if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.models import Order

logger = logging.getLogger(__name__)

class MarketComponent(IMarketComponent):
    """
    Manages market interactions for an agent, such as selecting the best seller.
    Extracts logic previously in Household.choose_best_seller.
    """

    def __init__(self, owner: 'Household', config):
        self.owner = owner
        self.config = config

    def choose_best_seller(self, item_id: str, context: MarketInteractionContext) -> Tuple[Optional[int], float]:
        """
        Selects the best seller for an item based on utility (price, quality, brand).
        Returns (BestSellerID, BestAskPrice).
        """
        markets = context["markets"]
        market = markets.get(item_id)
        if not market:
            return None, 0.0

        # We assume order_book_market has get_all_asks(item_id)
        if not hasattr(market, 'get_all_asks'):
            return None, 0.0

        asks = market.get_all_asks(item_id) # Should return List[Order]
        if not asks:
            return None, 0.0

        best_u = -float('inf')
        best_seller = None
        best_price = 0.0

        # Access owner preferences
        # Assuming owner (Household) has quality_preference, brand_loyalty
        quality_preference = getattr(self.owner, 'quality_preference', 0.5)
        brand_loyalty_map = getattr(self.owner, 'brand_loyalty', {})

        for ask in asks:
            price = ask.price
            seller_id = ask.agent_id

            # Phase 6: Read brand metadata from Order
            brand_data = getattr(ask, 'brand_info', {}) or {}
            quality = brand_data.get("perceived_quality", 1.0)
            awareness = brand_data.get("brand_awareness", 0.0)

            loyalty = brand_loyalty_map.get(seller_id, 1.0)

            # Utility Function: U = (Quality^alpha * (1+Awareness)^beta * Loyalty) / Price
            beta = getattr(self.config, "BRAND_SENSITIVITY_BETA", 0.5)

            numerator = (quality ** quality_preference) * ((1.0 + awareness) ** beta)
            utility = (numerator * loyalty) / max(0.01, price)

            if utility > best_u:
                best_u = utility
                best_seller = seller_id
                best_price = price

        return best_seller, best_price
