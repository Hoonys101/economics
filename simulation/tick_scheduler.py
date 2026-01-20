from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging

from simulation.models import Transaction, Order, StockOrder, RealEstateUnit
from simulation.core_agents import Household
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

if TYPE_CHECKING:
    from simulation.world_state import WorldState
    from simulation.action_processor import ActionProcessor
    from simulation.metrics.economic_tracker import EconomicIndicatorTracker

logger = logging.getLogger(__name__)


class TickScheduler:
    """
    Manages the schedule and execution of a single simulation tick.
    Decomposed from Simulation engine.
    """

    def __init__(self, world_state: WorldState, action_processor: ActionProcessor):
        self.world_state = world_state
        self.action_processor = action_processor

    def run_tick(self, injectable_sensory_dto: Optional[GovernmentStateDTO] = None) -> None:
        state = self.world_state

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

        # WO-054: Government Public Education Logic (START OF TICK)
        state.government.run_public_education(state.households, state.config_module, state.time, state.reflux_system)

        if (
            state.time > 0
            and state.time % state.config_module.IMITATION_LEARNING_INTERVAL == 0
        ):
            state.ai_training_manager.run_imitation_learning_cycle(state.time)

        # Update Bank Tick (Interest Processing)
        if hasattr(state.bank, "run_tick") and "reflux_system" in state.bank.run_tick.__code__.co_varnames:
             state.bank.run_tick(state.agents, state.time, reflux_system=state.reflux_system)
        elif hasattr(state.bank, "run_tick") and "current_tick" in state.bank.run_tick.__code__.co_varnames:
             state.bank.run_tick(state.agents, state.time)
        else:
             state.bank.run_tick(state.agents)

        # Phase 14-1: Firm Profit Distribution (Operation Reflux)
        for firm in state.firms:
             firm.distribute_profit(state.agents, state.time)

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
        state.logger.info(f"DEBUG_WO057 | Tick {state.time} | Indicators: {list(latest_indicators.keys())}")

        avg_price = latest_indicators.get('avg_goods_price', 'MISSING')
        avg_price_val = avg_price if isinstance(avg_price, (int, float)) else 0.0
        state.logger.info(f"DEBUG_WO057 | AvgPrice: {avg_price_val:.4f}")

        inf_sma = sensory_dto.inflation_sma if isinstance(sensory_dto.inflation_sma, (int, float)) else 0.0
        unemp_sma = sensory_dto.unemployment_sma if isinstance(sensory_dto.unemployment_sma, (int, float)) else 0.0
        debt_rat = sensory_dto.current_gdp if isinstance(sensory_dto.current_gdp, (int, float)) else 0.0

        state.logger.info(f"DEBUG_WO057 | SensoryDTO: InfSMA={inf_sma:.4f}, UnempSMA={unemp_sma:.4f}, DebtRat={debt_rat:.4f}")
        # -----------------------------------------

        # 3. Government Makes Policy Decision
        latest_gdp = state.tracker.get_latest_indicators().get("total_production", 0.0)
        market_data["total_production"] = latest_gdp

        state.government.make_policy_decision(market_data, state.time, state.central_bank)

        # Monetary policy is updated AFTER the government's fiscal/AI decision
        state.central_bank.step(state.time)
        new_base_rate = state.central_bank.get_base_rate()
        state.bank.update_base_rate(new_base_rate)

        # 4. Election Check
        state.government.check_election(state.time)

        # Age firms
        for firm in state.firms:
            firm.age += 1

        # Service national debt
        state.finance_system.service_debt(state.time)

        # Phase 4: Welfare Check
        state.government.run_welfare_check(list(state.agents.values()), market_data, state.time)

        # Snapshot agents for learning (Pre-state)
        for f in state.firms:
            if f.is_active: f.pre_state_snapshot = f.get_agent_data()
        for h in state.households:
            if h.is_active: h.pre_state_snapshot = h.get_agent_data()

        all_transactions: List[Transaction] = []

        firm_pre_states = {}
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

                firm_orders, action_vector = firm.make_decision(state.markets, state.goods_data, market_data, state.time, state.government, state.reflux_system, state.stress_scenario_config)
                for order in firm_orders:
                    target_market = state.markets.get(order.market_id)
                    if target_market:
                        target_market.place_order(order, state.time)

                state.logger.debug(f"TRACE_ENGINE | Firm {firm.id} submitted {len(firm_orders)} orders to markets.")

        household_pre_states = {}
        household_time_allocation = {}
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

                household_orders, action_vector = household.make_decision(
                    state.markets, state.goods_data, market_data, state.time, state.government, macro_financial_context, state.stress_scenario_config
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
                state.household_time_allocation[household.id] = leisure_hours

                for order in household_orders:
                    if order.order_type == "INVEST" and order.market_id == "admin":
                        state.logger.info(f"FOUND_INVEST_ORDER | Agent {household.id} attempting startup via admin market.")
                        state.firm_system.spawn_firm(state, household) # Note: spawn_firm still expects simulation instance (state)
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

        for market in state.markets.values():
            if isinstance(market, OrderBookMarket):
                all_transactions.extend(market.match_orders(state.time))

        # ---------------------------------------------------------
        # Stock Market Matching
        # ---------------------------------------------------------
        if state.stock_market is not None:
            stock_transactions = state.stock_market.match_orders(state.time)
            self.action_processor.process_stock_transactions(stock_transactions)
            all_transactions.extend(stock_transactions)
            state.stock_market.clear_expired_orders(state.time)

        # Process transactions
        market_data_cb = lambda: self.prepare_market_data(state.tracker).get("goods_market", {})
        self.action_processor.process_transactions(all_transactions, market_data_cb)

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
        state.technology_manager.update(state.time, state) # Passing state as simulation facade substitute

        # Phase 17-3B: Process Housing
        state.housing_system.process_housing(state)
        state.housing_system.apply_homeless_penalty(state)

        # Phase 17-3B: Housing Market Matching
        if "housing" in state.markets:
             housing_transactions = state.markets["housing"].match_orders(state.time)
             all_transactions.extend(housing_transactions)
             # Note: Housing transactions are processed inside housing system logic usually?
             # Wait, engine.py appended them to all_transactions but did not call process_transactions again explicitly for them.
             # Ah, _process_transactions is called ONCE in engine.py with all_transactions BEFORE housing_transactions extension.
             # Wait, looking at engine.py:
             # all_transactions.extend(stock_transactions)
             # self._process_transactions(all_transactions)
             # ...
             # all_transactions.extend(housing_transactions)
             # But _process_transactions was NOT called again.
             # This implies housing transactions generated HERE (late match) were NOT processed by _process_transactions in the same tick
             # UNLESS they are saved to DB by persistence manager buffer.
             # But their effects (assets transfer) might be missed?
             # Let's check engine.py again.
             # Yes, _process_transactions is called BEFORE housing logic.
             # housing_transactions are extended to all_transactions ONLY for buffering to DB?
             # HousingSystem.process_housing likely handles rent payments directly?
             # markets["housing"].match_orders returns transactions.
             # If they are not processed, money doesn't move.
             # BUT HousingSystem handles its own logic mostly.
             # If housing market matching produces sales, assets should move.
             # In engine.py:
             # self._process_transactions(all_transactions)
             # ...
             # housing_transactions = self.markets["housing"].match_orders(self.time)
             # all_transactions.extend(housing_transactions)

             # It seems housing transactions matched here are INDEED NOT processed by _process_transactions in engine.py!
             # This might be a bug or intended (handled elsewhere?).
             # Or maybe they are processed in NEXT tick? No, transactions are not carried over.
             # I will maintain this behavior for backward compatibility.
             # (They are added to all_transactions for persistence).

        # --- Phase 19: Population Dynamics ---
        if state.lifecycle_manager:
            state.lifecycle_manager.process_lifecycle_events(state)
        else:
            state.logger.error("LifecycleManager is not initialized!")

        # ---------------------------------------------------------
        # Activate Farm Logic (Production & Needs/Wages)
        # ---------------------------------------------------------
        for firm in state.firms:
             if firm.is_active:
                 firm.produce(state.time, technology_manager=state.technology_manager)
                 firm.update_needs(state.time, state.government, market_data, state.reflux_system)

                 # 2a. Corporate Tax
                 if firm.is_active and firm.finance.current_profit > 0:
                     tax_amount = state.government.calculate_corporate_tax(firm.finance.current_profit)
                     firm.assets -= tax_amount
                     state.government.collect_tax(tax_amount, "corporate_tax", firm.id, state.time)

        # 2b. Government Infra Investment
        if state.government.invest_infrastructure(state.time, state.reflux_system):
            tfp_boost = getattr(state.config_module, "INFRASTRUCTURE_TFP_BOOST", 0.05)
            for firm in state.firms:
                firm.productivity_factor *= (1.0 + tfp_boost)
            state.logger.info(
                f"GLOBAL_TFP_BOOST | All firms productivity increased by {tfp_boost*100:.1f}%",
                extra={"tick": state.time, "tags": ["government", "infrastructure"]}
            )

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

        # Entrepreneurship Check
        state.firm_system.check_entrepreneurship(state)

        # Phase 5: Finalize Government Stats
        state.government.finalize_tick(state.time)

        # Phase 8-B: Distribute Reflux
        state.reflux_system.distribute(state.households)

        # Save all state
        state.persistence_manager.buffer_tick_state(state, all_transactions)

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
            # Simple daily expenses tracking for solvency logic
            f.finance.last_daily_expenses = f.finance.expenses_this_tick
            f.finance.last_sales_volume = f.finance.sales_volume_this_tick
            f.finance.sales_volume_this_tick = 0.0
            f.finance.expenses_this_tick = 0.0
            f.finance.revenue_this_tick = 0.0

        # --- Gold Standard / Money Supply Verification ---
        if state.time >= 1:
            state.bank.check_solvency(state.government)

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
