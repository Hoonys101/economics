from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_GovernmentPrograms(IPhaseStrategy):
    """
    Phase 4.4: Government Spending Programs
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        market_data_prev = state.market_data

        if state.government:
            # Welfare
            welfare_txs = state.government.run_welfare_check(list(state.agents.values()), market_data_prev, state.time)
            if welfare_txs:
                state.transactions.extend(welfare_txs)

            # Infrastructure
            infra_txs = state.government.invest_infrastructure(state.time, state.households)
            if infra_txs:
                state.transactions.extend(infra_txs)

            # Education
            edu_txs = state.government.run_public_education(state.households, state.config_module, state.time)
            if edu_txs:
                state.transactions.extend(edu_txs)

        return state
