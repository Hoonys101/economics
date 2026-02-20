from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_MonetaryProcessing(IPhaseStrategy):
    """
    Phase 4.7: Monetary Processing
    Updates the MonetaryLedger based on credit creation/destruction transactions.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # WO-4.2B: Delegate to MonetaryLedger
        # We must process all transactions accumulated in WorldState so far,
        # as sim_state.transactions is cleared after each phase drain.
        if state.primary_government and hasattr(state.primary_government, "monetary_ledger"):
             # Combine drained transactions with any current pending ones (though likely empty here)
             all_transactions = list(self.world_state.transactions) + list(state.transactions)
             state.primary_government.monetary_ledger.process_transactions(all_transactions)

        return state
