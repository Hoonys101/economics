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

        if state.government:
             state.government.finalize_tick(state.time)

        if self.world_state.persistence_manager:
             # TD-160: Use world_state.transactions to ensure all drained transactions are captured
             self.world_state.persistence_manager.buffer_tick_state(self.world_state, self.world_state.transactions)
             if state.time % self.world_state.batch_save_interval == 0:
                 self.world_state.persistence_manager.flush_buffers(state.time)

        # Reset counters
        for h in state.households:
             if hasattr(h, "reset_consumption_counters"):
                 h.reset_consumption_counters()

        for f in state.firms:
            if hasattr(f, 'finance') and hasattr(f.finance, 'finalize_tick'):
                # Aggregating multi-currency expenses into a single float for metrics
                if isinstance(f.finance.expenses_this_tick, dict):
                    f.finance.last_daily_expenses = sum(f.finance.expenses_this_tick.values())

                # Correctly handles multi-currency reset and capitalization
                f.finance.finalize_tick()

                # Explicitly enforce dictionary reset if finalize_tick didn't (Safety Net)
                # This ensures we don't accidentally get a float from somewhere else.
                if not isinstance(f.finance.expenses_this_tick, dict):
                     f.finance.expenses_this_tick = {DEFAULT_CURRENCY: 0.0}
                if not isinstance(f.finance.revenue_this_tick, dict):
                     f.finance.revenue_this_tick = {DEFAULT_CURRENCY: 0.0}

            else:
                logger.warning(
                    f"FIRM_RESET_SKIPPED | Firm {f.id} skipped finance reset.",
                    extra={"firm_id": f.id, "has_finance": hasattr(f, 'finance')}
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
