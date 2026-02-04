from __future__ import annotations
import logging
import random
from typing import List, Any, TYPE_CHECKING
from simulation.ai.api import Personality # Added import

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.ai.household_ai import HouseholdAI

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

    def inherit_brain(self, parent_agent: Household, child_agent: Household) -> None:
        """
        Transfers knowledge (Q-Tables) and personality from parent to child.
        """
        # 1. Personality Inheritance (Mutation)
        mutation_prob = getattr(self.config_module, "MITOSIS_MUTATION_PROBABILITY", 0.2)
        if random.random() < mutation_prob:
            # Randomly mutate personality
            new_personality = random.choice(list(Personality))
            logger.info(
                f"MUTATION | {child_agent.id} mutated personality to {new_personality.name}",
                extra={"agent_id": child_agent.id, "tags": ["mitosis", "mutation"]}
            )
        else:
            # Inherit parent personality
            new_personality = parent_agent.personality

        # Recalculate desire weights based on (possibly new) personality
        # Phase 22.5: Psychology Component update
        # Use initialize_personality to set both personality and weights atomically

        weights = {"survival": 1.0, "asset": 1.0, "social": 1.0, "improvement": 1.0, "quality": 1.0}

        if new_personality in [Personality.MISER, Personality.CONSERVATIVE]:
            weights = {"survival": 1.0, "asset": 1.5, "social": 0.5, "improvement": 0.5, "quality": 1.0}
        elif new_personality in [Personality.STATUS_SEEKER, Personality.IMPULSIVE]:
            weights = {"survival": 1.0, "asset": 0.5, "social": 1.5, "improvement": 0.5, "quality": 1.0}
        elif new_personality == Personality.GROWTH_ORIENTED:
            weights = {"survival": 1.0, "asset": 0.5, "social": 0.5, "improvement": 1.5, "quality": 1.0}

        child_agent.initialize_personality(new_personality, weights)

        # 2. Q-Table Cloning
        self._clone_and_mutate_q_table(parent_agent, child_agent)

        # 3. Education XP Inheritance Bonus (Task #6)
        import math
        education_xp = getattr(parent_agent, "education_xp", 0.0)
        sensitivity = getattr(self.config_module, "EDUCATION_SENSITIVITY", 0.1)
        base_rate = getattr(self.config_module, "BASE_LEARNING_RATE", 0.1)
        max_rate = getattr(self.config_module, "MAX_LEARNING_RATE", 0.5)

        xp_bonus = math.log1p(education_xp) * sensitivity
        
        # Check if child decision engine has AI engine (RuleBased agents might not)
        if hasattr(child_agent.decision_engine, "ai_engine"):
            child_ai = child_agent.decision_engine.ai_engine
            child_ai.base_alpha = min(max_rate, base_rate + xp_bonus)

            logger.info(
                f"EDUCATION_INHERITANCE | Child {child_agent.id} base_alpha: {child_ai.base_alpha:.4f} (Bonus: {xp_bonus:.4f})",
                extra={"agent_id": child_agent.id, "tags": ["mitosis", "education"]}
            )


    def _get_top_performing_agents(self, percentile: float | None = None) -> List[Household]:
        if percentile is None:
            percentile = getattr(self.config_module, "TOP_PERFORMING_PERCENTILE", 0.1)
        """Identifies the top-performing agents based on their assets."""
        if not self.agents:
            return []

        # Fix for Phase 33 Multi-Currency
        def get_assets(a):
            if isinstance(a.assets, dict):
                 from modules.system.api import DEFAULT_CURRENCY
                 return a.assets.get(DEFAULT_CURRENCY, 0.0)
            return a.assets

        sorted_agents = sorted(self.agents, key=get_assets, reverse=True)
        top_n = max(1, int(len(self.agents) * percentile))
        return sorted_agents[:top_n]

    def _get_under_performing_agents(self, percentile: float | None = None) -> List[Household]:
        if percentile is None:
            percentile = getattr(self.config_module, "UNDER_PERFORMING_PERCENTILE", 0.5)
        """Identifies the under-performing agents based on their assets."""
        if not self.agents:
            return []

        # Fix for Phase 33 Multi-Currency
        def get_assets(a):
            if isinstance(a.assets, dict):
                 from modules.system.api import DEFAULT_CURRENCY
                 return a.assets.get(DEFAULT_CURRENCY, 0.0)
            return a.assets

        sorted_agents = sorted(self.agents, key=get_assets) # Ascending
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

        # FIX: Check if decision engines have 'ai_engine' attribute (skip RuleBased engines)
        if not hasattr(source_agent.decision_engine, "ai_engine") or not hasattr(target_agent.decision_engine, "ai_engine"):
            return

        source_ai = source_agent.decision_engine.ai_engine
        target_ai = target_agent.decision_engine.ai_engine

        # --- Handle V2 HouseholdAI Q-Tables (q_consumption, q_work, q_investment) ---
        if hasattr(source_ai, "q_consumption") and hasattr(target_ai, "q_consumption"):
            # Clone Consumption Q-Tables
            for item_id, source_manager in source_ai.q_consumption.items():
                if item_id not in target_ai.q_consumption:
                    from simulation.ai.q_table_manager import QTableManager
                    target_ai.q_consumption[item_id] = QTableManager()

                target_manager = target_ai.q_consumption[item_id]
                self._copy_and_mutate_single_table(source_manager, target_manager)

        if hasattr(source_ai, "q_work") and hasattr(target_ai, "q_work"):
            self._copy_and_mutate_single_table(source_ai.q_work, target_ai.q_work)

        if hasattr(source_ai, "q_investment") and hasattr(target_ai, "q_investment"):
            self._copy_and_mutate_single_table(source_ai.q_investment, target_ai.q_investment)

        # --- Handle Legacy Q-Tables (Strategy/Tactic) ---
        # Clone Strategy Q-Table
        source_strategy_manager = getattr(source_ai, "q_table_manager_strategy", None)
        target_strategy_manager = getattr(target_ai, "q_table_manager_strategy", None)

        if source_strategy_manager and target_strategy_manager:
            self._copy_and_mutate_single_table(source_strategy_manager, target_strategy_manager)

        # Clone Tactic Q-Table
        source_tactic_manager = getattr(source_ai, "q_table_manager_tactic", None)
        target_tactic_manager = getattr(target_ai, "q_table_manager_tactic", None)

        if source_tactic_manager and target_tactic_manager:
            self._copy_and_mutate_single_table(source_tactic_manager, target_tactic_manager)
        
        logger.debug(
            f"Cloned and mutated Q-tables from {source_agent.id} to {target_agent.id}."
        )

    def _copy_and_mutate_single_table(self, source_manager: Any, target_manager: Any):
        """Helper to copy and mutate a single QTableManager's table."""
        # Deep copy the Q-table
        new_q_table = {}
        for state, actions in source_manager.q_table.items():
            new_q_table[state] = actions.copy()

        # Mutate the Q-table
        # Use MITOSIS mutation rate if defined, else fallback to imitation rate
        mitosis_rate = getattr(self.config_module, "MITOSIS_Q_TABLE_MUTATION_RATE", None)
        imitation_rate = getattr(self.config_module, "IMITATION_MUTATION_RATE", 0.1)

        mutation_rate = mitosis_rate if mitosis_rate is not None else imitation_rate

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

    def end_episode(self, agents: List[Any]) -> None:
        """Called at the end of a simulation episode."""
        logger.info("End of episode. Saving learning data if applicable.")
        # Future: Save Q-tables or model weights here
