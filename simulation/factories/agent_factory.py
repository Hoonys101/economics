from __future__ import annotations
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import logging
import random
import copy

from simulation.core_agents import Household
from simulation.models import Talent
from simulation.utils.config_factory import create_config_dto
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.simulation.api import AgentCoreConfigDTO, AgentStateDTO
from modules.system.api import DEFAULT_CURRENCY
from simulation.ai.enums import Personality

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.systems.demographic_manager import DemographicManager

logger = logging.getLogger(__name__)

class HouseholdFactory:
    """
    Factory for creating Household agents.
    Encapsulates creation logic, configuration setup, and initial state hydration.
    """

    def __init__(self, config_module: Any):
        self.config_module = config_module

    def create_household(
        self,
        agent_id: int,
        simulation: Any,
        initial_age: float,
        gender: str,
        initial_assets: float = 0.0,
        generation: int = 0,
        parent_id: Optional[int] = None,
        spouse_id: Optional[int] = None,
        personality: Optional[Personality] = None,
        talent: Optional[Talent] = None,
        decision_engine: Optional[Any] = None,
        initial_needs: Optional[Dict[str, float]] = None
    ) -> Household:
        """
        Creates a fully initialized Household agent.
        """

        # 1. Config Setup
        hh_config_dto = create_config_dto(self.config_module, HouseholdConfigDTO)

        # 2. Core Config
        # Value Orientation: Try getting from engine, else config default
        vo = "Growth"
        if decision_engine and hasattr(decision_engine, 'value_orientation'):
            vo = decision_engine.value_orientation
        else:
            vo = getattr(self.config_module, 'DEFAULT_VALUE_ORIENTATION', 'Growth')

        # Get initial needs from config if not provided
        default_initial_needs = getattr(self.config_module, "INITIAL_NEEDS", {})

        core_config = AgentCoreConfigDTO(
            id=agent_id,
            name=f"Household_{agent_id}",
            value_orientation=vo,
            initial_needs=initial_needs if initial_needs else default_initial_needs.copy(),
            logger=simulation.logger,
            memory_interface=None
        )

        # 3. Defaults if not provided
        if talent is None:
            talent = Talent(base_learning_rate=1.0, max_potential={})

        if personality is None:
            personality = random.choice(list(Personality))

        # 4. Instantiate Household
        agent = Household(
            core_config=core_config,
            engine=decision_engine,
            talent=talent,
            goods_data=simulation.goods_data,
            personality=personality,
            config_dto=hh_config_dto,
            loan_market=simulation.markets.get("loan_market"),
            risk_aversion=1.0,
            initial_age=initial_age,
            gender=gender,
            parent_id=parent_id,
            generation=generation,
            initial_assets_record=initial_assets
        )

        # 5. Hydrate State (Assets)
        initial_state = AgentStateDTO(
            assets={DEFAULT_CURRENCY: initial_assets},
            inventory={},
            is_active=True
        )
        agent.load_state(initial_state)

        # 6. Additional Initializations
        if spouse_id:
            agent.spouse_id = spouse_id

        agent.education_level = 0
        base_wage = getattr(self.config_module, "INITIAL_WAGE", 10.0)
        agent.expected_wage = base_wage

        return agent

    def create_newborn(
        self,
        parent: Household,
        simulation: Any,
        new_id: int
    ) -> Household:
        """
        Creates a newborn household (child) from a parent.
        Handles inheritance of traits (personality, talent, brain).
        """
        # 1. Demographics
        initial_age = 0.0
        gender = random.choice(["M", "F"])
        generation = parent.generation + 1

        # 2. Inheritance Logic (Talent, Personality)
        child_talent = self._inherit_talent(parent.talent)
        child_personality = self._inherit_personality(parent.personality)

        # 3. Engine Creation (Brain)
        new_decision_engine = self._create_decision_engine_for_newborn(parent, simulation, new_id)

        # 4. Initial Assets (Zero - Gift transfer happens externally via SettlementSystem)
        initial_assets = 0.0

        # 5. Config
        initial_needs = getattr(self.config_module, "NEWBORN_INITIAL_NEEDS", None)

        # 6. Create Agent
        child = self.create_household(
            agent_id=new_id,
            simulation=simulation,
            initial_age=initial_age,
            gender=gender,
            initial_assets=initial_assets,
            generation=generation,
            parent_id=parent.id,
            spouse_id=None,
            personality=child_personality,
            talent=child_talent,
            decision_engine=new_decision_engine,
            initial_needs=initial_needs
        )

        # 7. Brain Inheritance (Weights)
        if hasattr(simulation, "ai_training_manager") and simulation.ai_training_manager:
            simulation.ai_training_manager.inherit_brain(parent, child)
        else:
            # logger might not be configured if strictly imported, but factory uses simulation.logger usually
            # But here we use 'logger' defined in module
            logger.warning("AITrainingManager not found for brain inheritance.")

        return child

    def _inherit_talent(self, parent_talent: Talent) -> Talent:
        """Inherit talent with mutation."""
        new_talent = copy.deepcopy(parent_talent)
        mutation_range = 0.1
        new_talent.base_learning_rate *= random.uniform(1.0 - mutation_range, 1.0 + mutation_range)
        return new_talent

    def _inherit_personality(self, parent_personality: Personality) -> Personality:
        """Inherit personality with potential mutation."""
        if random.random() < getattr(self.config_module, "MITOSIS_MUTATION_PROBABILITY", 0.1):
            return random.choice(list(Personality))
        return parent_personality

    def _create_decision_engine_for_newborn(self, parent: Household, simulation: Any, agent_id: int) -> Any:
        """Creates the decision engine for the newborn."""

        newborn_engine_type = getattr(self.config_module, "NEWBORN_ENGINE_TYPE", "AIDriven")
        # Check strategy override
        strategy = getattr(simulation, "strategy", None)
        if strategy and hasattr(strategy, "newborn_engine_type") and strategy.newborn_engine_type:
            newborn_engine_type = strategy.newborn_engine_type

        if str(newborn_engine_type).upper() == "RULE_BASED":
            from simulation.decisions.rule_based_household_engine import RuleBasedHouseholdDecisionEngine
            return RuleBasedHouseholdDecisionEngine(
                config_module=self.config_module,
                logger=simulation.logger
            )
        else:
            # AI Driven
            from simulation.ai.household_ai import HouseholdAI
            from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine

            ai_trainer = getattr(simulation, "ai_trainer", None)

            base_ai_engine = None
            if ai_trainer:
                base_ai_engine = ai_trainer.get_engine(parent.value_orientation)

            new_ai = HouseholdAI(
                agent_id=str(agent_id),
                ai_decision_engine=base_ai_engine,
            )

            engine = AIDrivenHouseholdDecisionEngine(
                ai_engine=new_ai,
                config_module=self.config_module,
                logger=simulation.logger
            )
            engine.loan_market = simulation.markets.get("loan_market")
            return engine
