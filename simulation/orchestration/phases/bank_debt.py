from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase_BankAndDebt(IPhaseStrategy):
    """
    Phase 4.2: Bank & Debt Service
    Handles bank interest/fees and agent debt servicing.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # 1. Bank Tick
        if state.bank and hasattr(state.bank, "run_tick"):
            bank_txs = state.bank.run_tick(state.agents, state.time)
            if bank_txs:
                state.transactions.extend(bank_txs)

        # 2. Debt Service
        if self.world_state.finance_system:
             debt_txs = self.world_state.finance_system.service_debt(state.time)
             if debt_txs:
                 state.transactions.extend(debt_txs)

        return state
