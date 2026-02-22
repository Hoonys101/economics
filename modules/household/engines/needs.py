from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging

from modules.household.api import INeedsEngine, NeedsInputDTO, NeedsOutputDTO, PrioritizedNeed
from modules.household.dtos import BioStateDTO

logger = logging.getLogger(__name__)

class NeedsEngine(INeedsEngine):
    """
    Stateless engine managing need decay, satisfaction from durable assets, and need prioritization.
    Logic migrated from SocialComponent/PsychologyComponent.
    """

    def evaluate_needs(self, input_dto: NeedsInputDTO) -> NeedsOutputDTO:
        bio_state = input_dto.bio_state
        econ_state = input_dto.econ_state
        social_state = input_dto.social_state
        config = input_dto.config
        goods_data = input_dto.goods_data

        new_bio_state = bio_state.copy()

        # 1. Apply Durable Asset Utility (Depreciation handled in ConsumptionEngine)
        # We assume durable assets provide utility based on their CURRENT state (before decay at end of tick)
        for asset in econ_state.durable_assets:
            item_id = asset["item_id"]
            if asset["remaining_life"] > 0:
                good_info = goods_data.get(item_id, {})
                utility_effects = good_info.get("utility_effects", {})

                for need_type, base_utility in utility_effects.items():
                    effective_utility = base_utility * asset["quality"]
                    if need_type in new_bio_state.needs:
                        new_bio_state.needs[need_type] = max(0.0, new_bio_state.needs[need_type] - effective_utility)

        # 2. Natural Growth (Decay) based on Config & Personality
        # Logic from SocialComponent.update_psychology
        base_growth = config.base_desire_growth

        # --- Household Merger Scaling ---
        household_size = 1
        if new_bio_state.spouse_id is not None:
            household_size += 1
        if new_bio_state.children_ids:
            household_size += len(new_bio_state.children_ids)

        # Scale Growth: Linear for survival, Sub-linear for others (Economies of Scale)
        survival_scale = float(household_size)
        other_scale = household_size ** 0.7

        new_bio_state.needs["survival"] = new_bio_state.needs.get("survival", 0.0) + (base_growth * survival_scale)

        for k in ["asset", "social", "improvement", "quality"]:
            weight = social_state.desire_weights.get(k, 1.0)
            new_bio_state.needs[k] = new_bio_state.needs.get(k, 0.0) + (base_growth * weight * other_scale)

        # Cap Needs
        max_val = config.max_desire_value
        for k in new_bio_state.needs:
            new_bio_state.needs[k] = min(max_val, new_bio_state.needs[k])

        # 3. Check Death Conditions (Survival Need)
        death_threshold = config.survival_need_death_threshold
        if new_bio_state.needs["survival"] >= death_threshold:
            new_bio_state.survival_need_high_turns += 1
        else:
            new_bio_state.survival_need_high_turns = 0

        if new_bio_state.survival_need_high_turns >= config.survival_need_death_ticks_threshold:
            new_bio_state.is_active = False
            # Logging handled here for visibility
            logger.info(f"NEEDS_DEATH | Agent {bio_state.id} died of starvation (Needs). High turns: {new_bio_state.survival_need_high_turns}")

        # 4. Prioritize Needs
        prioritized_needs = self._prioritize_needs(new_bio_state.needs, social_state.desire_weights)

        # Wave 4.3: Medical Need Injection
        if new_bio_state.has_disease:
            medical_need = PrioritizedNeed(
                need_id="medical",
                urgency=999.0, # Immediate priority above survival
                deficit=100.0
            )
            # Insert at top
            prioritized_needs.insert(0, medical_need)

        return NeedsOutputDTO(
            bio_state=new_bio_state,
            prioritized_needs=prioritized_needs
        )

    def _prioritize_needs(self, needs: Dict[str, float], desire_weights: Dict[str, float]) -> List[PrioritizedNeed]:
        """
        Creates a list of prioritized needs based on urgency (need value) and weights.
        """
        p_needs = []
        for need_id, value in needs.items():
            weight = desire_weights.get(need_id, 1.0)
            # Urgency score: value * weight? Or just value relative to max?
            # Urgency is usually 0.0 to 1.0 (relative to max_desire_value).
            # But let's use the raw value scaled by weight for sorting.
            score = value * weight

            p_needs.append(PrioritizedNeed(
                need_id=need_id,
                urgency=score,
                deficit=value # Usually need value is the deficit (0 is satisfied, 100 is starving)
            ))

        # Sort by urgency descending
        p_needs.sort(key=lambda x: x.urgency, reverse=True)
        return p_needs
