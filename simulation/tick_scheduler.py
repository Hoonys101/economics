from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Tuple
import logging

from simulation.models import Transaction, Order, StockOrder, RealEstateUnit
from simulation.core_agents import Household
from simulation.systems.tech.api import FirmTechInfoDTO, HouseholdEducationDTO
from simulation.firms import Firm
from simulation.markets.order_book_market import OrderBookMarket
from simulation.agents.government import Government
from simulation.dtos import (
    AIDecisionData,
    GovernmentStateDTO,
    MacroFinancialContext
)
from simulation.systems.api import (
    EventContext,
    SocialMobilityContext,
    SensoryContext,
    CommerceContext,
    LearningUpdateContext
)
from simulation.dtos.api import SimulationState

if TYPE_CHECKING:
    from simulation.world_state import WorldState
    from simulation.action_processor import ActionProcessor
    from simulation.metrics.economic_tracker import EconomicIndicatorTracker

logger = logging.getLogger(__name__)


class TickScheduler:
    """
    Manages the schedule and execution of a single simulation tick.
    Decomposed from Simulation engine.
    WO-103: Refactored to enforce the Sacred Sequence.
    """

    def __init__(self, world_state: WorldState, action_processor: ActionProcessor):
        self.world_state = world_state
        self.action_processor = action_processor
        from simulation.systems.system_effects_manager import SystemEffectsManager
        self.system_effects_manager = SystemEffectsManager(world_state.config_module)

    def run_tick(self, injectable_sensory_dto: Optional[GovernmentStateDTO] = None) -> None:
        state = self.world_state

        # WO-109: Phase 0A: Pre-Sequence Stabilization
        self._phase_pre_sequence_stabilization(state)

        # --- Gold Standard / Money Supply Verification (WO-016) ---
        if state.time == 0:
            state.baseline_money_supply = state.calculate_total_money()
            state.logger.info(
                f"MONEY_SUPPLY_BASELINE | Baseline Money Supply set to: {state.baseline_money_supply:.2f}",
                extra={"tick": state.time, "money_supply": state.baseline_money_supply}
            )

        state.time += 1
        state.logger.info(
            f"--- Starting Tick {state.time} ---",
            extra={"tick": state.time, "tags": ["tick_start"]},
        )

        # ===== Chaos Injection Events (via EventSystem) =====
        if state.event_system:
             context: EventContext = {
                 "households": state.households,
                 "firms": state.firms,
                 "markets": state.markets,
                 "government": state.government,
                 "central_bank": state.central_bank,
                 "bank": state.bank
             }
             state.event_system.execute_scheduled_events(state.time, context, state.stress_scenario_config)

        if (
            state.time > 0
            and state.time % state.config_module.IMITATION_LEARNING_INTERVAL == 0
        ):
            state.ai_training_manager.run_imitation_learning_cycle(state.time)

        # ==================================================================================
        # WO-116 Phase B: Transaction Generation Phase (System Transactions)
        # ==================================================================================
        system_transactions: List[Transaction] = []

        # WO-109: Drain inter-tick queue from previous tick's lifecycle events
        system_transactions.extend(state.inter_tick_queue)
        state.inter_tick_queue.clear()

        # 0. Firm Production (State Update: Inventory)
        for firm in state.firms:
             if firm.is_active:
                 firm.produce(state.time, technology_manager=state.technology_manager)

        # 1. Bank Tick (Interest)
        if hasattr(state.bank, "run_tick"):
             bank_txs = state.bank.run_tick(state.agents, state.time, reflux_system=state.reflux_system)
             system_transactions.extend(bank_txs)

        # 2. Firm Financials (Wages, Taxes, Dividends) - Requires Market Data (T-1)
        market_data_prev = self.prepare_market_data(state.tracker)
        for firm in state.firms:
             if firm.is_active:
                 firm_txs = firm.generate_transactions(
                     government=state.government,
                     market_data=market_data_prev,
                     all_households=state.households,
                     current_time=state.time
                 )
                 system_transactions.extend(firm_txs)

        # 3. Debt Service
        debt_txs = state.finance_system.service_debt(state.time)
        system_transactions.extend(debt_txs)

        # 4. Welfare & Taxes (Wealth)
        welfare_txs = state.government.run_welfare_check(list(state.agents.values()), market_data_prev, state.time)
        system_transactions.extend(welfare_txs)

        # 5. Infrastructure
        infra_txs = state.government.invest_infrastructure(state.time, state.reflux_system)
        if infra_txs:
            system_transactions.extend(infra_txs)

        # 6. Education (WO-054 Refactor)
        edu_txs = state.government.run_public_education(state.households, state.config_module, state.time, state.reflux_system)
        if edu_txs:
            system_transactions.extend(edu_txs)

        # ----------------------------------------------------------------------------------

        # Cleanup Orders (Reset for new tick)
        for firm in state.firms:
            firm.hires_last_tick = 0

        for market in state.markets.values():
            if isinstance(market, OrderBookMarket):
                market.clear_orders()

        # WO-057-Fix: Update tracker with the latest data before government decisions
        money_supply = state.calculate_total_money()
        state.tracker.track(state.time, state.households, state.firms, state.markets, money_supply=money_supply)

        # [WO-060] Update stock market reference prices at the start of the tick
        if state.stock_market is not None:
            active_firms = {f.id: f for f in state.firms if f.is_active}
            state.stock_market.update_reference_prices(active_firms)

        # Phase 17-4: Update Social Ranks & Calculate Reference Standard (via SocialSystem)
        market_data = self.prepare_market_data(state.tracker)

        if getattr(state.config_module, "ENABLE_VANITY_SYSTEM", False) and state.social_system:
            context: SocialMobilityContext = {
                "households": state.households
            }
            state.social_system.update_social_ranks(context)
            ref_std = state.social_system.calculate_reference_standard(context)
            market_data["reference_standard"] = ref_std

        # Phase 17-5: Leviathan Logic Integration
        # 1. Update Household Political Opinions
        for h in state.households:
            if h.is_active:
                h.update_political_opinion()

        # 2. Government Gathers Opinion
        state.government.update_public_opinion(state.households)

        # --- WO-057-B: Sensory Module Pipeline (via SensorySystem) ---
        sensory_context: SensoryContext = {
            "tracker": state.tracker,
            "government": state.government,
            "time": state.time
        }

        if state.sensory_system:
            sensory_dto = state.sensory_system.generate_government_sensory_dto(sensory_context)
        else:
            state.logger.error("SensorySystem not initialized! Check SimulationInitializer.")
            sensory_dto = GovernmentStateDTO(state.time, 0, 0, 0, 0, 0, 0)

        # Supply to Government
        if injectable_sensory_dto and injectable_sensory_dto.tick == state.time:
            state.government.update_sensory_data(injectable_sensory_dto)
            state.logger.warning(
                f"INJECTED_SENSORY_DATA | Overrode sensory data for tick {state.time} with custom DTO.",
                extra={"tick": state.time, "tags": ["test_injection"]}
            )
        else:
            state.government.update_sensory_data(sensory_dto)

        # --- WO-062: Macro-Financial Context for Households ---
        macro_financial_context = None
        if getattr(state.config_module, "MACRO_PORTFOLIO_ADJUSTMENT_ENABLED", False):
            interest_rate_trend = state.bank.base_rate - state.last_interest_rate
            state.last_interest_rate = state.bank.base_rate

            market_volatility = state.stock_tracker.get_market_volatility() if state.stock_tracker else 0.0

            macro_financial_context = MacroFinancialContext(
                inflation_rate=sensory_dto.inflation_sma,
                gdp_growth_rate=sensory_dto.gdp_growth_sma,
                market_volatility=market_volatility,
                interest_rate_trend=interest_rate_trend
            )

        # [DEBUG WO-057]
        latest_indicators = state.tracker.get_latest_indicators()

        # 3. Government Makes Policy Decision (Act)
        latest_gdp = state.tracker.get_latest_indicators().get("total_production", 0.0)
        market_data["total_production"] = latest_gdp

        state.government.make_policy_decision(market_data, state.time, state.central_bank)

        # Monetary policy is updated AFTER the government's fiscal/AI decision
        state.central_bank.step(state.time)
        new_base_rate = state.central_bank.get_base_rate()
        state.bank.update_base_rate(new_base_rate)

        # 4. Election Check
        state.government.check_election(state.time)

        # Age firms (moved to Lifecycle/UpdateNeeds but kept partly here?)
        # We handle 'age += 1' in firm.update_needs called in Lifecycle.
        # So we can remove this loop.
        # for firm in state.firms:
        #    firm.age += 1

        # Service national debt -> Moved to Transaction Gen
        # state.finance_system.service_debt(state.time)

        # Phase 4: Welfare Check -> Moved to Transaction Gen
        # state.government.run_welfare_check(list(state.agents.values()), market_data, state.time)

        # Snapshot agents for learning (Pre-state)
        for f in state.firms:
            if f.is_active: f.pre_state_snapshot = f.get_agent_data()
        for h in state.households:
            if h.is_active: h.pre_state_snapshot = h.get_agent_data()

        # ==================================================================================
        # THE SACRED SEQUENCE (WO-103)
        # ==================================================================================

        # 0. Construct Simulation State DTO
        sim_state = SimulationState(
            time=state.time,
            households=state.households,
            firms=state.firms,
            agents=state.agents,
            markets=state.markets,
            government=state.government,
            bank=state.bank,
            central_bank=state.central_bank,
            stock_market=state.stock_market,
            goods_data=state.goods_data,
            market_data=market_data,
            config_module=state.config_module,
            tracker=state.tracker,
            logger=state.logger,
            reflux_system=state.reflux_system,
            ai_training_manager=getattr(state, "ai_training_manager", None),
            ai_trainer=getattr(state, "ai_trainer", None),
            next_agent_id=state.next_agent_id,
            real_estate_units=state.real_estate_units,
            settlement_system=getattr(state, "settlement_system", None),
            inactive_agents=state.inactive_agents
        )

        # 1. Decisions
        firm_pre_states, household_pre_states, household_time_allocation = self._phase_decisions(
            sim_state, market_data, macro_financial_context
        )
        state.household_time_allocation = household_time_allocation # Update state

        # 2. Matching
        self._phase_matching(sim_state)

        # 3. Transactions
        self._phase_transactions(sim_state, system_transactions)
        state.transactions = sim_state.transactions  # Sync back for observability

        # 4. Lifecycle
        self._phase_lifecycle(sim_state)

        # Sync back scalars
        state.next_agent_id = sim_state.next_agent_id

        # WO-109: Process Effects
        self.system_effects_manager.process_effects(sim_state)

        # ==================================================================================
        # Post-Tick Logic
        # ==================================================================================

        # ---------------------------------------------------------
        # Activate Consumption Logic & Leisure Effects (via CommerceSystem)
        # ---------------------------------------------------------
        current_vacancies = 0
        labor_market = state.markets.get("labor")
        if labor_market and isinstance(labor_market, OrderBookMarket):
             for item_orders in labor_market.buy_orders.values():
                 for order in item_orders:
                     current_vacancies += order.quantity

        consumption_market_data = market_data.copy()
        consumption_market_data["job_vacancies"] = current_vacancies

        commerce_context: CommerceContext = {
            "households": state.households,
            "agents": state.agents,
            "breeding_planner": state.breeding_planner,
            "household_time_allocation": household_time_allocation,
            "reflux_system": state.reflux_system,
            "market_data": consumption_market_data,
            "config": state.config_module,
            "time": state.time
        }

        if state.commerce_system:
            household_leisure_effects = state.commerce_system.execute_consumption_and_leisure(commerce_context, state.stress_scenario_config)
        else:
            state.logger.error("CommerceSystem not initialized! Skipping consumption cycle.")
            household_leisure_effects = {}

        # --- Phase 23: Technology Manager Update ---
        # WO-053: Orchestrate Technology Update with DTOs
        # 1. Calculate Human Capital Index
        active_households_dto = [
            HouseholdEducationDTO(is_active=h.is_active, education_level=getattr(h, 'education_level', 0))
            for h in state.households
        ]
        total_edu = sum(h['education_level'] for h in active_households_dto if h['is_active'])
        active_count = sum(1 for h in active_households_dto if h['is_active'])
        human_capital_index = total_edu / active_count if active_count > 0 else 1.0

        # 2. Prepare Firm DTOs
        active_firms_dto = [
            FirmTechInfoDTO(id=f.id, sector=f.sector, is_visionary=getattr(f, 'is_visionary', False))
            for f in state.firms if f.is_active
        ]

        state.technology_manager.update(state.time, active_firms_dto, human_capital_index)

        # Phase 17-3B: Process Housing (Logic that didn't fit in matching/lifecycle)
        # Housing matching happened in _phase_matching.
        # But apply_homeless_penalty needs to run.
        state.housing_system.process_housing(state) # Update rent/maintenance
        state.housing_system.apply_homeless_penalty(state)

        # ---------------------------------------------------------
        # Activate Farm Logic (Production & Needs/Wages)
        # ---------------------------------------------------------
        for firm in state.firms:
             if firm.is_active:
                 # firm.produce -> Moved to Pre-Decision
                 # firm.update_needs -> Refactored to only do Lifecycle state updates (not financial)
                 firm.update_needs(state.time, state.government, market_data, state.reflux_system)

                 # Corporate Tax -> Removed (Handled in Transaction Generation)

                 # Gov Infra -> Removed (Handled in Pre-Decision)

        # --- AI Learning Update (Unified) ---
        market_data_for_learning = self.prepare_market_data(state.tracker)

        # Firms
        for firm in state.firms:
            if firm.is_active and firm.id in firm_pre_states:
                agent_data = firm.get_agent_data()

                reward = firm.decision_engine.ai_engine.calculate_reward(
                    firm, firm.get_pre_state_data(), agent_data
                )

                context: LearningUpdateContext = {
                    "reward": reward,
                    "next_agent_data": agent_data,
                    "next_market_data": market_data_for_learning
                }
                firm.update_learning(context)

                decision_data = AIDecisionData(
                    run_id=state.run_id,
                    tick=state.time,
                    agent_id=firm.id,
                    decision_type="VECTOR_V2",
                    decision_details={"reward": reward},
                    predicted_reward=None,
                    actual_reward=reward,
                )
                state.repository.save_ai_decision(decision_data)

        # Households
        for household in state.households:
            if household.is_active and household.id in household_pre_states:
                # Hybrid check: Only update learning if agent has AI engine
                if hasattr(household.decision_engine, 'ai_engine') and household.decision_engine.ai_engine:
                    post_state_data = household.get_agent_data()
                    agent_data = household.get_agent_data()

                    leisure_utility = household_leisure_effects.get(household.id, 0.0)
                    agent_data["leisure_utility"] = leisure_utility

                    reward = household.decision_engine.ai_engine._calculate_reward(
                        household.get_pre_state_data(),
                        post_state_data,
                        agent_data,
                        market_data_for_learning,
                    )

                    context: LearningUpdateContext = {
                        "reward": reward,
                        "next_agent_data": agent_data,
                        "next_market_data": market_data_for_learning
                    }
                    household.update_learning(context)

                    decision_data = AIDecisionData(
                        run_id=state.run_id,
                        tick=state.time,
                        agent_id=household.id,
                        decision_type="VECTOR_V2",
                        decision_details={"reward": reward},
                        predicted_reward=None,
                        actual_reward=reward,
                    )
                    state.repository.save_ai_decision(decision_data)

        # 8. M&A
        state.ma_manager.process_market_exits_and_entries(state.time)

        # 9. Cleanup Inactive Firms
        active_firms_count_before = len(state.firms)
        state.firms = [f for f in state.firms if f.is_active]

        if len(state.firms) < active_firms_count_before:
            state.logger.info(f"CLEANUP | Removed {active_firms_count_before - len(state.firms)} inactive firms from execution list.")

        # Phase 5: Finalize Government Stats
        state.government.finalize_tick(state.time)

        # Phase 8-B: Distribute Reflux
        state.reflux_system.distribute(state.households)

        # Save all state
        # Persistence manager needs ALL transactions?
        # state.persistence_manager.buffer_tick_state(state, all_transactions)
        # sim_state.transactions contains all processed transactions.
        state.persistence_manager.buffer_tick_state(state, sim_state.transactions)

        if state.time % state.batch_save_interval == 0:
            state.persistence_manager.flush_buffers(state.time)

        # Reset counters
        for h in state.households:
            if hasattr(h, "current_consumption"):
                h.current_consumption = 0.0
            if hasattr(h, "current_food_consumption"):
                h.current_food_consumption = 0.0
            if hasattr(h, "labor_income_this_tick"):
                h.labor_income_this_tick = 0.0
            if hasattr(h, "capital_income_this_tick"):
                h.capital_income_this_tick = 0.0

        for f in state.firms:
            f.last_daily_expenses = f.expenses_this_tick
            f.last_sales_volume = f.sales_volume_this_tick
            f.sales_volume_this_tick = 0.0
            f.expenses_this_tick = 0.0
            f.revenue_this_tick = 0.0

        # --- Gold Standard / Money Supply Verification ---
        if state.time >= 1:
            # Solvency check moved to start of tick (Phase 0A)

            current_money = state.calculate_total_money()
            expected_money = getattr(state, "baseline_money_supply", 0.0)
            if hasattr(state.government, "get_monetary_delta"):
                expected_money += state.government.get_monetary_delta()

            delta = current_money - expected_money

            msg = f"MONEY_SUPPLY_CHECK | Current: {current_money:.2f}, Expected: {expected_money:.2f}, Delta: {delta:.4f}"
            extra_data = {"tick": state.time, "current": current_money, "expected": expected_money, "delta": delta, "tags": ["money_supply"]}

            if abs(delta) > 1.0:
                 state.logger.warning(msg, extra=extra_data)
            else:
                 state.logger.info(msg, extra=extra_data)

        # WO-058: Generational Wealth Audit
        if state.time % 100 == 0:
             state.generational_wealth_audit.run_audit(state.households, state.time)

        # Phase 29: Crisis Monitor
        if state.crisis_monitor:
            state.crisis_monitor.monitor(state.time, [f for f in state.firms if f.is_active])

        state.logger.info(
            f"--- Ending Tick {state.time} ---",
            extra={"tick": state.time, "tags": ["tick_end"]},
        )

        for market in state.markets.values():
            market.clear_orders()

        if state.stock_market is not None:
            state.stock_tracker.track_all_firms([f for f in state.firms if f.is_active], state.stock_market)

    def _phase_decisions(self, state: SimulationState, market_data: Dict[str, Any], macro_context: Optional[MacroFinancialContext]) -> Tuple[Dict, Dict, Dict]:
        """Phase 1: Agents make decisions and place orders."""
        firm_pre_states = {}
        household_pre_states = {}
        household_time_allocation = {}

        # 1. Firms
        for firm in state.firms:
            if firm.is_active:
                if hasattr(firm.decision_engine, 'ai_engine') and firm.decision_engine.ai_engine:
                    pre_strategic_state = (
                        firm.decision_engine.ai_engine._get_strategic_state(
                            firm.get_agent_data(), market_data
                        )
                    )
                    pre_tactical_state = firm.decision_engine.ai_engine._get_tactical_state(
                        firm.decision_engine.ai_engine.chosen_intention,
                        firm.get_agent_data(),
                        market_data,
                    )
                    firm_pre_states[firm.id] = {
                        "pre_strategic_state": pre_strategic_state,
                        "pre_tactical_state": pre_tactical_state,
                        "chosen_intention": firm.decision_engine.ai_engine.chosen_intention,
                        "chosen_tactic": firm.decision_engine.ai_engine.last_chosen_tactic,
                    }

                stress_config = self.world_state.stress_scenario_config

                firm_orders, action_vector = firm.make_decision(
                    state.markets, state.goods_data, market_data, state.time,
                    state.government, state.reflux_system, stress_config
                )

                for order in firm_orders:
                    target_market = state.markets.get(order.market_id)
                    if target_market:
                        target_market.place_order(order, state.time)

                state.logger.debug(f"TRACE_ENGINE | Firm {firm.id} submitted {len(firm_orders)} orders to markets.")

        # 2. Households
        for household in state.households:
            if household.is_active:
                if hasattr(household.decision_engine, 'ai_engine') and household.decision_engine.ai_engine:
                    pre_strategic_state = (
                        household.decision_engine.ai_engine._get_strategic_state(
                            household.get_agent_data(), market_data
                        )
                    )
                    household_pre_states[household.id] = {
                        "pre_strategic_state": pre_strategic_state,
                    }

                stress_config = self.world_state.stress_scenario_config
                household_orders, action_vector = household.make_decision(
                    state.markets, state.goods_data, market_data, state.time, state.government, macro_context, stress_config
                )

                if hasattr(action_vector, 'work_aggressiveness'):
                    work_aggressiveness = action_vector.work_aggressiveness
                else:
                    work_aggressiveness = 0.5
                max_work_hours = state.config_module.MAX_WORK_HOURS
                shopping_hours = getattr(state.config_module, "SHOPPING_HOURS", 2.0)
                hours_per_tick = getattr(state.config_module, "HOURS_PER_TICK", 24.0)

                work_hours = work_aggressiveness * max_work_hours
                leisure_hours = max(0.0, hours_per_tick - work_hours - shopping_hours)

                household_time_allocation[household.id] = leisure_hours

                for order in household_orders:
                    if order.order_type == "INVEST" and order.market_id == "admin":
                        state.logger.info(f"FOUND_INVEST_ORDER | Agent {household.id} attempting startup via admin market.")
                        self.world_state.firm_system.spawn_firm(state, household)
                        continue

                    target_market_id = order.market_id

                    if order.order_type in ["DEPOSIT", "WITHDRAW", "LOAN_REQUEST", "REPAYMENT"]:
                        target_market_id = "loan_market"
                    elif order.item_id in ["deposit", "currency"]:
                        target_market_id = "loan_market"

                    household_target_market = state.markets.get(target_market_id)

                    if household_target_market:
                        household_target_market.place_order(order, state.time)
                    else:
                        state.logger.warning(
                            f"Market '{order.market_id}' not found for order from agent {household.id}",
                            extra={"tick": state.time},
                        )

                state.logger.debug(f"TRACE_ENGINE | Household {household.id} submitted {len(household_orders)} orders back to engine.")

        return firm_pre_states, household_pre_states, household_time_allocation

    def _phase_matching(self, state: SimulationState) -> None:
        """Phase 2: Match orders in all markets."""
        all_transactions = []

        # 1. Goods & Labor Markets
        for market in state.markets.values():
            if isinstance(market, OrderBookMarket):
                all_transactions.extend(market.match_orders(state.time))

        # 2. Stock Market
        if state.stock_market is not None:
            stock_transactions = state.stock_market.match_orders(state.time)
            # Legacy Note: action_processor.process_stock_transactions was here.
            # Now handled in TransactionProcessor.execute.
            all_transactions.extend(stock_transactions)
            state.stock_market.clear_expired_orders(state.time)

        # 3. Housing Market
        if "housing" in state.markets:
             housing_transactions = state.markets["housing"].match_orders(state.time)
             all_transactions.extend(housing_transactions)

        state.transactions = all_transactions

    def _phase_transactions(self, state: SimulationState, system_transactions: List[Transaction] = []) -> None:
        """Phase 3: Execute transactions."""
        # Merge system transactions
        if system_transactions:
            state.transactions.extend(system_transactions)

        # Use the system service directly via WorldState (or passed if added to DTO)
        if self.world_state.transaction_processor:
            self.world_state.transaction_processor.execute(state)
        else:
            state.logger.error("TransactionProcessor not initialized.")

    def _phase_lifecycle(self, state: SimulationState) -> None:
        """Phase 4: Agent Lifecycle."""
        if self.world_state.lifecycle_manager:
            lifecycle_txs = self.world_state.lifecycle_manager.execute(state)
            if lifecycle_txs:
                self.world_state.inter_tick_queue.extend(lifecycle_txs)
        else:
            state.logger.error("LifecycleManager not initialized.")

    def prepare_market_data(self, tracker: EconomicIndicatorTracker) -> Dict[str, Any]:
        """현재 틱의 시장 데이터를 에이전트의 의사결정을 위해 준비합니다."""
        state = self.world_state
        goods_market_data: Dict[str, Any] = {}

        debt_data_map = {}
        deposit_data_map = {}
        for agent_id in state.agents:
            if isinstance(state.agents[agent_id], Household) or isinstance(state.agents[agent_id], Firm):
                debt_data_map[agent_id] = state.bank.get_debt_summary(agent_id)
                deposit_data_map[agent_id] = state.bank.get_deposit_balance(agent_id)

        for good_name in state.config_module.GOODS:
            market = state.markets.get(good_name)
            if market and isinstance(market, OrderBookMarket):
                avg_price = market.get_daily_avg_price()
                if avg_price <= 0:
                    avg_price = market.get_best_ask(good_name) or 0
                if avg_price <= 0:
                    latest = tracker.get_latest_indicators()
                    avg_price = latest.get(f"{good_name}_avg_price", 0)
                if avg_price <= 0:
                    avg_price = state.config_module.GOODS[good_name].get("initial_price", 10.0)

                goods_market_data[f"{good_name}_current_sell_price"] = avg_price

        latest_indicators = tracker.get_latest_indicators()
        avg_wage = latest_indicators.get("labor_avg_price", state.config_module.LABOR_MARKET_MIN_WAGE)

        labor_market = state.markets.get("labor")
        best_wage_offer = 0.0
        if labor_market and isinstance(labor_market, OrderBookMarket):
            best_wage_offer = labor_market.get_best_bid("labor") or 0.0
            if best_wage_offer <= 0:
                best_wage_offer = avg_wage

        job_vacancies = 0
        if labor_market and isinstance(labor_market, OrderBookMarket):
             for item_orders in labor_market.buy_orders.values():
                 for order in item_orders:
                     job_vacancies += order.quantity

        goods_market_data["labor"] = {
            "avg_wage": avg_wage,
            "best_wage_offer": best_wage_offer
        }
        goods_market_data["job_vacancies"] = job_vacancies

        total_price = 0.0
        count = 0.0
        for good_name in state.config_module.GOODS:
            price = goods_market_data.get(f"{good_name}_current_sell_price")
            if price is not None:
                total_price += price
                count += 1

        avg_goods_price_for_market_data = total_price / count if count > 0 else 10.0

        stock_market_data = {}
        if state.stock_market:
            for firm in state.firms:
                firm_item_id = f"stock_{firm.id}"
                price = state.stock_market.get_daily_avg_price(firm.id)
                if price <= 0:
                    price = state.stock_market.get_best_ask(firm.id) or 0
                if price <= 0:
                    price = firm.assets / firm.total_shares if firm.total_shares > 0 else 10.0
                stock_market_data[firm_item_id] = {"avg_price": price}

        rent_prices = [u.rent_price for u in state.real_estate_units if u.owner_id is not None]
        avg_rent = sum(rent_prices) / len(rent_prices) if rent_prices else state.config_module.INITIAL_RENT_PRICE

        housing_market_data = {
            "avg_rent_price": avg_rent
        }

        return {
            "time": state.time,
            "goods_market": goods_market_data,
            "housing_market": housing_market_data,
            "loan_market": {"interest_rate": state.bank.base_rate},
            "stock_market": stock_market_data,
            "all_households": state.households,
            "avg_goods_price": avg_goods_price_for_market_data,
            "debt_data": debt_data_map,
            "deposit_data": deposit_data_map,
            "inflation": latest_indicators.get("inflation_rate", state.config_module.DEFAULT_INFLATION_RATE)
        }

    def _phase_pre_sequence_stabilization(self, state: WorldState) -> None:
        """Phase 0A: Pre-Sequence Stabilization (WO-109)."""
        if hasattr(state.bank, "generate_solvency_transactions"):
            stabilization_txs = state.bank.generate_solvency_transactions(state.government)
            if stabilization_txs:
                temp_sim_state = SimulationState(
                    time=state.time,
                    households=state.households,
                    firms=state.firms,
                    agents=state.agents,
                    markets=state.markets,
                    government=state.government,
                    bank=state.bank,
                    central_bank=state.central_bank,
                    stock_market=state.stock_market,
                    goods_data=state.goods_data,
                    market_data={},
                    config_module=state.config_module,
                    tracker=state.tracker,
                    logger=state.logger,
                    reflux_system=state.reflux_system,
                    ai_training_manager=state.ai_training_manager,
                    ai_trainer=state.ai_trainer,
                    settlement_system=state.settlement_system,
                    transactions=stabilization_txs,
                    inactive_agents=state.inactive_agents
                )
                if state.transaction_processor:
                    state.transaction_processor.execute(temp_sim_state)
                    state.logger.warning("STABILIZATION | Executed pre-sequence stabilization for Bank.")
