from _typeshed import Incomplete
from modules.demographics.api import DemographicStatsDTO as DemographicStatsDTO, GenderStatsDTO as GenderStatsDTO, IDemographicManager
from modules.household.api import IHouseholdFactory as IHouseholdFactory
from simulation.core_agents import Household as Household
from simulation.dtos.strategy import ScenarioStrategy as ScenarioStrategy
from simulation.factories.household_factory import HouseholdFactory as HouseholdFactory
from simulation.utils.config_factory import create_config_dto as create_config_dto
from simulation.world_state import WorldState as WorldState
from typing import Any

logger: Incomplete

class DemographicManager(IDemographicManager):
    """
    Optimized Demographic Manager (Phase 17)
    - O(1) Statistical Retrieval via event-driven caching.
    - Single Source of Truth for agent lifecycle (birth/death).
    """
    def __new__(cls, *args, **kwargs): ...
    config_module: Incomplete
    strategy: Incomplete
    logger: Incomplete
    settlement_system: Any | None
    household_factory: Incomplete
    initialized: bool
    def __init__(self, config_module: Any = None, strategy: ScenarioStrategy | None = None, household_factory: IHouseholdFactory | None = None) -> None: ...
    world_state: Incomplete
    def set_world_state(self, world_state: WorldState) -> None: ...
    def get_gender_stats(self) -> DemographicStatsDTO:
        """
        Retrieves demographic statistics in O(1).
        """
    def register_birth(self, agent: Any) -> None:
        """Registers birth and updates cache."""
    def register_death(self, agent: Any, cause: str = 'NATURAL') -> None:
        """Single Source of Truth for lifecycle termination."""
    def update_labor_hours(self, gender: str, delta: float) -> None:
        """Updates labor hour running totals (called by agents on time allocation change)."""
    def sync_stats(self, agents: list[Any]) -> None:
        """Rebuilds cache from active agent list (O(N) recovery)."""
    def process_aging(self, agents: list[Household], current_tick: int, market_data: dict[str, Any] | None = None) -> None: ...
    def process_births(self, simulation: Any, birth_requests: list[Household]) -> list[Household]: ...
