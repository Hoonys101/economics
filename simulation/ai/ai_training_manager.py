from __future__ import annotations
import logging
import random
from typing import List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)


class AITrainingManager:
    def __init__(self, agents: List[Household], config_module: Any):
        self.agents = agents
        self.config_module = config_module
        logger.info("AITrainingManager initialized.")

    def run_imitation_learning_cycle(self, current_tick: int):
        """The main entry point for the imitation learning cycle."""
        logger.info(f"Running imitation learning cycle at tick {current_tick}.")
        
        top_performers = self._get_top_performing_agents()
        if not top_performers:
            logger.info("No top performers found for imitation learning.")
            return

        under_performers = self._get_under_performing_agents()
        if not under_performers:
             logger.info("No under performers found for imitation learning.")
             return

        logger.info(f"Imitation Cycle: {len(top_performers)} Role Models, {len(under_performers)} Learners.")

        for learner in under_performers:
            role_model = random.choice(top_performers)
            self._clone_and_mutate_q_table(role_model, learner)

    def clone_from_fittest_agent(self, target_agent: Household) -> None:
        """Clones Q-tables from the absolute best agent to the target agent."""
        if not self.agents:
            return

        # Find the agent with the highest assets
        fittest_agent = max(self.agents, key=lambda x: x.assets)
        
        if fittest_agent.id == target_agent.id:
            return # Don't clone from self

        logger.info(f"Cloning from fittest agent {fittest_agent.id} to new agent {target_agent.id}")
        self._clone_and_mutate_q_table(fittest_agent, target_agent)

    def _get_top_performing_agents(self, percentile: float = 0.1) -> List[Household]:
        """Identifies the top-performing agents based on their assets."""
        if not self.agents:
            return []

        sorted_agents = sorted(self.agents, key=lambda x: x.assets, reverse=True)
        top_n = max(1, int(len(self.agents) * percentile))
        return sorted_agents[:top_n]

    def _get_under_performing_agents(self, percentile: float = 0.5) -> List[Household]:
        """Identifies the under-performing agents based on their assets."""
        if not self.agents:
            return []

        sorted_agents = sorted(self.agents, key=lambda x: x.assets) # Ascending
        bottom_n = max(1, int(len(self.agents) * percentile))
        return sorted_agents[:bottom_n]

    def _clone_and_mutate_q_table(
        self, source_agent: Household, target_agent: Household
    ):
        """Clones the Q-table from a source agent to a target agent with some mutation."""
        if not hasattr(source_agent, "decision_engine") or not hasattr(
            target_agent, "decision_engine"
        ):
            return

        # Clone Strategy Q-Table
        source_strategy_manager = (
            source_agent.decision_engine.ai_engine.q_table_manager_strategy
        )
        target_strategy_manager = (
            target_agent.decision_engine.ai_engine.q_table_manager_strategy
        )
        self._copy_and_mutate_single_table(source_strategy_manager, target_strategy_manager)

        # Clone Tactic Q-Table
        source_tactic_manager = (
            source_agent.decision_engine.ai_engine.q_table_manager_tactic
        )
        target_tactic_manager = (
            target_agent.decision_engine.ai_engine.q_table_manager_tactic
        )
        self._copy_and_mutate_single_table(source_tactic_manager, target_tactic_manager)
        
        logger.debug(
            f"Cloned and mutated Q-tables (Strategy & Tactic) from {source_agent.id} to {target_agent.id}."
        )

    def _copy_and_mutate_single_table(self, source_manager: Any, target_manager: Any):
        """Helper to copy and mutate a single QTableManager's table."""
        # Deep copy the Q-table
        # Assuming q_table is Dict[State, Dict[Action, float]]
        # We need to be careful with deep copying if keys are objects, but here they are likely tuples/Enums which are immutable/safe.
        # But the inner dict needs to be copied.
        new_q_table = {}
        for state, actions in source_manager.q_table.items():
            new_q_table[state] = actions.copy()

        # Mutate the Q-table
        mutation_rate = getattr(self.config_module, "IMITATION_MUTATION_RATE", 0.1)
        mutation_magnitude = getattr(
            self.config_module, "IMITATION_MUTATION_MAGNITUDE", 0.05
        )

        for state in new_q_table:
            for action in new_q_table[state]:
                if random.random() < mutation_rate:
                    new_q_table[state][action] += random.uniform(
                        -mutation_magnitude, mutation_magnitude
                    )
        
        target_manager.q_table = new_q_table
