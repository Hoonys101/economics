from __future__ import annotations
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import random
import logging

from modules.household.api import IBioComponent
from simulation.components.demographics_component import DemographicsComponent
from simulation.components.agent_lifecycle import AgentLifecycleComponent
from simulation.models import Skill
from modules.household.dtos import CloningRequestDTO

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.systems.api import LifecycleContext

logger = logging.getLogger(__name__)


class BioComponent(IBioComponent):
    """
    Manages biological and demographic aspects of the Household.
    Owns DemographicsComponent and AgentLifecycleComponent.
    """

    def __init__(
        self,
        owner: "Household",
        config_module: Any,
        initial_age: Optional[float] = None,
        gender: Optional[str] = None,
        parent_id: Optional[int] = None,
        generation: Optional[int] = None,
    ):
        self.owner = owner
        self.config_module = config_module

        # Defaults if not provided
        if initial_age is None:
            initial_age = random.uniform(20.0, 60.0)
        if gender is None:
            gender = random.choice(["M", "F"])
        if generation is None:
            generation = 0

        self.demographics = DemographicsComponent(
            owner=owner,
            initial_age=initial_age,
            gender=gender,
            parent_id=parent_id,
            generation=generation,
            config_module=config_module,
        )

        self.lifecycle_component = AgentLifecycleComponent(owner, config_module)

    @property
    def age(self) -> float:
        return self.demographics.age

    @property
    def gender(self) -> str:
        return self.demographics.gender

    @property
    def parent_id(self) -> Optional[int]:
        return self.demographics.parent_id

    @property
    def generation(self) -> int:
        return self.demographics.generation

    @property
    def spouse_id(self) -> Optional[int]:
        return self.demographics.spouse_id

    @property
    def children_ids(self) -> List[int]:
        return self.demographics.children_ids

    @property
    def children_count(self) -> int:
        return self.demographics.children_count

    def run_lifecycle(self, context: Dict[str, Any]):
        """
        Executes biological lifecycle updates: aging, death check, needs update (via lifecycle component).
        """
        # 1. Update Needs & Taxes via AgentLifecycleComponent
        # Ensure context matches LifecycleContext expected by AgentLifecycleComponent
        self.lifecycle_component.run_tick(context)

        # 2. Aging & Death via DemographicsComponent
        current_tick = context.get("time", 0)
        self.demographics.age_one_tick(current_tick)

    def clone(self, request: CloningRequestDTO) -> "Household":
        """
        Creates a new Household instance with copied biological/demographic state.
        This handles the 'biological' aspect of mitosis.
        """
        # Avoid circular import
        from simulation.core_agents import Household

        # 1. Create offspring demographics data
        offspring_demo_data = self.demographics.create_offspring_demographics(
            request.new_id, request.current_tick
        )

        # 2. Create new Household instance
        # We need to access owner's properties to pass to constructor
        # Note: Decision Engine creation is handled by Household (Facade) or delegated.
        # But Household constructor requires a decision engine.
        # We'll use the owner's method to create it (if exposed) or create a placeholder?
        # Household.clone used `_create_new_decision_engine`.
        # Since BioComponent shouldn't know about AI engine details, we might have a problem.
        # However, the prompt says "Move the clone() method logic... It will only be responsible for creating a new Household...".
        # The Household constructor REQUIRES decision_engine.

        # We can call a helper on the owner to get the engine, or pass it in.
        # But `clone` signature is fixed by IBioComponent (takes CloningRequestDTO).

        # Strategy: The BioComponent will call `Household(...)`.
        # Use `self.owner._create_new_decision_engine(request.new_id)` which is existing logic.
        # This assumes `owner` has this method.

        new_decision_engine = self.owner._create_new_decision_engine(request.new_id)

        cloned_household = Household(
            id=request.new_id,
            talent=self.owner.talent,  # Inherit talent object (immutable?) or should copy? Original code passed self.talent.
            goods_data=[g for g in self.owner.goods_info_map.values()],
            initial_assets=request.initial_assets_from_parent,
            initial_needs=self.owner.needs.copy(),
            decision_engine=new_decision_engine,
            value_orientation=self.owner.value_orientation,
            personality=self.owner.personality,
            config_module=self.config_module,
            loan_market=self.owner.decision_engine.loan_market,
            risk_aversion=self.owner.risk_aversion,
            logger=self.owner.logger,
            **offspring_demo_data,
        )

        # Attribute Sync (Biological/Physical mainly, but some Econ state is copied in original clone)
        # Original clone copied: skills, inventory, labor_skill, aptitude.

        # Skills (Biological/Learned capability)
        cloned_household.skills = {
            k: Skill(v.domain, v.value, v.observability)
            for k, v in self.owner.skills.items()
        }

        # Inventory (Inheritance? Usually empty for newborn, but maybe mitosis implies split?)
        # Original code copied inventory, leading to duplication.
        # Fixed to start empty (Zero-Sum resource logic).
        cloned_household.inventory = {}

        # Labor Skill
        cloned_household.labor_skill = self.owner.labor_skill

        # Aptitude Inheritance (WO-054)
        raw_aptitude = (self.owner.aptitude * 0.6) + (random.gauss(0.5, 0.15) * 0.4)
        cloned_household.aptitude = max(0.0, min(1.0, raw_aptitude))

        return cloned_household

    def get_generational_similarity(self, other: "Household") -> float:
        return self.demographics.get_generational_similarity(
            self.owner.talent.base_learning_rate, other.talent.base_learning_rate
        )
