from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_HousingSaga(IPhaseStrategy):
    """
    Phase 4.1: Advance Housing Sagas (Pre-Settlement Checks)

    This phase processes long-running transactions (sagas), specifically for housing.
    Its primary responsibility at this point in the tick is to perform pre-condition checks
    that do not depend on market matching or financial settlement, such as agent liveness.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        """
        Checks for agent liveness and cancels sagas if participants are no longer active.
        """
        # TD-253: Logic moved to SagaOrchestrator
        if state.saga_orchestrator:
            state.saga_orchestrator.process_sagas(state)
        elif state.settlement_system and hasattr(state.settlement_system, 'process_sagas'):
            # Fallback for compatibility during refactor
            state.settlement_system.process_sagas(state)

        return state
