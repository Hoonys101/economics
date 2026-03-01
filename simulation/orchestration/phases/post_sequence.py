from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState, AIDecisionData
from simulation.orchestration.utils import prepare_market_data
from simulation.systems.api import LearningUpdateContext
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.world_state import WorldState

logger = logging.getLogger(__name__)

class Phase5_PostSequence(IPhaseStrategy):
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # Housing
        if self.world_state.housing_system:
             self.world_state.housing_system.process_housing(state)
             self.world_state.housing_system.apply_homeless_penalty(state)

        # Final Burial Pass (Atomic Stabilization)
        # Catches starvation deaths from Phase_Consumption before Tick Metrics/Audit
        if hasattr(self.world_state, 'lifecycle_manager') and self.world_state.lifecycle_manager:
            inactive_households = [h for h in state.households if not h._bio_state.is_active]
            if inactive_households:
                logger.info(f"FINAL_BURIAL | Processing {len(inactive_households)} starvation deaths.")
                # We skip Aging/Birth/Marriage and go straight to Death logic
                # Pass a limited context for safety
                from simulation.systems.lifecycle.adapters import DeathContextAdapter
                death_context = DeathContextAdapter(state)
                # Process deaths atomically
                death_txs = self.world_state.lifecycle_manager.death_system.execute(death_context)
                if death_txs:
                    # Note: These txs are recorded in the current tick but might effect next tick
                    pass

        # Cleanup households (Ensure state consistency for Audit)
        state.households[:] = [h for h in state.households if h._bio_state.is_active]

        # Learning Update
        market_data_for_learning = prepare_market_data(state)

        # Firms
        for firm in state.firms:
            if firm.is_active and firm.id in state.firm_pre_states:
                agent_data = firm.get_agent_data()

                if hasattr(firm.decision_engine, 'ai_engine'):
                     reward = firm.decision_engine.ai_engine.calculate_reward(
                        firm, firm.get_pre_state_data(), agent_data
                     )

                     firm_context: LearningUpdateContext = {
                        "reward": reward,
                        "next_agent_data": agent_data,
                        "next_market_data": market_data_for_learning
                     }
                     firm.update_learning(firm_context)

                     decision_data = AIDecisionData(
                        run_id=state.agents.get(firm.id).run_id if hasattr(state.agents.get(firm.id), 'run_id') else 0,
                        tick=state.time,
                        agent_id=firm.id,
                        decision_type="VECTOR_V2",
                        decision_details={"reward": reward},
                        predicted_reward=None,
                        actual_reward=reward,
                     )
                     self.world_state.repository.analytics.save_ai_decision(decision_data)

        # Households
        for household in state.households:
             if household._bio_state.is_active and household.id in state.household_pre_states:
                 if hasattr(household.decision_engine, 'ai_engine') and household.decision_engine.ai_engine:
                     agent_data = household.get_agent_data()
                     leisure_utility = state.household_leisure_effects.get(household.id, 0.0)
                     agent_data["leisure_utility"] = leisure_utility

                     reward = household.decision_engine.ai_engine._calculate_reward(
                         household.get_pre_state_data(),
                         agent_data, # post_state is current
                         agent_data,
                         market_data_for_learning
                     )

                     hh_context: LearningUpdateContext = {
                        "reward": reward,
                        "next_agent_data": agent_data,
                        "next_market_data": market_data_for_learning
                     }
                     household.update_learning(hh_context)

                     decision_data = AIDecisionData(
                        run_id=state.agents.get(household.id).run_id if hasattr(state.agents.get(household.id), 'run_id') else 0,
                        tick=state.time,
                        agent_id=household.id,
                        decision_type="VECTOR_V2",
                        decision_details={"reward": reward},
                        predicted_reward=None,
                        actual_reward=reward,
                     )
                     self.world_state.repository.analytics.save_ai_decision(decision_data)

        if self.world_state.ma_manager:
            self.world_state.ma_manager.process_market_exits_and_entries(state.time)

        # Cleanup firms
        active_firms_before = len(state.firms)
        state.firms[:] = [f for f in state.firms if f.is_active]
        if len(state.firms) < active_firms_before:
             state.logger.info(f"CLEANUP | Removed {active_firms_before - len(state.firms)} inactive firms.")

        if state.primary_government:
             state.primary_government.finalize_tick(state.time)

        if self.world_state.persistence_manager and self.world_state.analytics_system:
             # TD-272: Aggregation via AnalyticsSystem
             agent_states, transactions, indicators, market_history = self.world_state.analytics_system.aggregate_tick_data(self.world_state)

             self.world_state.persistence_manager.buffer_data(
                 agent_states,
                 transactions,
                 indicators,
                 market_history
             )

             if state.time % self.world_state.batch_save_interval == 0:
                 self.world_state.persistence_manager.flush_buffers(state.time)

        # Reset counters
        for h in state.households:
             if hasattr(h, "reset_consumption_counters"):
                 h.reset_consumption_counters()

        # Fetch market context for multi-currency finalization
        market_context = None
        if state.tracker and hasattr(state.tracker, "capture_market_context"):
            market_context = state.tracker.capture_market_context()

        if not market_context:
            market_context = {
                "exchange_rates": {DEFAULT_CURRENCY: 1.0},
                "benchmark_rates": {}
            }

        for f in state.firms:
            if hasattr(f, 'reset'):
                # WO-4.6: New reset interface
                f.reset()
            else:
                logger.warning(
                    f"FIRM_RESET_SKIPPED | Firm {f.id} missing reset method.",
                    extra={"firm_id": f.id}
                )

        if self.world_state.generational_wealth_audit and state.time % 100 == 0:
             self.world_state.generational_wealth_audit.run_audit(state.households, state.time)

        if self.world_state.crisis_monitor:
             self.world_state.crisis_monitor.monitor(state.time, state.firms)

        for market in state.markets.values():
             market.clear_orders()

        if state.stock_market:
             state.stock_tracker.track_all_firms(state.firms, state.stock_market)

        return state
