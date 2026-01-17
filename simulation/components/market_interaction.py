from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, TYPE_CHECKING
from simulation.systems.api import IMarketComponent, MarketInteractionContext
from simulation.config import SimulationConfig

if TYPE_CHECKING:
    from simulation.core_agents import Household

class MarketComponent(IMarketComponent):
    """판매자 선택과 같은 시장 상호작용을 책임지는 컴포넌트."""

    def __init__(self, owner: Household, config: SimulationConfig):
        self.owner = owner
        self.config = config

    def choose_best_seller(self, item_id: str, context: MarketInteractionContext) -> Tuple[Optional[int], float]:
        """
        가격, 품질, 브랜드 인지도, 충성도를 포함하는 효용에 기반하여
        주어진 아이템에 대한 최적의 판매자를 선택합니다.
        """
        markets = context['markets']
        market = markets.get(item_id)
        if not market:
            return None, 0.0

        # We assume order_book_market has get_all_asks(item_id) returning list of SellOrders
        if not hasattr(market, 'get_all_asks'):
             return None, 0.0

        asks = market.get_all_asks(item_id)
        if not asks:
            return None, 0.0

        best_u = -float('inf')
        best_seller = None
        best_price = 0.0

        # Beta (Brand Sensitivity) from Config
        beta = getattr(self.config, "BRAND_SENSITIVITY_BETA", 0.5)

        for ask in asks:
            price = ask.price
            seller_id = ask.agent_id

            # Read brand metadata from Order
            brand_data = getattr(ask, 'brand_info', {}) or {}
            quality = brand_data.get("perceived_quality", 1.0)
            awareness = brand_data.get("brand_awareness", 0.0)

            # Household preferences
            quality_preference = getattr(self.owner, 'quality_preference', 0.5)
            brand_loyalty_map = getattr(self.owner, 'brand_loyalty', {})
            loyalty = brand_loyalty_map.get(seller_id, 1.0)

            # Utility Function: U = (Quality^pref * (1 + Awareness)^beta * Loyalty) / Price
            numerator = (quality ** quality_preference) * ((1.0 + awareness) ** beta)
            utility = (numerator * loyalty) / max(0.01, price)

            if utility > best_u:
                best_u = utility
                best_seller = seller_id
                best_price = price

        return best_seller, best_price
