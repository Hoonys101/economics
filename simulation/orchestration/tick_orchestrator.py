from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING, Any, Dict
import logging

from simulation.dtos.api import SimulationState, GovernmentStateDTO
from simulation.orchestration.phases import (
    Phase0_PreSequence, Phase_Production, Phase1_Decision, Phase2_Matching,
    Phase3_Transaction, Phase4_Lifecycle, Phase5_PostSequence,
    prepare_market_data
)

if TYPE_CHECKING:
    from simulation.world_state import WorldState
    from simulation.action_processor import ActionProcessor
    from simulation.orchestration.api import IPhaseStrategy

logger = logging.getLogger(__name__)

class TickOrchestrator:
    def __init__(self, world_state: WorldState, action_processor: ActionProcessor):
        self.world_state = world_state
        self.action_processor = action_processor

        # Initialize phases with dependencies
        self.phases: List[IPhaseStrategy] = [
            Phase0_PreSequence(world_state),
            Phase_Production(world_state),
            Phase1_Decision(world_state),
            Phase2_Matching(world_state),
            Phase3_Transaction(world_state, action_processor),
            Phase4_Lifecycle(world_state),
            Phase5_PostSequence(world_state)
        ]

    def run_tick(self, injectable_sensory_dto: Optional[GovernmentStateDTO] = None) -> None:
        state = self.world_state

        # Money Supply Verification (Tick 0)
        # This check is usually done before any activity starts
        if state.time == 0:
            state.baseline_money_supply = state.calculate_total_money()
            state.logger.info(
                f"MONEY_SUPPLY_BASELINE | Baseline Money Supply set to: {state.baseline_money_supply:.2f}",
                extra={"tick": state.time, "money_supply": state.baseline_money_supply}
            )

        # Increment time
        state.time += 1
        state.logger.info(
            f"--- Starting Tick {state.time} ---",
            extra={"tick": state.time, "tags": ["tick_start"]},
        )

        # 1. Create the comprehensive state DTO for this tick
        sim_state = self._create_simulation_state_dto(injectable_sensory_dto)

        # 2. Execute all phases in sequence
        for phase in self.phases:
            sim_state = phase.execute(sim_state)

        # 3. Post-execution state synchronization
        self._synchronize_world_state(sim_state)

        # 4. Final persistence and cleanup
        self._finalize_tick(sim_state)

        state.logger.info(
            f"--- Ending Tick {state.time} ---",
            extra={"tick": state.time, "tags": ["tick_end"]},
        )

    def _create_simulation_state_dto(self, injectable_sensory_dto: Optional[GovernmentStateDTO]) -> SimulationState:
        state = self.world_state

        return SimulationState(
            time=state.time,
            households=state.households,
            firms=state.firms,
            agents=state.agents,
            markets=state.markets,
            government=state.government,
            bank=state.bank,
            central_bank=state.central_bank,
            stock_market=state.stock_market,
            stock_tracker=state.stock_tracker,
            goods_data=state.goods_data,
            market_data={}, # Will be populated in Phase 1 (and 0 for Gov)
            config_module=state.config_module,
            tracker=state.tracker,
            logger=state.logger,
            ai_training_manager=state.ai_training_manager,
            ai_trainer=state.ai_trainer,
            settlement_system=state.settlement_system,
            next_agent_id=state.next_agent_id,
            real_estate_units=state.real_estate_units,
            injectable_sensory_dto=injectable_sensory_dto,
            inactive_agents=state.inactive_agents
        )

    def _synchronize_world_state(self, sim_state: SimulationState):
        # Sync back scalar values that might have changed
        self.world_state.next_agent_id = sim_state.next_agent_id

        # Note: Collections (households, firms, etc.) are passed by reference in DTO,
        # so modifications to objects inside them are already reflected.
        # But if the list itself was replaced (e.g. filtered), we need to sync.
        # Phase 5 filtered state.firms in place: state.firms[:] = [...]
        # So WorldState.firms should be updated because it shares the same list object?
        # Yes, `state.firms[:] = ...` modifies the list in place.
        # `sim_state.firms` refers to `self.world_state.firms`.
        pass

    def _finalize_tick(self, sim_state: SimulationState):
        state = self.world_state

        # Money Supply Verification (Post-Tick)
        if state.time >= 1:
            current_money = state.calculate_total_money()
            expected_money = state.baseline_money_supply
            if hasattr(state.government, "get_monetary_delta"):
                expected_money += state.government.get_monetary_delta()

            delta = current_money - expected_money

            msg = f"MONEY_SUPPLY_CHECK | Current: {current_money:.2f}, Expected: {expected_money:.2f}, Delta: {delta:.4f}"
            extra_data = {"tick": state.time, "current": current_money, "expected": expected_money, "delta": delta, "tags": ["money_supply"]}

            if abs(delta) > 1.0:
                 state.logger.warning(msg, extra=extra_data)
            else:
                 state.logger.info(msg, extra=extra_data)

    def prepare_market_data(self) -> Dict[str, Any]:
        """
        Legacy/External access to market data preparation.
        Delegates to the logic used in Phase 1.

        Used by: Simulation._prepare_market_data
        """
        # Create a proper SimulationState DTO to satisfy type requirements
        # passing None for injectable_sensory_dto as it's not needed for this legacy call
        sim_state = self._create_simulation_state_dto(None)
        return prepare_market_data(sim_state)
