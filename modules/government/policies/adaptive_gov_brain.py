from typing import List, Dict, Any, Optional
import logging
from simulation.ai.enums import PoliticalParty, PolicyActionTag
from modules.government.dtos import PolicyActionDTO
from simulation.dtos import GovernmentStateDTO as SensoryDTO

logger = logging.getLogger(__name__)

class AdaptiveGovBrain:
    """
    Utility-driven decision engine for the government (WO-057-A).
    Implements a Propose-Filter-Execute architecture using mental models
    to predict policy outcomes and maximize party-specific utility.
    """

    def __init__(self, config: Any):
        self.config = config

    def propose_actions(self, sensory_data: SensoryDTO, ruling_party: PoliticalParty) -> List[PolicyActionDTO]:
        """
        Generates a list of potential policy actions with predicted utilities.
        """
        candidates = self._generate_candidates()
        scored_actions = []

        current_utility = self._calculate_utility(sensory_data, ruling_party)

        for action in candidates:
            predicted_state = self._predict_outcome(sensory_data, action)
            predicted_utility = self._calculate_utility(predicted_state, ruling_party)

            # Score is the net utility gain (or raw utility?)
            # Usually we select max utility.
            action.utility = predicted_utility
            scored_actions.append(action)

        # Sort by utility descending
        scored_actions.sort(key=lambda x: x.utility, reverse=True)
        return scored_actions

    def _generate_candidates(self) -> List[PolicyActionDTO]:
        """
        Returns a list of all possible actions to evaluate.
        """
        # Define the action space
        # Note: Parameters are delta multipliers or absolute targets

        candidates = [
            # 1. Fiscal Expansion (Stimulus)
            PolicyActionDTO(
                name="Fiscal Stimulus (Welfare+)",
                utility=0.0,
                tag=PolicyActionTag.KEYNESIAN_FISCAL,
                action_type="ADJUST_WELFARE",
                params={"multiplier_delta": 0.1}
            ),
            PolicyActionDTO(
                name="Tax Cut (Corp)",
                utility=0.0,
                tag=PolicyActionTag.KEYNESIAN_FISCAL,
                action_type="ADJUST_CORP_TAX",
                params={"rate_delta": -0.02}
            ),
             PolicyActionDTO(
                name="Tax Cut (Income)",
                utility=0.0,
                tag=PolicyActionTag.KEYNESIAN_FISCAL,
                action_type="ADJUST_INCOME_TAX",
                params={"rate_delta": -0.02}
            ),

            # 2. Austerity (Contraction)
            PolicyActionDTO(
                name="Austerity (Welfare-)",
                utility=0.0,
                tag=PolicyActionTag.AUSTRIAN_AUSTERITY,
                action_type="ADJUST_WELFARE",
                params={"multiplier_delta": -0.1}
            ),
            PolicyActionDTO(
                name="Tax Hike (Corp)",
                utility=0.0,
                tag=PolicyActionTag.AUSTRIAN_AUSTERITY,
                action_type="ADJUST_CORP_TAX",
                params={"rate_delta": 0.02}
            ),
             PolicyActionDTO(
                name="Tax Hike (Income)",
                utility=0.0,
                tag=PolicyActionTag.AUSTRIAN_AUSTERITY,
                action_type="ADJUST_INCOME_TAX",
                params={"rate_delta": 0.02}
            ),

            # 3. Status Quo
            PolicyActionDTO(
                name="Maintain Course",
                utility=0.0,
                tag=PolicyActionTag.GENERAL_ADMIN,
                action_type="DO_NOTHING",
                params={}
            )
        ]
        return candidates

    def _predict_outcome(self, current: SensoryDTO, action: PolicyActionDTO) -> SensoryDTO:
        """
        Simple Heuristic Mental Model (WO-057-A).
        Predicts the *next* state based on the action.
        """
        # Clone current state (using simple copy or kwargs since it's frozen/dataclass)
        from dataclasses import replace
        next_state = replace(current)

        # Apply heuristics
        # These are rough estimates for decision making, not simulation truth.

        if action.action_type == "ADJUST_WELFARE":
            delta = action.params.get("multiplier_delta", 0.0)
            # Higher welfare -> Higher LowAssetApproval, Lower Gini (Improvement), Lower GDP (crowding out?)
            # +0.1 Multiplier => +0.05 Approval (Low), -0.01 Gini, -0.001 GDP Growth
            if delta > 0:
                next_state.approval_low_asset = min(1.0, current.approval_low_asset + 0.05)
                next_state.gini_index = max(0.0, current.gini_index - 0.01)
                next_state.gdp_growth_sma -= 0.001
            else:
                next_state.approval_low_asset = max(0.0, current.approval_low_asset - 0.05)
                next_state.gini_index = min(1.0, current.gini_index + 0.01)
                next_state.gdp_growth_sma += 0.001

        elif action.action_type == "ADJUST_CORP_TAX":
            delta = action.params.get("rate_delta", 0.0)
            # Lower Corp Tax -> Higher HighAssetApproval, Higher GDP Growth, Higher Gini (Worse)
            # -0.02 Rate => +0.04 Approval (High), +0.005 GDP Growth, +0.005 Gini
            if delta < 0: # Cut
                next_state.approval_high_asset = min(1.0, current.approval_high_asset + 0.04)
                next_state.gdp_growth_sma += 0.005
                next_state.gini_index = min(1.0, current.gini_index + 0.005)
            else: # Hike
                next_state.approval_high_asset = max(0.0, current.approval_high_asset - 0.04)
                next_state.gdp_growth_sma -= 0.005
                next_state.gini_index = max(0.0, current.gini_index - 0.005)

        elif action.action_type == "ADJUST_INCOME_TAX":
            delta = action.params.get("rate_delta", 0.0)
            # Lower Income Tax -> Higher Approval (General/Low), Higher GDP (Consumption), Higher Gini?
            # -0.02 Rate => +0.03 Approval (Low), +0.02 Approval (High), +0.002 GDP
            if delta < 0: # Cut
                next_state.approval_low_asset = min(1.0, current.approval_low_asset + 0.03)
                next_state.approval_high_asset = min(1.0, current.approval_high_asset + 0.02)
                next_state.gdp_growth_sma += 0.002
            else: # Hike
                next_state.approval_low_asset = max(0.0, current.approval_low_asset - 0.03)
                next_state.approval_high_asset = max(0.0, current.approval_high_asset - 0.02)
                next_state.gdp_growth_sma -= 0.002

        # DO_NOTHING assumes slight trend continuation or decay,
        # but for comparison we can keep it static or apply slight reversion.

        return next_state

    def _calculate_utility(self, state: SensoryDTO, party: PoliticalParty) -> float:
        """
        Party-specific Utility Function.
        """
        if party == PoliticalParty.RED:
            # RED Utility: U = 0.7 * LowAssetApproval + 0.3 * (1 - Gini)
            # Focus on Equality and Working Class
            u = 0.7 * state.approval_low_asset + 0.3 * (1.0 - state.gini_index)
            return u

        elif party == PoliticalParty.BLUE:
            # BLUE Utility: U = 0.6 * HighAssetApproval + 0.4 * GDPGrowth
            # Focus on Growth and Asset Holders
            # Note: GDP Growth is typically small (0.02).
            # We might want to scale it or just accept it's a small component relative to approval.
            # Using raw values as per spec.
            u = 0.6 * state.approval_high_asset + 0.4 * state.gdp_growth_sma
            return u

        return 0.0
