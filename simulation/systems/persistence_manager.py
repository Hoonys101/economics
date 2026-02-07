from __future__ import annotations
import logging
from typing import TYPE_CHECKING, List, Dict, Any, Optional
from simulation.dtos import (
    AgentStateData,
    TransactionData,
    EconomicIndicatorData,
    MarketHistoryData,
)
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.models import Transaction

logger = logging.getLogger(__name__)

class PersistenceManager:
    """
    Phase 22.5: Persistence Manager System
    Handles DB state buffering, calculation of aggregate indicators for persistence, 
    and batch flushing to simulation repository.
    TD-272: Refactored to be a pure sink (no logic).
    """

    def __init__(self, run_id: int, config_module: Any, repository: Any):
        self.run_id = run_id
        self.config = config_module
        self.repository = repository
        
        # Internal Buffers
        self.agent_state_buffer: List[AgentStateData] = []
        self.transaction_buffer: List[TransactionData] = []
        self.economic_indicator_buffer: List[EconomicIndicatorData] = []
        self.market_history_buffer: List[MarketHistoryData] = []

    def buffer_data(
        self,
        agent_states: List[AgentStateData],
        transactions: List[TransactionData],
        indicators: Optional[EconomicIndicatorData],
        market_history: List[MarketHistoryData] = None
    ) -> None:
        """
        TD-272: Pure data buffering.
        Receives pre-assembled DTOs and appends them to internal buffers.
        """
        if agent_states:
            self.agent_state_buffer.extend(agent_states)
        
        if transactions:
            self.transaction_buffer.extend(transactions)
        
        if indicators:
            self.economic_indicator_buffer.append(indicators)

        if market_history:
            self.market_history_buffer.extend(market_history)

    def flush_buffers(self, current_tick: int):
        """
        Periodically flushes buffered states to the database repository.
        """
        if not (self.agent_state_buffer or self.transaction_buffer or 
                self.economic_indicator_buffer or self.market_history_buffer):
            return

        logger.info(
            f"DB_FLUSH_START | Flushing buffers to DB at tick {current_tick}",
            extra={"tick": current_tick, "tags": ["db_flush"]}
        )

        if self.agent_state_buffer:
            self.repository.agents.save_agent_states_batch(self.agent_state_buffer)
            self.agent_state_buffer.clear()

        if self.transaction_buffer:
            self.repository.markets.save_transactions_batch(self.transaction_buffer)
            self.transaction_buffer.clear()

        if self.economic_indicator_buffer:
            self.repository.analytics.save_economic_indicators_batch(self.economic_indicator_buffer)
            self.economic_indicator_buffer.clear()

        if self.market_history_buffer:
            self.repository.markets.save_market_history_batch(self.market_history_buffer)
            self.market_history_buffer.clear()

        logger.info(
            f"DB_FLUSH_END | Finished flushing buffers to DB at tick {current_tick}",
            extra={"tick": current_tick, "tags": ["db_flush"]}
        )
