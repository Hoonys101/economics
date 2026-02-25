from _typeshed import Incomplete
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.ai.api import Personality as Personality
from simulation.ai.household_ai import HouseholdAI as HouseholdAI
from simulation.core_agents import Household as Household
from typing import Any

logger: Incomplete

class AITrainingManager:
    agents: Incomplete
    config_module: Incomplete
    def __init__(self, agents: list[Household], config_module: Any) -> None: ...
    def run_imitation_learning_cycle(self, current_tick: int):
        """The main entry point for the imitation learning cycle."""
    def clone_from_fittest_agent(self, target_agent: Household) -> None:
        """Clones Q-tables from the absolute best agent to the target agent."""
    def inherit_brain(self, parent_agent: Household, child_agent: Household) -> None:
        """
        Transfers knowledge (Q-Tables) and personality from parent to child.
        """
    def end_episode(self, agents: list[Any]) -> None:
        """Called at the end of a simulation episode."""
