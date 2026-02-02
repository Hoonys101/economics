from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING, Any, Dict
import logging

from simulation.dtos.api import SimulationState, GovernmentStateDTO
from simulation.orchestration.phases import (
    Phase0_PreSequence, Phase_Production, Phase1_Decision, Phase2_Matching,
    Phase3_Transaction, Phase_Bankruptcy, Phase_Consumption, Phase5_PostSequence
)
from simulation.orchestration.utils import prepare_market_data
from simulation.orchestration.phases_recovery import Phase_SystemicLiquidation

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
            Phase_Bankruptcy(world_state),           # Phase 4 (Spec): Lifecycle & Bankruptcy
            Phase_SystemicLiquidation(world_state),  # Phase 4.5 (Spec): Systemic Liquidation
            Phase2_Matching(world_state),            # Phase 5 (Spec): Matching
            Phase3_Transaction(world_state),
            Phase_Consumption(world_state),          # Late Lifecycle (Consumption Finalization)
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

        # TD-177: Ensure flow counters are reset at the start of the tick
        if state.government and hasattr(state.government, "reset_tick_flow"):
            state.government.reset_tick_flow()

        # 1. Create the comprehensive state DTO for this tick
        sim_state = self._create_simulation_state_dto(injectable_sensory_dto)

        # 2. Execute all phases in sequence
        for phase in self.phases:
            sim_state = phase.execute(sim_state)
            # TD-192: Immediately drain and sync state back to WorldState
            self._drain_and_sync_state(sim_state)

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
            escrow_agent=getattr(state, "escrow_agent", None),
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
            inactive_agents=state.inactive_agents,
            effects_queue=[], # TD-192: Init empty
            inter_tick_queue=[], # TD-192: Init empty
            transactions=[] # TD-192: Init empty
        )

    def _drain_and_sync_state(self, sim_state: SimulationState):
        """
        Drains transient queues from SimulationState into WorldState and syncs scalars.
        This ensures changes from a phase are immediately persisted before the next phase runs.
        """
        ws = self.world_state

        # --- Sync Scalars ---
        ws.next_agent_id = sim_state.next_agent_id

        # --- Drain Transient Queues ---
        # The core of the solution: move items from the DTO's queue to the WorldState's
        # master queue for the tick, then clear the DTO's queue so it's fresh for the next phase.

        if sim_state.effects_queue:
            ws.effects_queue.extend(sim_state.effects_queue)
            sim_state.effects_queue.clear() # Prevent double-processing

        if sim_state.inter_tick_queue:
            ws.inter_tick_queue.extend(sim_state.inter_tick_queue)
            sim_state.inter_tick_queue.clear() # Prevent double-processing

        if sim_state.transactions:
            # TD-177: Structural Guarantee for M2 Integrity
            # Process monetary transactions incrementally as they are drained.
            # This ensures ALL transactions, including late-bound ones, are captured.
            if sim_state.government and hasattr(sim_state.government, "process_monetary_transactions"):
                sim_state.government.process_monetary_transactions(sim_state.transactions)

            ws.transactions.extend(sim_state.transactions)
            sim_state.transactions.clear() # Prevent double-processing

        # --- Sync mutable collections by reference (ensure no re-assignment) ---
        # This acts as a safety check. If a phase violates the rule, this will raise an error.
        if ws.agents is not sim_state.agents:
            raise RuntimeError("CRITICAL: 'agents' collection was re-assigned in a phase. Use in-place modification.")

        # Update the inactive agents dictionary
        ws.inactive_agents.update(sim_state.inactive_agents)

    def _finalize_tick(self, sim_state: SimulationState):
        state = self.world_state

        # TD-160: Clear world_state transactions to prevent memory leak and double-processing
        # Persistence has already happened in Phase 5.
        state.transactions.clear()

        # Track Economics
        if state.tracker:
             state.tracker.track(
                 time=state.time,
                 households=state.households,
                 firms=state.firms,
                 markets=state.markets,
                 money_supply=state.calculate_total_money()
             )

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
