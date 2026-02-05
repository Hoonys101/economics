from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase3_Transaction(IPhaseStrategy):
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # Move system transactions from queue if any (e.g. from Bankruptcy phase)
        if state.inter_tick_queue:
            state.transactions.extend(state.inter_tick_queue)
            state.inter_tick_queue.clear()

        # WO-024: Monetary Transactions are now processed incrementally in TickOrchestrator._drain_and_sync_state (TD-177)
        # Main transaction processing logic
        if self.world_state.transaction_processor:
            # TD-192: Pass combined transactions to ensure execution of drained (historic) and current items
            combined_txs = list(self.world_state.transactions) + list(state.transactions)
            results = self.world_state.transaction_processor.execute(state, transactions=combined_txs)

            # WO-116: Record Revenue (Saga Pattern)
            if state.taxation_system:
                state.taxation_system.record_revenue(results)
        else:
            state.logger.error("TransactionProcessor not initialized.")

        return state
