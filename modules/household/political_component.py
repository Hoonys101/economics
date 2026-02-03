import logging
import random
from typing import Dict, Any, Optional
from simulation.ai.enums import Personality, PoliticalParty, PoliticalVision

logger = logging.getLogger(__name__)

class PoliticalComponent:
    """
    Household's political soul.
    Calculates approval and trust based on internal vision and external reality.
    
    Vision: 0.0 (Safety/Equity) to 1.0 (Growth/Ladder)
    """

    def __init__(self, personality: Personality):
        self._economic_vision: float = self._derive_vision(personality)
        self._trust_score: float = 0.5
        self._current_approval: float = 0.5
        
        # Determine discretized vision for convenience
        self._vision_enum: PoliticalVision = (
            PoliticalVision.GROWTH if self._economic_vision > 0.5 
            else PoliticalVision.SAFETY
        )

    def _derive_vision(self, personality: Personality) -> float:
        """Derives economic vision from personality with some noise."""
        vision_map = {
            Personality.GROWTH_ORIENTED: 0.9,
            Personality.STATUS_SEEKER: 0.8,
            Personality.MISER: 0.4, # Misers often prefer conservative stability but might shift
            Personality.CONSERVATIVE: 0.3, # Personality 'Conservative' usually favors stability/status-quo
            Personality.IMPULSIVE: 0.5
        }
        base = vision_map.get(personality, 0.5)
        # Add noise to ensure diversity within cohorts (Emergence)
        return max(0.0, min(1.0, base + random.uniform(-0.15, 0.15)))

    @property
    def economic_vision(self) -> float:
        return self._economic_vision

    @property
    def trust_score(self) -> float:
        return self._trust_score

    @property
    def vision_enum(self) -> PoliticalVision:
        return self._vision_enum

    def calculate_approval(
        self, 
        survival_satisfaction: float, 
        gov_party: PoliticalParty,
        gov_stance: float
    ) -> float:
        """
        [ADR-2] The Happiness Index & Ideological Match.
        
        Approval = (0.4 * Economic Reality) + (0.6 * Ideological Match)
        Modified by Trust.
        """
        # 1. Economic Reality (0.0 - 1.0)
        # Assuming survival_satisfaction is already normalized
        economic_reality = max(0.0, min(1.0, survival_satisfaction))

        # 2. Ideological Distance (0.0 - 1.0)
        # Distance = |My Vision - Gov Stance|
        # Match = 1.0 - Distance
        ideological_match = 1.0 - abs(self._economic_vision - gov_stance)

        # 3. Base Approval
        base_approval = (0.4 * economic_reality) + (0.6 * ideological_match)

        # 4. Trust Damper
        # If trust is extremely low, approval is cratered regardless of match
        if self._trust_score < 0.2:
            base_approval *= (self._trust_score / 0.2)
            
        self._current_approval = max(0.0, min(1.0, base_approval))
        return self._current_approval

    def update_trust(self, economic_satisfaction: float):
        """
        Updates trust based on economic outcomes. 
        Uses an EMA to reflect 'Memory' but slow adaptation.
        """
        alpha = 0.05 # Trust changes slowly
        self._trust_score = (1 - alpha) * self._trust_score + alpha * economic_satisfaction
        self._trust_score = max(0.0, min(1.0, self._trust_score))

    def get_state_dict(self) -> Dict[str, Any]:
        return {
            "economic_vision": self._economic_vision,
            "vision_enum": self._vision_enum.name,
            "trust_score": self._trust_score,
            "approval": self._current_approval
        }
