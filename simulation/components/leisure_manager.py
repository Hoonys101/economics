from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Dict, Any, Optional
from simulation.dtos import LeisureEffectDTO

if TYPE_CHECKING:
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class LeisureManager:
    """
    Phase 22.5: Household Leisure Component
    Manages leisure activities (Self-Dev, Parenting, Entertainment).
    """

    def __init__(self, owner: "Household", config_module: Any):
        self.owner = owner
        self.config = config_module
        
        # State
        self.last_leisure_type = "SELF_DEV"

    def apply_leisure_effect(self, leisure_hours: float, consumed_items: Dict[str, float]) -> LeisureEffectDTO:
        """
        Calculates and applies effects of leisure based on time and consumption.
        """
        leisure_type = self._determine_leisure_type(consumed_items)
        self.last_leisure_type = leisure_type

        # Get coefficients
        coeffs = self.config.LEISURE_COEFFS.get(leisure_type, {})
        utility_per_hour = coeffs.get("utility_per_hour", 0.0)
        xp_gain_per_hour = coeffs.get("xp_gain_per_hour", 0.0)
        productivity_gain = coeffs.get("productivity_gain", 0.0)

        utility_gained = leisure_hours * utility_per_hour
        xp_gained = leisure_hours * xp_gain_per_hour
        prod_gained = leisure_hours * productivity_gain

        # Execute Effects
        if leisure_type == "SELF_DEV" and prod_gained > 0:
            self.owner.labor_skill += prod_gained
            logger.debug(
                f"LEISURE | {self.owner.id} (SELF_DEV) Labor Skill +{prod_gained:.4f}",
                extra={"agent_id": self.owner.id, "tags": ["leisure"]}
            )
        elif leisure_type == "ENTERTAINMENT":
             # Utility is applied via needs reduction usually or logged
             pass

        return LeisureEffectDTO(
            leisure_type=leisure_type,
            leisure_hours=leisure_hours,
            utility_gained=utility_gained,
            xp_gained=xp_gained
        )

    def _determine_leisure_type(self, consumed_items: Dict[str, float]) -> str:
        """Helper to classify leisure based on context."""
        has_children = len(self.owner.children_ids) > 0
        has_education = consumed_items.get("education_service", 0.0) > 0
        has_luxury = (
            consumed_items.get("luxury_food", 0.0) > 0 or
            consumed_items.get("clothing", 0.0) > 0
        )

        if has_children and has_education:
            return "PARENTING"
        elif has_luxury:
            return "ENTERTAINMENT"
        else:
            return "SELF_DEV"
