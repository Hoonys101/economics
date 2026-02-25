from _typeshed import Incomplete
from simulation.core_agents import Household as Household
from simulation.dtos import AgentStateData as AgentStateData, EconomicIndicatorData as EconomicIndicatorData, MarketHistoryData as MarketHistoryData, TransactionData as TransactionData
from simulation.firms import Firm as Firm
from simulation.models import Transaction as Transaction
from simulation.world_state import WorldState as WorldState

logger: Incomplete

class AnalyticsSystem:
    """
    Service responsible for gathering and aggregating simulation data for persistence.
    TD-272: Decouples aggregation logic from PersistenceManager.
    """
    def __init__(self) -> None: ...
    def aggregate_tick_data(self, world_state: WorldState) -> tuple[list[AgentStateData], list[TransactionData], EconomicIndicatorData, list[MarketHistoryData]]:
        """
        Aggregates data from the world state into DTOs for persistence.
        """
