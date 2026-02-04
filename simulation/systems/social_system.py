"""
Implements the SocialSystem which handles social rank updates and reference standard calculation.
"""
from typing import Dict, Any, List
from simulation.systems.api import ISocialSystem, SocialMobilityContext

class SocialSystem(ISocialSystem):
    """
    Manages social mobility, rank calculation, and reference standards for the simulation.
    """

    def __init__(self, config: Any):
        self.config = config

    def _get_housing_tier(self, agent: Any) -> float:
        """Helper to estimate housing tier based on residence."""
        if hasattr(agent, "residing_property_id") and agent.residing_property_id is not None:
            return 1.0
        if hasattr(agent, "_econ_state") and agent._econ_state.residing_property_id is not None:
            return 1.0
        return 0.0

    def update_social_ranks(self, context: SocialMobilityContext) -> None:
        """
        Calculates and updates the social rank (percentile) for all active households.
        The score is a weighted sum of consumption and housing tier.
        """
        households = context["households"]
        scores = []

        for h in households:
            if not h.is_active: continue

            # Calculate Score
            consumption_score = h._econ_state.current_consumption * 10.0
            housing_tier = self._get_housing_tier(h)
            housing_score = housing_tier * 1000.0

            total_score = consumption_score + housing_score
            scores.append((h, total_score))

        # Sort and Assign Rank
        # Higher score = Better rank (Higher Percentile)
        scores.sort(key=lambda x: x[1], reverse=True)

        n = len(scores)
        if n == 0: return

        for rank_idx, (agent, _) in enumerate(scores):
            # Rank 0 (Top) -> Percentile 1.0
            # Rank N-1 (Bottom) -> Percentile 0.0
            percentile = 1.0 - (rank_idx / n)
            agent.social_rank = percentile

    def calculate_reference_standard(self, context: SocialMobilityContext) -> Dict[str, float]:
        """
        Calculates the average consumption and housing tier of the top 20% households.
        """
        households = context["households"]
        active_households = [h for h in households if h.is_active]

        if not active_households:
            return {"avg_consumption": 0.0, "avg_housing_tier": 0.0}

        # Sort by social rank
        sorted_hh = sorted(active_households, key=lambda h: getattr(h, "social_rank", 0.0), reverse=True)

        top_20_count = max(1, int(len(active_households) * 0.20))
        top_20 = sorted_hh[:top_20_count]

        avg_cons = sum(h._econ_state.current_consumption for h in top_20) / len(top_20)
        avg_tier = sum(self._get_housing_tier(h) for h in top_20) / len(top_20)

        return {
            "avg_consumption": avg_cons,
            "avg_housing_tier": avg_tier
        }
