from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_Politics(IPhaseStrategy):
    """
    Phase 4.3: Political Orchestrator
    Handles elections, public opinion updates, and government policy decisions.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # Access PoliticsSystem via world_state or state if available

        politics_system = self.world_state.politics_system
        # Fallback to DTO if not on WorldState (for testing flexibility)
        if not politics_system and hasattr(state, 'politics_system') and state.politics_system:
             politics_system = state.politics_system

        if politics_system:
            politics_system.process_tick(state)
        else:
            logger.warning("Phase_Politics executed but no PoliticsSystem found.")

        return state
