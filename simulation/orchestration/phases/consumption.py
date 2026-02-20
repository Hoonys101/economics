from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState
from simulation.systems.api import CommerceContext

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_Consumption(IPhaseStrategy):
    """
    Phase: Consumption Finalization.
    Formerly part of Phase4_Lifecycle.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        consumption_market_data = state.market_data

        commerce_context: CommerceContext = {
            "households": state.households,
            "agents": state.agents,
            "breeding_planner": self.world_state.breeding_planner,
            "household_time_allocation": state.household_time_allocation,
            "market_data": consumption_market_data,
            "config": state.config_module,
            "time": state.time,
            "government": state.primary_government
        }

        if self.world_state.commerce_system:
            leisure_effects = self.world_state.commerce_system.finalize_consumption_and_leisure(
                commerce_context, state.planned_consumption
            )
            state.household_leisure_effects = leisure_effects

        return state
