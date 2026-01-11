from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.personality import Personality

logger = logging.getLogger(__name__)

class PsychologyComponent:
    """
    Phase 22.5: Household Psychology Component
    Manages personality-driven desire weights, needs update logic,
    and political sentiment.
    """

    def __init__(self, owner: "Household", personality: "Personality", config_module: Any):
        self.owner = owner
        self.config = config_module
        self.personality = personality
        
        # Desire weights based on personality
        self.desire_weights: Dict[str, float] = {}
        self._initialize_desire_weights(personality)
        
        # State
        self.survival_need_high_turns = 0

    def _initialize_desire_weights(self, personality: "Personality"):
        """
        Initializes desire growth weights based on legacy Personality Enum.
        """
        from simulation.ai.enums import Personality
        
        # Default
        self.desire_weights = {
            "survival": 1.0,
            "asset": 1.0,
            "social": 1.0,
            "improvement": 1.0,
            "quality": 1.0
        }
        
        if personality in [Personality.MISER, Personality.CONSERVATIVE]:
            self.desire_weights.update({"asset": 1.5, "social": 0.5, "improvement": 0.5})
        elif personality in [Personality.STATUS_SEEKER, Personality.IMPULSIVE]:
            self.desire_weights.update({"asset": 0.5, "social": 1.5, "improvement": 0.5})
        elif personality == Personality.GROWTH_ORIENTED:
            self.desire_weights.update({"asset": 0.5, "social": 0.5, "improvement": 1.5})

    def update_needs(self, current_tick: int, market_data: Optional[Dict[str, Any]] = None):
        """
        Updates needs based on personality growth, durable utility, and death conditions.
        """
        # 1. Apply Durable Asset Utility (Depreciation & Satisfaction)
        for asset in list(self.owner.durable_assets):
            # Depreciation
            asset["remaining_life"] -= 1
            if asset["remaining_life"] <= 0:
                self.owner.durable_assets.remove(asset)
                continue

            # Utility Application
            good_info = self.owner.goods_info_map.get(asset["item_id"], {})
            utility_effects = good_info.get("utility_effects", {})

            for need_type, base_utility in utility_effects.items():
                effective_utility = base_utility * asset["quality"]
                if need_type in self.owner.needs:
                    self.owner.needs[need_type] = max(0.0, self.owner.needs[need_type] - effective_utility)

        # 2. Natural Growth based on Personality
        base_growth = self.config.BASE_DESIRE_GROWTH
        self.owner.needs["survival"] += base_growth
        
        for k in ["asset", "social", "improvement", "quality"]:
            weight = self.desire_weights.get(k, 1.0)
            self.owner.needs[k] = self.owner.needs.get(k, 0.0) + (base_growth * weight)

        # Cap
        for k in self.owner.needs:
            self.owner.needs[k] = min(self.config.MAX_DESIRE_VALUE, self.owner.needs[k])

        # 3. Check Death Conditions
        if self.owner.needs["survival"] >= self.config.SURVIVAL_NEED_DEATH_THRESHOLD:
            self.survival_need_high_turns += 1
        else:
            self.survival_need_high_turns = 0

        # Assets Death Check
        if (self.owner.assets <= self.config.ASSETS_DEATH_THRESHOLD or 
            self.survival_need_high_turns >= self.config.HOUSEHOLD_DEATH_TURNS_THRESHOLD):
            self.owner.is_active = False
            self._log_death(current_tick, market_data)

    def update_political_opinion(self):
        """
        Calculates approval rating based on discontent (Survival Need).
        """
        survival_need = self.owner.needs.get("survival", 0.0)
        discontent = survival_need / 100.0
        # If discontent < 0.4, Approve (1), else Disapprove (0)
        self.owner.approval_rating = 1 if discontent < 0.4 else 0

    def calculate_social_status(self):
        """
        Calculates social status based on assets and luxury inventory.
        """
        luxury_goods_value = 0.0
        for item_id, quantity in self.owner.inventory.items():
            good_info = self.owner.goods_info_map.get(item_id)
            if good_info and good_info.get("is_luxury", False):
                luxury_goods_value += quantity

        self.owner.social_status = (
            self.owner.assets * self.config.SOCIAL_STATUS_ASSET_WEIGHT
        ) + (luxury_goods_value * self.config.SOCIAL_STATUS_LUXURY_WEIGHT)

    def _log_death(self, current_tick: int, market_data: Optional[Dict[str, Any]]):
        """Internal helper for logging death forensics."""
        # Retrieve forensics data from market_data if available
        market_food_price = None
        job_vacancies = 0
        if market_data:
             goods_market = market_data.get("goods_market", {})
             market_food_price = goods_market.get("basic_food_current_sell_price")
             job_vacancies = market_data.get("job_vacancies", 0)

        logger.warning(
            f"AGENT_DEATH | ID: {self.owner.id} (Cause: starvation/insolvency)",
            extra={
                "tick": current_tick,
                "agent_id": self.owner.id,
                "survival_need": self.owner.needs["survival"],
                "assets": self.owner.assets,
                "market_food_price": market_food_price,
                "job_vacancies": job_vacancies,
                "tags": ["death", "autopsy"]
            }
        )
