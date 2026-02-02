from __future__ import annotations
from typing import List, Any, Callable, TYPE_CHECKING
import logging

from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.firms import Firm

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class ActionProcessor:
    """
    Processes actions and transactions in the simulation.
    Decomposed from Simulation engine.
    WO-103: Adapts legacy calls to SystemInterface.
    """

    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def process_transactions(
        self,
        transactions: List[Transaction],
        market_data_callback: Callable[[], Any]
    ) -> None:
        """
        Delegates transaction processing to the TransactionProcessor system using SimulationState.
        """
        if self.world_state.transaction_processor:
            # Construct partial market_data from callback
            try:
                goods_market_data = market_data_callback()
            except Exception:
                goods_market_data = {}

            market_data = {"goods_market": goods_market_data}

            from simulation.dtos.api import SimulationState
            state = SimulationState(
                time=self.world_state.time,
                households=self.world_state.households,
                firms=self.world_state.firms,
                agents=self.world_state.agents,
                markets=self.world_state.markets,
                government=self.world_state.government,
                bank=self.world_state.bank,
                central_bank=self.world_state.central_bank,
                stock_market=self.world_state.stock_market,
                stock_tracker=self.world_state.stock_tracker,
                goods_data=self.world_state.goods_data,
                market_data=market_data,
                config_module=self.world_state.config_module,
                tracker=self.world_state.tracker,
                logger=self.world_state.logger,
                ai_training_manager=getattr(self.world_state, "ai_training_manager", None),
                ai_trainer=getattr(self.world_state, "ai_trainer", None),
                settlement_system=getattr(self.world_state, "settlement_system", None),
                next_agent_id=self.world_state.next_agent_id,
                real_estate_units=self.world_state.real_estate_units,
                transactions=transactions,
                effects_queue=self.world_state.effects_queue,
                inter_tick_queue=self.world_state.inter_tick_queue,
                inactive_agents=self.world_state.inactive_agents
            )
            self.world_state.transaction_processor.execute(state)
            
            # TD-192: Synchronize scalar values AND transient queues back to WorldState
            # Critical: TransactionProcessor might populate these queues.
            self.world_state.next_agent_id = state.next_agent_id
            
            # Note: Lists are mutable, so in-place appends work by reference.
            # However, if TP re-assigned the list, we would lose data.
            # Explicit sync protects against re-assignment bugs.
            if state.effects_queue is not self.world_state.effects_queue:
                 self.world_state.effects_queue.extend(state.effects_queue)
            
            if state.inter_tick_queue is not self.world_state.inter_tick_queue:
                 self.world_state.inter_tick_queue.extend(state.inter_tick_queue)

            # Inactive agents map might be updated
            self.world_state.inactive_agents.update(state.inactive_agents)
        else:
            logger.error("TransactionProcessor is not initialized in WorldState.")

    def process_stock_transactions(self, transactions: List[Transaction]) -> None:
        """Process stock transactions."""
        # Now handled by TransactionProcessor
        self.process_transactions(transactions, lambda: {})
