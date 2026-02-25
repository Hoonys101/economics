"""
Demographics Module API
Defines the interface for Population Management and Statistical Aggregation.
"""
from typing import Protocol, Dict, List, Any, TypedDict, runtime_checkable, Optional
from enum import Enum

# --- Data Transfer Objects ---

class GenderStatsDTO(TypedDict):
    """
    Data Transfer Object for gender-specific statistics.
    Aggregates count and economic participation.
    """
    count: int
    total_labor_hours: float
    avg_labor_hours: float

class DemographicStatsDTO(TypedDict):
    """
    Aggregate DTO for all demographic statistics.
    """
    M: GenderStatsDTO
    F: GenderStatsDTO
    total_population: int
    active_population: int

# --- Protocols ---

@runtime_checkable
class IDemographicManager(Protocol):
    """
    Interface for the Demographic Manager.
    Acts as the Single Source of Truth for population lifecycle and statistics.
    """

    def register_birth(self, agent: Any) -> None:
        """
        Registers a new agent in the demographic system.
        Updates population caches and triggers birth events.
        """
        ...

    def register_death(self, agent: Any, cause: str = "NATURAL") -> None:
        """
        Processes the death of an agent.
        Updates population caches, marks agent as inactive.
        """
        ...

    def update_labor_hours(self, gender: str, delta: float) -> None:
        """
        Updates the running total of labor hours for a specific gender.
        Called by agents when their time allocation changes.
        """
        ...

    def get_gender_stats(self) -> DemographicStatsDTO:
        """
        Retrieves the current demographic statistics.
        MUST be O(1) - returning cached values.
        """
        ...

    def sync_stats(self, agents: List[Any]) -> None:
        """
        Force-rebuilds the internal cache from a list of agents.
        """
        ...

    def process_aging(self, agents: List[Any], current_tick: int, market_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Processes aging for a list of agents.
        """
        ...
