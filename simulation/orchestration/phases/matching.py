from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState
from simulation.markets.order_book_market import OrderBookMarket

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase2_Matching(IPhaseStrategy):
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        matched_txs = []
        for market in state.markets.values():
            if isinstance(market, OrderBookMarket):
                matched_txs.extend(market.match_orders(state.time))

        if state.stock_market:
            stock_txs = state.stock_market.match_orders(state.time)
            matched_txs.extend(stock_txs)
            state.stock_market.clear_expired_orders(state.time)

        if "housing" in state.markets:
             housing_txs = state.markets["housing"].match_orders(state.time)
             matched_txs.extend(housing_txs)

        state.transactions.extend(matched_txs)
        return state
