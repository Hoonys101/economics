from __future__ import annotations
import dataclasses
import logging
from typing import Any, List, Optional, TYPE_CHECKING
from modules.common.config.api import IConfigManager, GovernmentConfigDTO
from simulation.ai.enums import PoliticalParty
from modules.government.political.orchestrator import PoliticalOrchestrator
from modules.government.political.api import IVoter, ILobbyist

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

class PoliticsSystem:
    """
    The Politics System acts as the Political Orchestrator.
    It manages public opinion, elections, and translates political mandates into government policy.
    Refactored to delegate aggregation to PoliticalOrchestrator.
    """

    def __init__(self, config_manager: IConfigManager):
        self._config_manager = config_manager
        self.election_cycle = 100 # Default, could be configurable
        self.last_election_tick = 0
        self.perceived_public_opinion = 0.5
        self.approval_history: List[float] = []

        # New Orchestrator
        self.orchestrator = PoliticalOrchestrator()

    def process_tick(self, state: SimulationState) -> None:
        """
        Main orchestration method called by Phase_Politics.
        """
        # 1. Collect Votes & Lobbying (Batch Scanner)
        self._collect_signals(state)

        # 2. Update Political Climate
        climate = self.orchestrator.calculate_political_climate(state.time)

        # 3. Sync to Government
        if state.primary_government:
            self._sync_climate_to_government(state.primary_government, climate)

        # 4. Check for Election
        if state.time > 0 and state.time % self.election_cycle == 0:
            self._conduct_election(state, climate)

        # 5. Reset Cycle
        self.orchestrator.reset_cycle()

        # 6. Enact Policy (Continuous adjustment or Mandate enforcement)
        if state.primary_government:
            # Ensure total_production is fresh
            latest_gdp = state.tracker.get_latest_indicators().get("total_production", 0.0)
            if state.market_data:
                state.market_data["total_production"] = latest_gdp

            # Delegate strictly policy decision logic to the government agent
            state.primary_government.make_policy_decision(
                state.market_data or {},
                state.time,
                state.central_bank
            )

    def _collect_signals(self, state: SimulationState) -> None:
        """
        Iterates over agents to collect votes and lobbying efforts.
        Acts as the 'Batch Scanner' adapter.
        """
        # Collect Votes
        for h in state.households:
            # Check if implements IVoter
            if isinstance(h, IVoter):
                 try:
                     vote = h.cast_vote(state.time, state.primary_government) # Passing gov as state for now
                     self.orchestrator.register_vote(vote)
                 except Exception as e:
                     logger.warning(f"Failed to cast vote for household {h.id}: {e}")

        # Collect Lobbying
        for f in state.firms:
            if isinstance(f, ILobbyist):
                try:
                    result = f.formulate_lobbying_effort(state.time, state.primary_government)
                    if result:
                        effort, payment_request = result

                        # Execute Payment
                        if state.settlement_system:
                            success = state.settlement_system.transfer(
                                payment_request.payer,
                                payment_request.payee,
                                payment_request.amount,
                                payment_request.memo,
                                payment_request.currency
                            )

                            if success:
                                self.orchestrator.register_lobbying(effort)
                                logger.info(f"LOBBYING_SUCCESS | Firm {f.id} spent {payment_request.amount} to influence {effort.target_policy}")
                            else:
                                logger.debug(f"LOBBYING_FAILED | Firm {f.id} failed payment.")
                except Exception as e:
                    logger.warning(f"Failed to process lobbying for firm {f.id}: {e}")

    def _sync_climate_to_government(self, government: Any, climate: Any) -> None:
        government.approval_rating = climate.overall_approval_rating
        if hasattr(government, 'perceived_public_opinion'):
            government.perceived_public_opinion = climate.overall_approval_rating

        # Log Top Grievances for debugging
        if climate.top_grievances:
             logger.debug(f"POLITICAL_CLIMATE | Approval: {climate.overall_approval_rating:.2f} | Grievances: {climate.top_grievances}")

    def _conduct_election(self, state: SimulationState, climate: Any) -> None:
        if not state.primary_government:
            return

        self.last_election_tick = state.time

        # Election Logic using Climate Data
        # If approval > 0.5, Incumbent wins. Else Challenger wins.
        # This is a simplification of the "Clash of Mandates"

        incumbent_party = state.primary_government.ruling_party

        # Logic: If Approval > 0.5, Incumbent keeps power.
        # If Approval < 0.5, they lose to the OPPOSITE party.

        winner = incumbent_party
        if climate.overall_approval_rating < 0.5:
             winner = PoliticalParty.RED if incumbent_party == PoliticalParty.BLUE else PoliticalParty.BLUE

        if winner != incumbent_party:
            state.primary_government.ruling_party = winner
            logger.warning(
                f"ELECTION_RESULTS | REGIME CHANGE! {incumbent_party.name} -> {winner.name}. Approval: {climate.overall_approval_rating:.2f}",
                extra={"tick": state.time, "agent_id": state.primary_government.id, "tags": ["election", "regime_change"]}
            )
            # Trigger Policy Mandate
            self._apply_policy_mandate(state.primary_government, winner)
        else:
            logger.info(
                f"ELECTION_RESULTS | INCUMBENT VICTORY ({winner.name}). Approval: {climate.overall_approval_rating:.2f}",
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
