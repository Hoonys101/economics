from _typeshed import Incomplete
from modules.household.api import HouseholdFactoryContext as HouseholdFactoryContext, IHouseholdFactory
from simulation.ai.api import Personality as Personality
from simulation.core_agents import Household as Household
from simulation.models import Talent as Talent
from typing import Any

logger: Incomplete

class HouseholdFactory(IHouseholdFactory):
    """
    Factory for creating Household agents.
    Encapsulates creation logic, configuration setup, and initial state hydration.
    """
    context: Incomplete
    def __init__(self, context: HouseholdFactoryContext) -> None: ...
    def create_household(self, agent_id: int, initial_age: float, gender: str, initial_assets: int = 0, generation: int = 0, parent_id: int | None = None, spouse_id: int | None = None, personality: Personality | None = None, talent: Talent | None = None, decision_engine: Any | None = None, initial_needs: dict[str, float] | None = None, major: str | None = None) -> Household:
        """
        Standard initialization for a Household agent.
        """
    def create_newborn(self, parent: Household, new_id: int, initial_assets: int = 0, current_tick: int = 0, simulation: Any = None) -> Household:
        """
        Creates a newborn household (child) from a parent.
        Handles inheritance of traits (personality, talent, brain).
        Enforces Zero-Sum integrity for initial assets (gift).
        """
    def clone_household(self, source_hh: Household, new_id: int, initial_assets: int, current_tick: int) -> Household:
        """
        Deep copy / Mitosis logic.
        Delegates to create_newborn for now as per domain logic (mitosis).
        If exact clone is needed, different logic would be applied.
        """
    def create_immigrant(self, new_id: int, current_tick: int, initial_assets: int) -> Household:
        """Creates a new household representing an immigrant."""
    def create_initial_population(self, num_agents: int) -> list[Household]:
        """Creates the initial population of households for the simulation."""
