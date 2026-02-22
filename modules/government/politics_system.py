from __future__ import annotations
import dataclasses
import logging
from typing import Any, List, Optional, TYPE_CHECKING
from modules.common.config.api import IConfigManager, GovernmentConfigDTO
from simulation.ai.enums import PoliticalParty

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class PoliticsSystem:
    """
    The Politics System acts as the Political Orchestrator.
    It manages public opinion, elections, and translates political mandates into government policy.
    Replaces legacy check_election and update_public_opinion logic in Government agent.
    """

    def __init__(self, config_manager: IConfigManager):
        self._config_manager = config_manager
        self.election_cycle = 100 # Default, could be configurable
        self.last_election_tick = 0
        self.perceived_public_opinion = 0.5
        self.approval_history: List[float] = []

    def process_tick(self, state: SimulationState) -> None:
        """
        Main orchestration method called by Phase_Politics.
        """
        # 1. Update Public Opinion (Approval Rating)
        self._update_public_opinion(state)

        # 2. Check for Election
        if state.time > 0 and state.time % self.election_cycle == 0:
            self._conduct_election(state)

        # 3. Enact Policy (Continuous adjustment or Mandate enforcement)
        # Note: Government agent has 'make_policy_decision' which uses FiscalEngine.
        # PoliticsSystem updates the CONFIG or STATE constraints that FiscalEngine uses.
        # But 'make_policy_decision' is also called here to execute the decision for the tick.
        if state.primary_government:
            # We construct market_data if needed, but Phase_Politics might have done it?
            # Phase0_PreSequence used to call 'prepare_market_data'.
            # Phase_Politics executes after Phase_SystemicLiquidation.
            # Usually market_data is already in state.market_data from Phase1_Decision.

            # Ensure total_production is fresh (as per Phase0 logic)
            latest_gdp = state.tracker.get_latest_indicators().get("total_production", 0.0)
            if state.market_data:
                state.market_data["total_production"] = latest_gdp

            # Delegate strictly policy decision logic to the government agent
            state.primary_government.make_policy_decision(
                state.market_data or {},
                state.time,
                state.central_bank
            )

    def _update_public_opinion(self, state: SimulationState) -> None:
        if not state.primary_government:
            return

        total_approval = 0
        count = 0
        for h in state.households:
            # Check if active
            is_active = h._bio_state.is_active if hasattr(h, '_bio_state') else getattr(h, 'is_active', False)
            if is_active:
                # Access social state safely
                social_state = getattr(h, '_social_state', None)
                if social_state:
                    rating = getattr(social_state, 'approval_rating', 0)
                    total_approval += rating
                    count += 1

        avg_approval = total_approval / count if count > 0 else 0.5

        # Update internal state
        self.perceived_public_opinion = avg_approval
        self.approval_history.append(avg_approval)
        if len(self.approval_history) > 10:
            self.approval_history.pop(0)

        # Sync to Government Agent
        state.primary_government.approval_rating = avg_approval
        # Also update perceived opinion on gov if it has the attribute
        if hasattr(state.primary_government, 'perceived_public_opinion'):
            state.primary_government.perceived_public_opinion = avg_approval

    def _conduct_election(self, state: SimulationState) -> None:
        if not state.primary_government:
            return

        self.last_election_tick = state.time

        # Simple Vote Counting: Economic Vision
        # < 0.5 -> Safety (RED)
        # >= 0.5 -> Growth (BLUE)

        votes_blue = 0
        votes_red = 0

        for h in state.households:
            is_active = h._bio_state.is_active if hasattr(h, '_bio_state') else getattr(h, 'is_active', False)
            if is_active:
                social_state = getattr(h, '_social_state', None)
                if social_state:
                    vision = getattr(social_state, 'economic_vision', 0.5)
                    if vision >= 0.5:
                        votes_blue += 1
                    else:
                        votes_red += 1

        winner = PoliticalParty.BLUE if votes_blue >= votes_red else PoliticalParty.RED

        current_party = state.primary_government.ruling_party

        if winner != current_party:
            state.primary_government.ruling_party = winner
            logger.warning(
                f"ELECTION_RESULTS | REGIME CHANGE! {current_party.name} -> {winner.name}. Votes: Blue={votes_blue}, Red={votes_red}",
                extra={"tick": state.time, "agent_id": state.primary_government.id, "tags": ["election", "regime_change"]}
            )
            # Trigger Policy Mandate
            self._apply_policy_mandate(state.primary_government, winner)
        else:
            logger.info(
                f"ELECTION_RESULTS | INCUMBENT VICTORY ({winner.name}). Votes: Blue={votes_blue}, Red={votes_red}",
                extra={"tick": state.time, "agent_id": state.primary_government.id, "tags": ["election"]}
            )

    def _apply_policy_mandate(self, government: Any, party: PoliticalParty) -> None:
        """
        Applies the winning party's platform to the government configuration.
        """
        # Blue: Low Corp Tax, Low Income Tax (Supply Side)
        # Red: High Corp Tax, Progressive Income Tax (Demand Side / Welfare)

        # We update the Government object directly for immediate effect,
        # AND update the Config via ConfigManager for persistence/consistency.

        new_income_tax = 0.1
        new_corp_tax = 0.2

        if party == PoliticalParty.BLUE:
            new_income_tax = 0.15 # Moderate
            new_corp_tax = 0.15   # Low
        elif party == PoliticalParty.RED:
            new_income_tax = 0.25 # High
            new_corp_tax = 0.30   # High

        # Update Government Agent State
        government.income_tax_rate = new_income_tax
        government.corporate_tax_rate = new_corp_tax

        # Update Config
        try:
            current_config = self._config_manager.get_config("government", GovernmentConfigDTO)
            new_config = dataclasses.replace(
                current_config,
                income_tax_rate=new_income_tax,
                corporate_tax_rate=new_corp_tax
            )
            self._config_manager.update_config("government", new_config)
            logger.info(f"POLICY_MANDATE | Applied {party.name} platform. IncomeTax: {new_income_tax}, CorpTax: {new_corp_tax}")
        except Exception as e:
            logger.error(f"Failed to update government config during mandate application: {e}")

    # Legacy method kept for backward compatibility (if tests use it)
    def enact_new_tax_policy(self, simulation_state: Any) -> None:
        """Deprecated: Logic moved to process_tick and _apply_policy_mandate."""
        pass
