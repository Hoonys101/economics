"""
Implements the SocialSystem which handles social rank updates and reference standard calculation.
"""
from typing import Dict, Any, List
from simulation.systems.api import ISocialSystem, SocialMobilityContext
from simulation.decisions.housing_manager import HousingManager

class SocialSystem(ISocialSystem):
    """
    Manages social mobility, rank calculation, and reference standards for the simulation.
    """

    def __init__(self, config: Any):
        self.config = config

    def update_social_ranks(self, context: SocialMobilityContext) -> None:
        """
        Calculates and updates the social rank (percentile) for all active households.
        The score is a weighted sum of consumption and housing tier.
        """
        households = context["households"]
        # HousingManager might be passed in context or instantiated here.
        # The spec says context has 'housing_manager', but the old code instantiated it.
        # Let's instantiate it if not provided to be safe, or use what's provided.
        # For simplicity and to match legacy logic, we instantiate a helper.
        # But `HousingManager` needs an agent.

        scores = []

        # We need a helper for housing tier. The HousingManager takes (agent, config).
        # We will reuse it per agent or just create one temporary instance if stateless?
        # HousingManager.get_housing_tier(agent) uses agent attributes.
        # So we can just instantiate it once with None agent if the method accepts agent.
        # Checking HousingManager code... `get_housing_tier` takes `agent`.
        # The `__init__` takes `agent`, but `get_housing_tier` also takes `agent` as argument.
        # This seems redundant or one is ignored.
        # Looking at `simulation/decisions/housing_manager.py`:
        # class HousingManager: def __init__(self, agent: Any, config: Any): self.agent = agent ...
        # def get_housing_tier(self, agent: Any) -> float: ...
        # It seems it can be used statelessly if we pass agent to get_housing_tier.

        hm = context.get("housing_manager")
        if not hm:
             hm = HousingManager(None, self.config)

        for h in households:
            if not h._bio_state.is_active: continue

            # Calculate Score
            consumption_score = h._econ_state.current_consumption * 10.0
            housing_tier = hm.get_housing_tier(h)
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
        active_households = [h for h in households if h._bio_state.is_active]

        if not active_households:
            return {"avg_consumption": 0.0, "avg_housing_tier": 0.0}

        # Sort by social rank
        sorted_hh = sorted(active_households, key=lambda h: getattr(h, "social_rank", 0.0), reverse=True)

        top_20_count = max(1, int(len(active_households) * 0.20))
        top_20 = sorted_hh[:top_20_count]

        hm = context.get("housing_manager")
        if not hm:
             hm = HousingManager(None, self.config)

        avg_cons = sum(h._econ_state.current_consumption for h in top_20) / len(top_20)
        avg_tier = sum(hm.get_housing_tier(h) for h in top_20) / len(top_20)

        return {
            "avg_consumption": avg_cons,
            "avg_housing_tier": avg_tier
        }
