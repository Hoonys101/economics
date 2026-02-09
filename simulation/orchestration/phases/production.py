from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_Production(IPhaseStrategy):
    """
    Phase 0.5: Technology update and firm production.
    Ensures firms have updated inventory before the Decision phase.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        from simulation.systems.tech.api import FirmTechInfoDTO, HouseholdEducationDTO

        # 1. Calculate Human Capital Index
        active_households_dto = [
            HouseholdEducationDTO(is_active=h._bio_state.is_active, education_level=getattr(h, 'education_level', 0) or 0)
            for h in state.households if h._bio_state.is_active
        ]

        total_edu = sum(h['education_level'] for h in active_households_dto)
        active_count = len(active_households_dto)
        human_capital_index = total_edu / active_count if active_count > 0 else 1.0

        # 2. Update Technology System
        if self.world_state.technology_manager:
            active_firms_dto = [
                f.get_tech_info() for f in state.firms if f.is_active
            ]
            self.world_state.technology_manager.update(state.time, active_firms_dto, human_capital_index)

        # 3. Trigger Firm Production
        for firm in state.firms:
            if firm.is_active:
                firm.produce(state.time, technology_manager=self.world_state.technology_manager)

        return state
