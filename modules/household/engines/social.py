from __future__ import annotations
from typing import List, Dict, Any, Optional
import random
import logging

from modules.household.api import ISocialEngine, SocialInputDTO, SocialOutputDTO
from modules.household.dtos import SocialStateDTO
from simulation.ai.enums import Personality, PoliticalParty
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class SocialEngine(ISocialEngine):
    """
    Stateless engine managing social status, political opinion, and other social metrics.
    Logic migrated from SocialComponent/PoliticalComponent.
    """

    def update_status(self, input_dto: SocialInputDTO) -> SocialOutputDTO:
        social_state = input_dto.social_state
        econ_state = input_dto.econ_state
        bio_state = input_dto.bio_state
        config = input_dto.config
        all_items = input_dto.all_items
        market_data = input_dto.market_data

        new_social_state = social_state.copy()

        # 1. Calculate Social Status (SocialComponent.calculate_social_status)
        total_assets_val = econ_state.wallet.get_balance(DEFAULT_CURRENCY)

        # Assumption: Luxury value is sum of inventory quantities (simplified legacy logic)
        luxury_goods_value = sum(all_items.values())

        asset_weight = config.social_status_asset_weight
        luxury_weight = config.social_status_luxury_weight

        new_social_state.social_status = (
            total_assets_val * asset_weight
        ) + (luxury_goods_value * luxury_weight)

        # 2. Update Political Opinion (PoliticalComponent.update_opinion)
        if market_data:
            gov_data = market_data.get("government")
            gov_party = None
            if gov_data:
                # Assuming gov_data is dict or object
                if isinstance(gov_data, dict):
                    party_obj = gov_data.get("party")
                    if party_obj:
                        if isinstance(party_obj, PoliticalParty):
                            gov_party = party_obj
                        elif isinstance(party_obj, str):
                            # Convert string to Enum
                            try:
                                party_str = party_obj
                                if "." in party_str:
                                    party_name = party_str.split(".")[-1]
                                    gov_party = PoliticalParty[party_name]
                                else:
                                    gov_party = PoliticalParty[party_str.upper()]
                            except KeyError:
                                # Fallback or specific mapping
                                pass
                elif hasattr(gov_data, "party"):
                     gov_party = gov_data.party

            if gov_party:
                survival_need = bio_state.needs.get("survival", 0.0)
                new_social_state = self._update_political_opinion(
                    new_social_state, survival_need, gov_party
                )

        return SocialOutputDTO(
            social_state=new_social_state
        )

    def _update_political_opinion(
        self,
        state: SocialStateDTO,
        survival_need: float,
        gov_party: PoliticalParty
    ) -> SocialStateDTO:
        """
        Updates political approval based on satisfaction and ideological match.
        """
        new_state = state.copy() # redundant since caller copied, but safe

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
