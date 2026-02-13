from __future__ import annotations
from typing import TYPE_CHECKING, Dict
import logging
import math

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState
from modules.system.api import MarketSignalDTO
from simulation.markets.order_book_market import OrderBookMarket

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_SystemicLiquidation(IPhaseStrategy):
    """
    Phase 4.5: Systemic Liquidation.
    The Public Manager generates orders to liquidate recovered assets.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        if not self.world_state.public_manager:
            return state

        # 1. Generate Market Signals
        # (Copied/Adapted from Phase1_Decision to ensure PublicManager has fresh data)
        market_signals: Dict[str, MarketSignalDTO] = {}

        for m_id, market in state.markets.items():
            if isinstance(market, OrderBookMarket):
                all_items = set(market.buy_orders.keys()) | set(market.sell_orders.keys()) | set(market.last_traded_prices.keys())

                # Add items from PublicManager inventory to ensure we check them
                if self.world_state.public_manager and hasattr(self.world_state.public_manager, "managed_inventory"):
                     all_items.update(self.world_state.public_manager.managed_inventory.keys())

                for item_id in all_items:
                     price_history = list(market.price_history.get(item_id, []))
                     history_7d = price_history[-7:]

                     volatility = 0.0
                     if len(history_7d) > 1:
                         mean = sum(history_7d) / len(history_7d)
                         variance = sum((p - mean) ** 2 for p in history_7d) / len(history_7d)
                         volatility = math.sqrt(variance)

                     # min_p, max_p = market.get_dynamic_price_bounds(item_id)
                     is_frozen = False

                     # Calculate total quantities and depth efficiently
                     bids = market.get_all_bids(item_id)
                     asks = market.get_all_asks(item_id)
                     total_bid_qty = sum(o.quantity for o in bids)
                     total_ask_qty = sum(o.quantity for o in asks)

                     signal = MarketSignalDTO(
                         market_id=m_id,
                         item_id=item_id,
                         best_bid=market.get_best_bid(item_id),
                         best_ask=market.get_best_ask(item_id),
                         last_traded_price=market.get_last_traded_price(item_id),
                         last_trade_tick=market.get_last_trade_tick(item_id) or -1,
                         price_history_7d=history_7d,
                         volatility_7d=volatility,
                         order_book_depth_buy=len(bids),
                         order_book_depth_sell=len(asks),
                         total_bid_quantity=total_bid_qty,
                         total_ask_quantity=total_ask_qty,
                         is_frozen=is_frozen
                     )
                     market_signals[item_id] = signal

        # 2. Public Manager generates orders
        liquidation_orders = self.world_state.public_manager.generate_liquidation_orders(market_signals)

        # 3. Place orders
        for order in liquidation_orders:
            # Order must have market_id. If not, fallback.
            market_id = order.market_id
            if not market_id:
                market_id = order.item_id # Legacy convention

            target_market = state.markets.get(market_id)

            if target_market:
                target_market.place_order(order, state.time)
            else:
                logger.warning(f"PublicManager tried to place order for {order.item_id} but no market found.")

        return state
