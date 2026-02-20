from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_FirmProductionAndSalaries(IPhaseStrategy):
    """
    Phase 4.3: Firm Operations (Transactions)
    Handles core firm operations like paying salaries.
    Note: Production logic is in Phase_Production, this is for financial transactions.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        market_data_prev = state.market_data

        # TD-213: Fetch market context for multi-currency transactions
        market_context = None
        if state.tracker and hasattr(state.tracker, "capture_market_context"):
            market_context = state.tracker.capture_market_context()

        # Fallback if no tracker
        if not market_context:
             from modules.system.api import DEFAULT_CURRENCY
             market_context = {
                 "exchange_rates": {DEFAULT_CURRENCY: 1.0},
                 "benchmark_rates": {}
             }

        for firm in state.firms:
             if firm.is_active:
                 firm_txs = firm.generate_transactions(
                     government=state.primary_government,
                     market_data=market_data_prev,
                     shareholder_registry=state.shareholder_registry,
                     current_time=state.time,
                     market_context=market_context
                 )
                 if firm_txs:
                     state.transactions.extend(firm_txs)
        return state
