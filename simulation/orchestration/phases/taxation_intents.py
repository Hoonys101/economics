from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_TaxationIntents(IPhaseStrategy):
    """
    Phase 4.6: Corporate Tax Intents
    Generates tax obligations before final transaction processing.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # WO-116: Corporate Tax Intent Generation
        if state.taxation_system and state.government:
            tax_intents = state.taxation_system.generate_corporate_tax_intents(state.firms, current_tick=state.time)
            for tx in tax_intents:
                if tx.seller_id == "GOVERNMENT":
                     tx.seller_id = state.government.id
            if tax_intents:
                state.transactions.extend(tax_intents)
        return state
