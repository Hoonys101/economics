from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_Bankruptcy(IPhaseStrategy):
    """
    Phase 4: Agent Decisions & Lifecycle (Bankruptcy Check)
    Agents make decisions. Bankrupt agents are identified here.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        if self.world_state.lifecycle_manager:
            lifecycle_txs = self.world_state.lifecycle_manager.execute(state)
            if lifecycle_txs:
                state.inter_tick_queue.extend(lifecycle_txs)
        return state
