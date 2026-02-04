import logging
import random
from typing import Tuple
from modules.household.dtos import SocialStateDTO
from simulation.ai.enums import Personality, PoliticalParty, PoliticalVision

logger = logging.getLogger(__name__)

class PoliticalComponent:
    """
    Household's political soul.
    Stateless component that operates on SocialStateDTO.
    """

    def initialize_state(self, personality: Personality) -> Tuple[float, float]:
        """
        Derives initial economic vision and trust score from personality.
        Returns: (economic_vision, trust_score)
        """
        vision_map = {
            Personality.GROWTH_ORIENTED: 0.9,
            Personality.STATUS_SEEKER: 0.8,
            Personality.MISER: 0.4,
            Personality.CONSERVATIVE: 0.3,
            Personality.IMPULSIVE: 0.5
        }
        base = vision_map.get(personality, 0.5)
        # Add noise to ensure diversity within cohorts (Emergence)
        economic_vision = max(0.0, min(1.0, base + random.uniform(-0.15, 0.15)))
        trust_score = 0.5
        return economic_vision, trust_score

    def update_opinion(
        self,
        state: SocialStateDTO,
        survival_need: float,
        gov_party: PoliticalParty
    ) -> SocialStateDTO:
        """
        Updates political approval based on satisfaction and ideological match.
        """
        new_state = state.copy()

        # 1. Derive Gov Stance from Party
        # BLUE (Growth) -> 0.9, RED (Safety) -> 0.1
        gov_stance = 0.9 if gov_party == PoliticalParty.BLUE else 0.1

        # 2. Calculate Satisfaction
        # High survival need = Low satisfaction
        # Assuming survival_need is 0-100 scale where 100 is max need (bad)
        discontent = min(1.0, survival_need / 100.0)
        satisfaction = 1.0 - discontent
        new_state.discontent = discontent

        # 3. Calculate Ideological Match
        # Distance = |My Vision - Gov Stance|
        ideological_match = 1.0 - abs(new_state.economic_vision - gov_stance)

        # 4. Update Trust (EMA)
        # Trust grows with satisfaction, decays with dissatisfaction
        # Using slow adaptation (alpha=0.05)
        new_trust = 0.95 * new_state.trust_score + 0.05 * satisfaction
        new_state.trust_score = max(0.0, min(1.0, new_trust))

        # 5. Calculate Approval
        # Approval = 0.4 * Satisfaction + 0.6 * Match
        approval_score = (0.4 * satisfaction) + (0.6 * ideological_match)

        # 6. Trust Damper
        if new_state.trust_score < 0.2:
            approval_score = 0.0

        # 7. Update Binary Approval Rating
        # Threshold 0.5
        new_state.approval_rating = 1 if approval_score > 0.5 else 0

        return new_state
