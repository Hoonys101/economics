from _typeshed import Incomplete
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.dtos import AgentStateData as AgentStateData, EconomicIndicatorData as EconomicIndicatorData, MarketHistoryData as MarketHistoryData, TransactionData as TransactionData
from simulation.models import Transaction as Transaction
from typing import Any

logger: Incomplete

class PersistenceManager:
    """
    Phase 22.5: Persistence Manager System
    Handles DB state buffering, calculation of aggregate indicators for persistence, 
    and batch flushing to simulation repository.
    TD-272: Refactored to be a pure sink (no logic).
    """
    run_id: Incomplete
    config: Incomplete
    repository: Incomplete
    agent_state_buffer: list[AgentStateData]
    transaction_buffer: list[TransactionData]
    economic_indicator_buffer: list[EconomicIndicatorData]
    market_history_buffer: list[MarketHistoryData]
    def __init__(self, run_id: int, config_module: Any, repository: Any) -> None: ...
    def buffer_data(self, agent_states: list[AgentStateData], transactions: list[TransactionData], indicators: EconomicIndicatorData | None, market_history: list[MarketHistoryData] = None) -> None:
        """
        TD-272: Pure data buffering.
        Receives pre-assembled DTOs and appends them to internal buffers.
        """
    def flush_buffers(self, current_tick: int):
        """
        Periodically flushes buffered states to the database repository.
        """
