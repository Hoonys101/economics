from __future__ import annotations
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import random
import logging

from modules.household.api import ISocialComponent
from simulation.components.psychology_component import PsychologyComponent
from simulation.components.leisure_manager import LeisureManager
from simulation.ai.api import Personality
from simulation.dtos import LeisureEffectDTO

if TYPE_CHECKING:
    from simulation.core_agents import Household

class SocialComponent(ISocialComponent):
    """
    Manages social and psychological aspects of the Household.
    Owns PsychologyComponent and LeisureManager.
    """
    def __init__(self, owner: "Household", config_module: Any, personality: Personality, initial_assets: float = 0.0):
        self.owner = owner
        self.config_module = config_module
        self.logger = owner.logger
        self.personality = personality

        # Sub-components
        self.psychology = PsychologyComponent(owner, personality, config_module)
        self.leisure = LeisureManager(owner, config_module)

        # State
        self.approval_rating: int = 1
        self.discontent: float = 0.0
        self.last_leisure_type: "LeisureType" = "IDLE"

        # Personality Attributes (Randomized)
        self.patience: float = max(0.0, min(1.0, 0.5 + random.uniform(-0.3, 0.3)))
        self.optimism: float = max(0.0, min(1.0, 0.5 + random.uniform(-0.3, 0.3)))
        self.ambition: float = max(0.0, min(1.0, 0.5 + random.uniform(-0.3, 0.3)))

        # Vanity - Conformity
        conformity_ranges = getattr(config_module, "CONFORMITY_RANGES", {})
        c_min, c_max = conformity_ranges.get(personality.name, conformity_ranges.get(None, (0.3, 0.7)))
        self.conformity: float = random.uniform(c_min, c_max)
        self.social_rank: float = 0.5

        # Brand Economy Traits
        # Initialize quality_preference based on Personality and Wealth
        # Note: We use initial_assets here because owner.assets might not be set yet
        mean_assets = getattr(config_module, "INITIAL_HOUSEHOLD_ASSETS_MEAN", 1000.0) # Fallback
        is_wealthy = initial_assets > mean_assets * 1.5
        is_poor = initial_assets < mean_assets * 0.5

        if personality == Personality.STATUS_SEEKER or is_wealthy:
            # Snob
            min_pref = getattr(config_module, "QUALITY_PREF_SNOB_MIN", 0.7)
            self.quality_preference = random.uniform(min_pref, 1.0)
        elif personality == Personality.MISER or is_poor:
            # Miser
            max_pref = getattr(config_module, "QUALITY_PREF_MISER_MAX", 0.3)
            self.quality_preference = random.uniform(0.0, max_pref)
        else:
            # Average
            min_snob = getattr(config_module, "QUALITY_PREF_SNOB_MIN", 0.7)
            max_miser = getattr(config_module, "QUALITY_PREF_MISER_MAX", 0.3)
            self.quality_preference = random.uniform(max_miser, min_snob)

        self.brand_loyalty: Dict[int, float] = {}
        self.last_purchase_memory: Dict[str, int] = {}

    def calculate_social_status(self) -> None:
        self.psychology.calculate_social_status()

    def update_political_opinion(self) -> None:
        """
        Phase 17-5: Update Political Opinion based on Discontent.
        Discontent = Survival Need / 100.0.
        Approval = 1 if Discontent < 0.4 else 0.
        """
        # Access owner needs (managed by BioComponent/Lifecycle or BaseAgent)
        survival_need = self.owner.needs.get("survival", 0.0)
        self.discontent = min(1.0, survival_need / 100.0)

        # Determine Approval (Tolerance = 0.4)
        if self.discontent < 0.4:
            self.approval_rating = 1
        else:
            self.approval_rating = 0

    def apply_leisure_effect(self, leisure_hours: float, consumed_items: Dict[str, float]) -> LeisureEffectDTO:
        return self.leisure.apply_leisure_effect(leisure_hours, consumed_items)
