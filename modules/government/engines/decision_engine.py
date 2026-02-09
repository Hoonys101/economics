from typing import Any, Dict, Optional, List
import logging
from modules.government.api import IGovernmentDecisionEngine
from modules.government.dtos import GovernmentStateDTO, PolicyDecisionDTO, PolicyActionDTO
from simulation.dtos.api import MarketSnapshotDTO
from simulation.ai.enums import PolicyActionTag, EconomicSchool, PoliticalParty
from modules.government.policies.adaptive_gov_brain import AdaptiveGovBrain

logger = logging.getLogger(__name__)

class GovernmentDecisionEngine(IGovernmentDecisionEngine):
    """
    Stateless engine that decides on government policy actions.
    It delegates the specific logic to a strategy (e.g., Taylor Rule, AI).
    """

    def __init__(self, config_module: Any, strategy_mode: str = "TAYLOR_RULE"):
        self.config = config_module
        self.strategy_mode = strategy_mode
        self.brain = AdaptiveGovBrain(config_module)

    def decide(
        self,
        state: GovernmentStateDTO,
        market_snapshot: MarketSnapshotDTO,
        central_bank: Any
    ) -> PolicyDecisionDTO:
        """
        Decides on a policy action based on current state and market data.
        """
        # Calculate Potential GDP (Common Logic for all strategies)
        current_gdp = market_snapshot.market_data.get("total_production", 0.0)
        if current_gdp == 0.0 and state.sensory_data:
             current_gdp = state.sensory_data.current_gdp

        potential_gdp = state.potential_gdp
        if potential_gdp == 0.0:
            potential_gdp = current_gdp
        else:
            alpha = 0.01
            potential_gdp = (alpha * current_gdp) + ((1-alpha) * potential_gdp)

        if self.strategy_mode == "AI_ADAPTIVE":
             if not state.sensory_data:
                 return PolicyDecisionDTO(action_tag=PolicyActionTag.GENERAL_ADMIN, status="NO_SENSORY_DATA", parameters={})

             # Use AdaptiveGovBrain
             # Ensure ruling_party is a PoliticalParty enum member
             party = state.ruling_party
             if isinstance(party, str):
                 try:
                     party = PoliticalParty[party]
                 except KeyError:
                     party = PoliticalParty.BLUE # Default fallback

             proposed = self.brain.propose_actions(state.sensory_data, party)

             # Filter Lockouts
             valid = []
             for action in proposed:
                 lock_until = state.policy_lockouts.get(action.tag, 0)
                 if state.tick >= lock_until:
                     valid.append(action)

             if not valid:
                 return PolicyDecisionDTO(action_tag=PolicyActionTag.GENERAL_ADMIN, status="NO_VALID_ACTIONS", parameters={})

             best = valid[0]
             # Inject potential_gdp into result parameters so it updates state
             params = best.params.copy()
             params["potential_gdp"] = potential_gdp

             return PolicyDecisionDTO(
                 action_tag=best.tag,
                 parameters=params,
                 metadata={"action_type": best.action_type, "utility": best.utility, "name": best.name},
                 status="EXECUTED"
             )

        else: # TAYLOR_RULE or default
            return self._decide_taylor_rule(state, market_snapshot, central_bank, potential_gdp, current_gdp)

    def _decide_taylor_rule(self, state: GovernmentStateDTO, market_snapshot: MarketSnapshotDTO, central_bank: Any, potential_gdp: float, current_gdp: float) -> PolicyDecisionDTO:
        """
        Implements Taylor Rule-based fiscal policy logic.
        """
        gdp_gap = 0.0
        if potential_gdp > 0:
            gdp_gap = (current_gdp - potential_gdp) / potential_gdp

        # Counter-Cyclical Logic
        auto_cyclical = getattr(self.config, "AUTO_COUNTER_CYCLICAL_ENABLED", False)

        new_income_tax_rate = state.income_tax_rate
        action_tag = PolicyActionTag.GENERAL_ADMIN
        fiscal_stance = 0.0

        if auto_cyclical:
            sensitivity = getattr(self.config, "FISCAL_SENSITIVITY_ALPHA", 0.5)
            base_tax_rate = getattr(self.config, "INCOME_TAX_RATE", 0.1)

            fiscal_stance = -sensitivity * gdp_gap
            new_tax_rate = base_tax_rate * (1 - fiscal_stance)
            new_income_tax_rate = new_tax_rate

            if fiscal_stance > 0:
                action_tag = PolicyActionTag.KEYNESIAN_FISCAL
            elif fiscal_stance < 0:
                action_tag = PolicyActionTag.AUSTRIAN_AUSTERITY

        return PolicyDecisionDTO(
            action_tag=action_tag,
            parameters={
                "income_tax_rate": new_income_tax_rate,
                "potential_gdp": potential_gdp,
                "fiscal_stance": fiscal_stance
            },
            metadata={
                "strategy": "TAYLOR_RULE",
                "fiscal_stance": fiscal_stance
            },
            status="EXECUTED"
        )
