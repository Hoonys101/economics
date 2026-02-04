from __future__ import annotations
from typing import Optional, TYPE_CHECKING, override

from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from modules.household.dtos import BioStateDTO, EconStateDTO, SocialStateDTO
    from simulation.dtos.config_dtos import HouseholdConfigDTO
    from modules.household.bio_component import BioComponent
    from modules.household.econ_component import EconComponent
    from simulation.decisions.base_decision_engine import BaseDecisionEngine
    from logging import Logger

class HouseholdReproductionMixin:
    """
    Mixin for Household reproduction and inheritance logic.
    Handles cloning (child creation) and heir designation.
    """

    # Type hints for properties expected on self
    id: int
    logger: Logger
    config: "HouseholdConfigDTO"
    _bio_state: "BioStateDTO"
    _econ_state: "EconStateDTO"
    _social_state: "SocialStateDTO"
    goods_info_map: dict
    decision_engine: "BaseDecisionEngine"
    value_orientation: str
    risk_aversion: float

    # Components
    bio_component: "BioComponent"
    econ_component: "EconComponent"

    @override
    def clone(self, new_id: int, initial_assets_from_parent: float, current_tick: int) -> "Household":
        """
        Clones the household. Orchestrates Bio and Econ cloning logic.
        """
        from simulation.core_agents import Household

        # 1. Bio Cloning (Demographics)
        offspring_demo = self.bio_component.create_offspring_demographics(
            self._bio_state, new_id, current_tick, self.config
        )

        # 2. Econ Cloning (Inheritance)
        # We need parent skills.
        econ_inheritance = self.econ_component.prepare_clone_state(
            self._econ_state, self._econ_state.skills, self.config
        )

        # 3. Create Decision Engine
        new_decision_engine = self._create_new_decision_engine(new_id)

        # 4. Instantiate New Household
        # Combine args
        cloned_household = Household(
            id=new_id,
            talent=self._econ_state.talent, # Copied reference
            goods_data=[g for g in self.goods_info_map.values()],
            initial_assets=initial_assets_from_parent,
            initial_needs=self._bio_state.needs.copy(), # Inherit current needs or reset? Usually reset.
            # BioComponent.create_offspring_demographics didn't return initial needs.
            # We'll use copy of parent needs as per original logic.

            decision_engine=new_decision_engine,
            value_orientation=self.value_orientation,
            personality=self._social_state.personality, # Inherit personality
            config_dto=self.config,
            loan_market=self.decision_engine.loan_market,
            risk_aversion=self.risk_aversion,
            logger=None,

            # Demographics from Bio
            initial_age=offspring_demo["initial_age"],
            gender=offspring_demo["gender"],
            parent_id=offspring_demo["parent_id"],
            generation=offspring_demo["generation"]
        )

        # 5. Apply Econ Inheritance
        cloned_household._econ_state.skills = econ_inheritance["skills"]
        cloned_household._econ_state.education_level = econ_inheritance["education_level"]
        cloned_household._econ_state.expected_wage = econ_inheritance["expected_wage"]
        cloned_household._econ_state.labor_skill = econ_inheritance["labor_skill"]
        if "aptitude" in econ_inheritance:
             cloned_household._econ_state.aptitude = econ_inheritance["aptitude"]

        return cloned_household

    def _create_new_decision_engine(self, new_id: int) -> AIDrivenHouseholdDecisionEngine:
        shared_ai_engine = self.decision_engine.ai_engine.ai_decision_engine
        new_ai_engine = HouseholdAI(
            agent_id=str(new_id),
            ai_decision_engine=shared_ai_engine,
            gamma=self.decision_engine.ai_engine.gamma,
            epsilon=self.decision_engine.ai_engine.action_selector.epsilon,
            base_alpha=self.decision_engine.ai_engine.base_alpha,
            learning_focus=self.decision_engine.ai_engine.learning_focus
        )
        return AIDrivenHouseholdDecisionEngine(
            ai_engine=new_ai_engine,
            config_module=self.config,
            logger=self.logger
        )

    def get_generational_similarity(self, other: "Household") -> float:
        talent_diff = abs(self._econ_state.talent.base_learning_rate - other._econ_state.talent.base_learning_rate)
        similarity = max(0.0, 1.0 - talent_diff)
        return similarity

    # --- IHeirProvider Implementation ---

    def get_heir(self) -> Optional[int]:
        """
        Returns the ID of the designated heir (Spouse -> Oldest Child -> None).
        """
        if self._bio_state.spouse_id is not None:
            return self._bio_state.spouse_id
        if self._bio_state.children_ids:
            return self._bio_state.children_ids[0]
        return None
