from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
import logging

from modules.household.api import ISocialComponent
from modules.household.dtos import SocialStateDTO
from simulation.dtos import LeisureEffectDTO
from simulation.ai.api import Personality

if TYPE_CHECKING:
    from simulation.dtos.config_dtos import HouseholdConfigDTO

logger = logging.getLogger(__name__)

class SocialComponent(ISocialComponent):
    """
    Stateless component managing social and psychological aspects of the Household.
    Operates on SocialStateDTO.
    """

    def calculate_social_status(
        self,
        state: SocialStateDTO,
        assets: float,
        luxury_inventory: Dict[str, float],
        config: HouseholdConfigDTO
    ) -> SocialStateDTO:
        """
        Calculates social status based on assets and luxury inventory.
        Logic migrated from PsychologyComponent.calculate_social_status.
        """
        new_state = state.copy()

        luxury_goods_value = sum(luxury_inventory.values()) # Assuming values are quantities?

        asset_weight = config.social_status_asset_weight
        luxury_weight = config.social_status_luxury_weight

        new_state.social_status = (
            assets * asset_weight
        ) + (luxury_goods_value * luxury_weight)

        return new_state

    def update_political_opinion(
        self,
        state: SocialStateDTO,
        survival_need: float
    ) -> SocialStateDTO:
        """
        Updates political approval based on needs.
        Logic migrated from PsychologyComponent.update_political_opinion.
        """
        new_state = state.copy()
        new_state.discontent = min(1.0, survival_need / 100.0)

        # Determine Approval (Tolerance = 0.4)
        if new_state.discontent < 0.4:
            new_state.approval_rating = 1
        else:
            new_state.approval_rating = 0

        return new_state

    def apply_leisure_effect(
        self,
        state: SocialStateDTO,
        labor_skill: float,
        children_count: int,
        leisure_hours: float,
        consumed_items: Dict[str, float],
        config: HouseholdConfigDTO
    ) -> Tuple[SocialStateDTO, float, LeisureEffectDTO]:
        """
        Applies leisure effects.
        Returns: (Updated Social State, Updated Labor Skill (value), Result DTO)
        Logic migrated from LeisureManager.
        """
        new_state = state.copy()

        # Determine Leisure Type
        has_children = children_count > 0
        has_education = consumed_items.get("education_service", 0.0) > 0
        has_luxury = (
            consumed_items.get("luxury_food", 0.0) > 0 or
            consumed_items.get("clothing", 0.0) > 0
        )

        leisure_type = "SELF_DEV"
        if has_children and has_education:
            leisure_type = "PARENTING"
        elif has_luxury:
            leisure_type = "ENTERTAINMENT"

        new_state.last_leisure_type = leisure_type

        # Get coefficients
        leisure_coeffs = config.leisure_coeffs
        coeffs = leisure_coeffs.get(leisure_type, {})
        utility_per_hour = coeffs.get("utility_per_hour", 0.0)
        xp_gain_per_hour = coeffs.get("xp_gain_per_hour", 0.0)
        productivity_gain = coeffs.get("productivity_gain", 0.0)

        utility_gained = leisure_hours * utility_per_hour
        xp_gained = leisure_hours * xp_gain_per_hour
        prod_gained = leisure_hours * productivity_gain

        new_labor_skill = labor_skill

        # Execute Effects
        if leisure_type == "SELF_DEV" and prod_gained > 0:
            new_labor_skill += prod_gained
            # Logging handled by Facade or we ignore context here

        return new_state, new_labor_skill, LeisureEffectDTO(
            leisure_type=leisure_type,
            leisure_hours=leisure_hours,
            utility_gained=utility_gained,
            xp_gained=xp_gained
        )

    def update_psychology(
        self,
        state: SocialStateDTO,
        bio_needs: Dict[str, float],
        assets: float,
        durable_assets: List[Dict[str, Any]],
        goods_info_map: Dict[str, Any],
        config: HouseholdConfigDTO,
        current_tick: int,
        market_data: Optional[Dict[str, Any]]
    ) -> Tuple[SocialStateDTO, Dict[str, float], List[Dict[str, Any]], bool]:
        """
        Updates psychological state and needs.
        Returns: (Updated Social State, Updated Needs, Updated Durable Assets List, Is Active (bool))
        Logic migrated from PsychologyComponent.
        """
        new_state = state.copy()
        new_needs = bio_needs.copy()
        is_active = True

        # 1. Apply Durable Asset Utility (Depreciation & Satisfaction)
        living_assets = []
        for asset in durable_assets:
            # Depreciation - We modify a copy of the dict if possible, or new dict.
            # asset is dict.
            new_asset = asset.copy()
            new_asset["remaining_life"] -= 1

            if new_asset["remaining_life"] > 0:
                living_assets.append(new_asset)
                # Utility Application
                good_info = goods_info_map.get(new_asset["item_id"], {})
                utility_effects = good_info.get("utility_effects", {})

                for need_type, base_utility in utility_effects.items():
                    effective_utility = base_utility * new_asset["quality"]
                    if need_type in new_needs:
                        new_needs[need_type] = max(0.0, new_needs[need_type] - effective_utility)

        # 2. Natural Growth based on Personality
        base_growth = config.base_desire_growth
        new_needs["survival"] = new_needs.get("survival", 0.0) + base_growth

        for k in ["asset", "social", "improvement", "quality"]:
            weight = new_state.desire_weights.get(k, 1.0)
            new_needs[k] = new_needs.get(k, 0.0) + (base_growth * weight)

        # Cap
        max_val = config.max_desire_value
        for k in new_needs:
            new_needs[k] = min(max_val, new_needs[k])

        # 3. Check Death Conditions
        death_threshold = config.survival_need_death_threshold
        if new_needs["survival"] >= death_threshold:
            new_state.survival_need_high_turns += 1
        else:
            new_state.survival_need_high_turns = 0

        # Assets Death Check
        assets_death_threshold = config.assets_death_threshold
        turns_threshold = config.household_death_turns_threshold

        if (assets <= assets_death_threshold or
            new_state.survival_need_high_turns >= turns_threshold):
            is_active = False
            # Logging handled by caller

        return new_state, new_needs, living_assets, is_active
