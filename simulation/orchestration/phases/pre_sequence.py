from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState, GovernmentSensoryDTO
from modules.government.dtos import MacroEconomicSnapshotDTO
from simulation.systems.api import (
    EventContext, SocialMobilityContext, SensoryContext
)
from modules.government.components.monetary_policy_manager import MonetaryPolicyManager
from simulation.orchestration.utils import prepare_market_data

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase0_PreSequence(IPhaseStrategy):
    def __init__(self, world_state: WorldState):
        self.world_state = world_state
        self.mp_manager = MonetaryPolicyManager(world_state.config_module)

    def execute(self, state: SimulationState) -> SimulationState:
        # WO-109: Pre-Sequence Stabilization
        if state.bank and hasattr(state.bank, "generate_solvency_transactions"):
            stabilization_txs = state.bank.generate_solvency_transactions(state.primary_government)
            if stabilization_txs:
                state.transactions.extend(stabilization_txs)
                state.logger.warning("STABILIZATION | Queued pre-sequence stabilization transactions.")

        # AI Training
        if state.ai_training_manager:
            if state.time > 0 and state.time % state.config_module.IMITATION_LEARNING_INTERVAL == 0:
                state.ai_training_manager.run_imitation_learning_cycle(state.time)

        # --- WO-060 / Phase 17 Logic (Social & Gov) ---

        # Update Stock Market Reference Prices
        if state.stock_market:
            active_firms = {f.id: f for f in state.firms if f.is_active}
            state.stock_market.update_reference_prices(active_firms)

        # Prepare Market Data (for Gov/Social)
        market_data = prepare_market_data(state)

        # Social Ranks
        if getattr(state.config_module, "ENABLE_VANITY_SYSTEM", False) and self.world_state.social_system:
            context: SocialMobilityContext = {
                "households": state.households
            }
            self.world_state.social_system.update_social_ranks(context)
            ref_std = self.world_state.social_system.calculate_reference_standard(context)
            market_data["reference_standard"] = ref_std

        # Government Public Opinion
        if state.primary_government:
            state.primary_government.update_public_opinion(state.households)

        # Sensory System
        sensory_context: SensoryContext = {
            "tracker": state.tracker,
            "government": state.primary_government,
            "time": state.time,
            "inequality_tracker": self.world_state.inequality_tracker,
            "households": state.households
        }

        sensory_dto = GovernmentSensoryDTO(state.time, 0, 0, 0, 0, 0, 0)
        if self.world_state.sensory_system:
            sensory_dto = self.world_state.sensory_system.generate_government_sensory_dto(sensory_context)
        else:
             state.logger.error("SensorySystem not initialized!")

        if state.primary_government:
            if state.injectable_sensory_dto and state.injectable_sensory_dto.tick == state.time:
                state.primary_government.update_sensory_data(state.injectable_sensory_dto)
                state.logger.warning(
                    f"INJECTED_SENSORY_DATA | Overrode sensory data for tick {state.time} with custom DTO.",
                    extra={"tick": state.time, "tags": ["test_injection"]}
                )
            else:
                state.primary_government.update_sensory_data(sensory_dto)

            # Government Policy Decision
            latest_gdp = state.tracker.get_latest_indicators().get("total_production", 0.0)
            market_data["total_production"] = latest_gdp
            state.primary_government.make_policy_decision(market_data, state.time, state.central_bank)

            state.primary_government.check_election(state.time)

        # WO-146: Monetary Policy Manager Integration
        # Ensure Central Bank updates its internal state (Potential GDP)
        if state.central_bank and hasattr(state.central_bank, "step"):
             state.central_bank.step(state.time)

        # Apply Monetary Policy periodically to ensure stability (WO-146 Insight)
        update_interval = getattr(state.config_module, "CB_UPDATE_INTERVAL", 10)

        if state.time > 0 and state.time % update_interval == 0:
            # Create MacroEconomicSnapshotDTO with macro indicators
            latest_indicators = state.tracker.get_latest_indicators()
            # Retrieve potential GDP from Central Bank if available
            potential_gdp = 0.0
            if state.central_bank and hasattr(state.central_bank, "potential_gdp"):
                 potential_gdp = state.central_bank.potential_gdp

            macro_snapshot = MacroEconomicSnapshotDTO(
                 inflation_rate=latest_indicators.get("inflation_rate", 0.0),
                 unemployment_rate=latest_indicators.get("unemployment_rate", 0.0),
                 nominal_gdp=latest_indicators.get("total_production", 0.0),
                 potential_gdp=potential_gdp
            )

            mp_policy = self.mp_manager.determine_monetary_stance(macro_snapshot)

            if state.central_bank:
                 state.central_bank.base_rate = mp_policy.target_interest_rate

            if state.bank and hasattr(state.bank, "update_base_rate"):
                 state.bank.update_base_rate(mp_policy.target_interest_rate)

        # Events (Moved to end to ensure shocks overwrite policy decisions)
        if self.world_state.event_system:
             context: EventContext = {
                 "households": state.households,
                 "firms": state.firms,
                 "markets": state.markets,
                 "government": state.primary_government,
                 "central_bank": state.central_bank,
                 "bank": state.bank
             }
             self.world_state.event_system.execute_scheduled_events(state.time, context, self.world_state.stress_scenario_config)

        return state
