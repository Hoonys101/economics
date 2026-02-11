from __future__ import annotations
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import logging
import random
import copy

from simulation.core_agents import Household
from simulation.models import Talent
from modules.simulation.api import AgentCoreConfigDTO, AgentStateDTO
from modules.system.api import DEFAULT_CURRENCY
from simulation.ai.api import Personality
from modules.household.api import HouseholdFactoryContext, IHouseholdFactory

logger = logging.getLogger(__name__)

class HouseholdFactory:
    """
    Factory for creating Household agents.
    Encapsulates creation logic, configuration setup, and initial state hydration.
    """

    def __init__(self, context: HouseholdFactoryContext):
        self.context = context

    def _create_base_household(
        self,
        agent_id: int,
        initial_age: float,
        gender: str,
        initial_assets: int = 0,
        generation: int = 0,
        parent_id: Optional[int] = None,
        spouse_id: Optional[int] = None,
        personality: Optional[Personality] = None,
        talent: Optional[Talent] = None,
        decision_engine: Optional[Any] = None,
        initial_needs: Optional[Dict[str, float]] = None
    ) -> Household:
        """
        Internal method to create a fully initialized Household agent.
        """
        # 1. Config Setup (Used from context)
        hh_config_dto = self.context.household_config_dto
        core_config_module = self.context.core_config_module

        # 2. Core Config
        # Value Orientation: Try getting from engine, else config default
        vo = "Growth"
        if decision_engine and hasattr(decision_engine, 'value_orientation'):
            vo = decision_engine.value_orientation
        else:
            vo = getattr(core_config_module, 'DEFAULT_VALUE_ORIENTATION', 'Growth')

        # Get initial needs from config if not provided
        default_initial_needs = getattr(core_config_module, "INITIAL_NEEDS", {})

        core_config = AgentCoreConfigDTO(
            id=agent_id,
            name=f"Household_{agent_id}",
            value_orientation=vo,
            initial_needs=initial_needs if initial_needs else default_initial_needs.copy(),
            logger=logger,
            memory_interface=self.context.memory_system
        )

        # 3. Defaults if not provided
        if talent is None:
            talent = Talent(base_learning_rate=1.0, max_potential={})

        if personality is None:
            personality = random.choice(list(Personality))

        # 4. Instantiate Household
        # Note: We pass markets and goods_data from context
        agent = Household(
            core_config=core_config,
            engine=decision_engine,
            talent=talent,
            goods_data=self.context.goods_data,
            personality=personality,
            config_dto=hh_config_dto,
            loan_market=self.context.loan_market,
            risk_aversion=1.0,
            initial_age=initial_age,
            gender=gender,
            parent_id=parent_id,
            generation=generation,
            initial_assets_record=int(initial_assets)
        )

        # 5. Hydrate State (Assets)
        initial_state = AgentStateDTO(
            assets={DEFAULT_CURRENCY: int(initial_assets)},
            inventory={},
            is_active=True
        )
        agent.load_state(initial_state)

        # 6. Additional Initializations
        if spouse_id:
            agent.spouse_id = spouse_id

        agent.education_level = 0
        base_wage = getattr(core_config_module, "INITIAL_WAGE", 10.0)
        agent.expected_wage = int(base_wage * 100) # Convert to pennies

        # Inject dependencies
        agent.decision_engine.markets = self.context.markets
        agent.decision_engine.goods_data = self.context.goods_data
        if hasattr(agent, 'settlement_system'):
            agent.settlement_system = self.context.settlement_system

        # Register with AI Training Manager
        if self.context.ai_training_manager:
            self.context.ai_training_manager.agents.append(agent)

        return agent

    def create_newborn(
        self,
        parent: Household,
        new_id: int,
        initial_assets: int, # This is the gift amount
        current_tick: int
    ) -> Household:
        """
        Creates a newborn household (child) from a parent.
        Handles inheritance of traits (personality, talent, brain).
        Enforces Zero-Sum integrity for initial assets (gift).
        """
        # 1. Demographics
        initial_age = 0.0
        gender = random.choice(["M", "F"])
        generation = parent.generation + 1

        # 2. Inheritance Logic (Talent, Personality)
        child_talent = self._inherit_talent(parent.talent)
        child_personality = self._inherit_personality(parent.personality)

        # 3. Engine Creation (Brain)
        new_decision_engine = self._create_decision_engine_for_newborn(parent, new_id)

        # 4. Config
        initial_needs = getattr(self.context.core_config_module, "NEWBORN_INITIAL_NEEDS", None)

        # 5. Create Agent with 0 assets (to be funded via transfer)
        child = self._create_base_household(
            agent_id=new_id,
            initial_age=initial_age,
            gender=gender,
            initial_assets=0,
            generation=generation,
            parent_id=parent.id,
            spouse_id=None,
            personality=child_personality,
            talent=child_talent,
            decision_engine=new_decision_engine,
            initial_needs=initial_needs
        )

        # 6. Brain Inheritance (Weights)
        if self.context.ai_training_manager:
            self.context.ai_training_manager.inherit_brain(parent, child)
        else:
            logger.warning("AITrainingManager not found for brain inheritance.")

        # 7. Zero-Sum Transfer of Gift
        if initial_assets > 0:
            # Transfer from Parent to Child
            self.context.settlement_system.transfer(
                sender=parent,
                receiver=child,
                amount=initial_assets,
                transaction_type="BIRTH_GIFT",
                tick=current_tick
            )

        return child

    def create_immigrant(
        self,
        new_id: int,
        current_tick: int,
        initial_assets: int
    ) -> Household:
        """Creates a new household representing an immigrant."""
        # Random demographics
        age_range = getattr(self.context.core_config_module, "initial_household_age_range", (20, 60))
        initial_age = random.uniform(*age_range)
        gender = random.choice(["M", "F"])

        # Logic for immigrant decision engine
        engine = self._create_default_decision_engine(new_id)

        immigrant = self._create_base_household(
            agent_id=new_id,
            initial_age=initial_age,
            gender=gender,
            initial_assets=initial_assets, # External injection
            decision_engine=engine
        )
        return immigrant

    def create_initial_population(
        self,
        num_agents: int
    ) -> List[Household]:
        """Creates the initial population of households for the simulation."""
        agents = []
        mean_assets = int(getattr(self.context.core_config_module, "initial_household_assets_mean", 1000) * 100) # Pennies

        for i in range(num_agents):
            agent_id = i

            assets = int(random.gauss(mean_assets, mean_assets * 0.2))
            assets = max(0, assets)

            age_range = getattr(self.context.core_config_module, "initial_household_age_range", (20, 60))
            initial_age = random.uniform(*age_range)
            gender = random.choice(["M", "F"])

            engine = self._create_default_decision_engine(agent_id)

            agent = self._create_base_household(
                agent_id=agent_id,
                initial_age=initial_age,
                gender=gender,
                initial_assets=assets,
                decision_engine=engine
            )
            agents.append(agent)

        return agents

    def _inherit_talent(self, parent_talent: Talent) -> Talent:
        """Inherit talent with mutation."""
        new_talent = copy.deepcopy(parent_talent)
        mutation_range = 0.1
        new_talent.base_learning_rate *= random.uniform(1.0 - mutation_range, 1.0 + mutation_range)
        return new_talent

    def _inherit_personality(self, parent_personality: Personality) -> Personality:
        """Inherit personality with potential mutation."""
        if random.random() < getattr(self.context.core_config_module, "MITOSIS_MUTATION_PROBABILITY", 0.1):
            return random.choice(list(Personality))
        return parent_personality

    def _create_decision_engine_for_newborn(self, parent: Household, agent_id: int) -> Any:
        """Creates the decision engine for the newborn."""
        return self._create_engine_logic(agent_id, parent_value_orientation=parent.value_orientation)

    def _create_default_decision_engine(self, agent_id: int) -> Any:
        return self._create_engine_logic(agent_id)

    def _create_engine_logic(self, agent_id: int, parent_value_orientation: Optional[str] = None) -> Any:
        newborn_engine_type = getattr(self.context.core_config_module, "NEWBORN_ENGINE_TYPE", "AIDriven")

        if str(newborn_engine_type).upper() == "RULE_BASED":
            from simulation.decisions.rule_based_household_engine import RuleBasedHouseholdDecisionEngine
            return RuleBasedHouseholdDecisionEngine(
                config_module=self.context.core_config_module,
                logger=logger
            )
        else:
            # AI Driven
            from simulation.ai.household_ai import HouseholdAI
            from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine

            base_ai_engine = None
            if self.context.ai_training_manager:
                # Use parent VO if available, else random or default
                vo = parent_value_orientation or "Growth"
                base_ai_engine = self.context.ai_training_manager.get_engine(vo)

            new_ai = HouseholdAI(
                agent_id=str(agent_id),
                ai_decision_engine=base_ai_engine,
            )

            engine = AIDrivenHouseholdDecisionEngine(
                ai_engine=new_ai,
                config_module=self.context.core_config_module,
                logger=logger
            )
            engine.loan_market = self.context.loan_market
            return engine
