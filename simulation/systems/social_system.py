from __future__ import annotations
from typing import Dict, Any, List, Optional
from simulation.systems.api import ISocialSystem, SocialMobilityContext
from simulation.config import SimulationConfig

class SocialSystem(ISocialSystem):
    """사회적 순위 및 지위와 같은 동적 요소를 관리하는 시스템."""

    def __init__(self, config: SimulationConfig):
        self.config = config

    def update_social_ranks(self, context: SocialMobilityContext) -> None:
        """모든 가계의 사회적 순위 백분위를 계산하고 할당합니다."""
        households = context['households']
        housing_manager = context['housing_manager']

        scores = []
        for h in households:
            if not h.is_active: continue

            consumption_score = h.current_consumption * 10.0 # Weight consumption
            housing_tier = housing_manager.get_housing_tier(h)
            housing_score = housing_tier * 1000.0 # Tier 1=1000, Tier 3=3000

            total_score = consumption_score + housing_score
            scores.append((h.id, total_score))

        # Sort and Assign Rank
        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
        n = len(sorted_scores)
        if n == 0: return

        # Map household IDs to agents for rank update
        # Since we have the household objects in the context, we can update them directly
        # But wait, the original code used self.agents.get(hid)
        # context['households'] is List['Household']. We can create a map.

        household_map = {h.id: h for h in households}

        for rank_idx, (hid, _) in enumerate(sorted_scores):
            # Rank 0 (Top) -> Percentile 1.0
            # Rank N-1 (Bottom) -> Percentile 0.0
            percentile = 1.0 - (rank_idx / n)
            agent = household_map.get(hid)
            if agent:
                agent.social_rank = percentile

    def calculate_reference_standard(self, context: SocialMobilityContext) -> Dict[str, float]:
        """최상위 사회 계층의 평균 소비 및 주거 수준을 계산합니다."""
        households = context['households']
        housing_manager = context['housing_manager']

        active_households = [h for h in households if h.is_active]
        if not active_households:
            return {"avg_consumption": 0.0, "avg_housing_tier": 0.0}

        top_20_count = max(1, int(len(active_households) * 0.20))
        sorted_hh = sorted(active_households, key=lambda h: getattr(h, "social_rank", 0.0), reverse=True)
        top_20 = sorted_hh[:top_20_count]

        avg_cons = sum(h.current_consumption for h in top_20) / len(top_20)
        avg_tier = sum(housing_manager.get_housing_tier(h) for h in top_20) / len(top_20)

        return {
            "avg_consumption": avg_cons,
            "avg_housing_tier": avg_tier
        }
