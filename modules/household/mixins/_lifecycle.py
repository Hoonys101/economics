from __future__ import annotations
from typing import List, Dict, Optional, Any, TYPE_CHECKING, override
from logging import Logger

from simulation.dtos import ConsumptionResult, LeisureEffectDTO
from simulation.dtos.scenario import StressScenarioConfig
from simulation.ai.api import Personality
from simulation.systems.api import LearningUpdateContext

if TYPE_CHECKING:
    from modules.household.dtos import BioStateDTO, EconStateDTO, SocialStateDTO
    from modules.simulation.dtos.api import HouseholdConfigDTO
    from modules.household.consumption_manager import ConsumptionManager
    from modules.household.bio_component import BioComponent
    from modules.household.econ_component import EconComponent
    from modules.household.social_component import SocialComponent
    from modules.household.political_component import PoliticalComponent
    from simulation.decisions.base_decision_engine import BaseDecisionEngine

class HouseholdLifecycleMixin:
    """
    Mixin for Household lifecycle and consumption logic.
    Handles needs updates, consumption, leisure, and aging.
    """

    # Type hints for properties expected on self
    id: int
    logger: Logger
    config: "HouseholdConfigDTO"
    _bio_state: "BioStateDTO"
    _econ_state: "EconStateDTO"
    _social_state: "SocialStateDTO"
    goods_info_map: Dict[str, Any]
    distress_tick_counter: int

    # Components
    consumption_manager: "ConsumptionManager"
    bio_component: "BioComponent"
    econ_component: "EconComponent"
    social_component: "SocialComponent"
    political_component: "PoliticalComponent"
    decision_engine: "BaseDecisionEngine"

    def consume(self, item_id: str, quantity: float, current_time: int) -> ConsumptionResult:
        # Delegate to ConsumptionManager
        self._econ_state, new_needs, result = self.consumption_manager.consume(
            self._econ_state,
            self._bio_state.needs,
            item_id,
            quantity,
            current_time,
            self.goods_info_map.get(item_id, {}),
            self.config
        )
        self._bio_state.needs = new_needs
        return result

    @override
    def update_needs(self, current_tick: int, market_data: Optional[Dict[str, Any]] = None):
        """
        Updates agent needs and lifecycle (Bio, Social, Econ-Work).
        Replaces legacy AgentLifecycleComponent.
        """
        if not self._bio_state.is_active:
            return

        # 1. Work (Econ)
        if self._econ_state.is_employed:
            self._econ_state, labor_res = self.econ_component.work(
                self._econ_state, 8.0, self.config
            )
            # We could log labor_res if needed

        # 2. Update Psychology/Social (Needs & Death Check)
        self._social_state, new_needs, new_durable_assets, is_active = self.social_component.update_psychology(
            self._social_state,
            self._bio_state.needs,
            self._econ_state.assets,
            self._econ_state.durable_assets,
            self.goods_info_map,
            self.config,
            current_tick,
            market_data
        )
        self._bio_state.needs = new_needs
        self._econ_state.durable_assets = new_durable_assets

        # WO-167: Grace Protocol - Override death if in distress grace period
        if not is_active:
            self.distress_tick_counter += 1
            if self.distress_tick_counter <= getattr(self.config, "distress_grace_period_ticks", 10):
                is_active = True
                self.logger.info(
                    f"GRACE_PROTOCOL_SAVE | Household {self.id} saved from death. Distress tick {self.distress_tick_counter}",
                    extra={"agent_id": self.id, "tags": ["grace_protocol", "survival"]}
                )
        else:
            self.distress_tick_counter = 0

        self._bio_state.is_active = is_active

        # 3. Update Political Opinion
        gov_party = None
        if market_data and "government" in market_data:
            gov_party = market_data["government"].get("party")

        self._social_state = self.political_component.update_opinion(
            self._social_state,
            self._bio_state.needs.get("survival", 0.0),
            gov_party
        )

        # 4. Aging (Bio) - Also checks natural death
        self._bio_state = self.bio_component.age_one_tick(
            self._bio_state, self.config, current_tick
        )

        # 5. Skill Updates
        self._econ_state = self.econ_component.update_skills(self._econ_state, self.config)

    def apply_leisure_effect(self, leisure_hours: float, consumed_items: Dict[str, float]) -> LeisureEffectDTO:
        self._social_state, self._econ_state.labor_skill, result = self.social_component.apply_leisure_effect(
            self._social_state,
            self._econ_state.labor_skill,
            len(self._bio_state.children_ids),
            leisure_hours,
            consumed_items,
            self.config
        )
        return result

    @override
    def update_perceived_prices(self, market_data: Dict[str, Any], stress_scenario_config: Optional[StressScenarioConfig] = None) -> None:
        self._econ_state = self.econ_component.update_perceived_prices(
            self._econ_state, market_data, self.goods_info_map, stress_scenario_config, self.config
        )

    def initialize_demographics(
        self,
        age: float,
        gender: str,
        parent_id: Optional[int],
        generation: int,
        spouse_id: Optional[int] = None
    ) -> None:
        """
        Explicitly initializes demographic state.
        Used by DemographicManager during agent creation.
        """
        self._bio_state.age = age
        self._bio_state.gender = gender
        self._bio_state.parent_id = parent_id
        self._bio_state.generation = generation
        self._bio_state.spouse_id = spouse_id

    def initialize_personality(self, personality: Personality, desire_weights: Dict[str, float]) -> None:
        """
        Explicitly initializes personality and desire weights.
        Used by DemographicManager and AITrainingManager (during brain inheritance).
        """
        self._social_state.personality = personality
        self._social_state.desire_weights = desire_weights

    def update_learning(self, context: LearningUpdateContext) -> None:
        reward = context["reward"]
        next_agent_data = context["next_agent_data"]
        next_market_data = context["next_market_data"]

        self.decision_engine.ai_engine.update_learning_v2(
            reward=reward,
            next_agent_data=next_agent_data,
            next_market_data=next_market_data,
        )

    def add_education_xp(self, xp: float) -> None:
        self._econ_state.education_xp += xp

    def add_durable_asset(self, asset: Dict[str, Any]) -> None:
        from modules.household.dtos import DurableAssetDTO
        dto = DurableAssetDTO(
            item_id=asset['item_id'],
            quality=asset['quality'],
            remaining_life=asset['remaining_life']
        )
        self._econ_state.durable_assets.append(dto)
