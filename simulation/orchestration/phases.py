from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import (
    SimulationState, MarketSnapshotDTO, GovernmentPolicyDTO,
    DecisionContext, MacroFinancialContext, AIDecisionData
)
from simulation.dtos import (
    GovernmentStateDTO
)
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.markets.order_book_market import OrderBookMarket
from simulation.systems.api import (
    EventContext, SocialMobilityContext, SensoryContext,
    CommerceContext, LearningUpdateContext
)
from simulation.models import Transaction

if TYPE_CHECKING:
    from simulation.world_state import WorldState
    from simulation.action_processor import ActionProcessor
    from simulation.metrics.economic_tracker import EconomicIndicatorTracker
    from simulation.dtos.scenario import StressScenarioConfig

logger = logging.getLogger(__name__)

def prepare_market_data(state: SimulationState) -> Dict[str, Any]:
    """Prepares market data for agent decisions."""
    tracker = state.tracker
    goods_market_data: Dict[str, Any] = {}

    debt_data_map = {}
    deposit_data_map = {}

    # 1. Debt & Deposit Data
    if state.bank:
        for agent_id, agent in state.agents.items():
            if isinstance(agent, (Household, Firm)):
                debt_status = state.bank.get_debt_status(str(agent_id))

                total_burden = 0.0
                ticks_per_year = 100
                if hasattr(state.bank, "_get_config"):
                     ticks_per_year = state.bank._get_config("bank_defaults.ticks_per_year", 100)

                for loan in debt_status.get("loans", []):
                    total_burden += (loan["outstanding_balance"] * loan["interest_rate"]) / ticks_per_year

                debt_data_entry = dict(debt_status)
                debt_data_entry["daily_interest_burden"] = total_burden
                debt_data_entry["total_principal"] = debt_status["total_outstanding_debt"]

                debt_data_map[agent_id] = debt_data_entry
                deposit_data_map[agent_id] = state.bank.get_balance(str(agent_id))

    # 2. Goods Market Data
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
    job_vacancies = 0

    if labor_market and isinstance(labor_market, OrderBookMarket):
        best_wage_offer = labor_market.get_best_bid("labor") or 0.0
        if best_wage_offer <= 0:
            best_wage_offer = avg_wage

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

    interest_rate = 0.05
    if state.bank:
        interest_rate = state.bank.base_rate

    return {
        "time": state.time,
        "goods_market": goods_market_data,
        "housing_market": housing_market_data,
        "loan_market": {"interest_rate": interest_rate},
        "stock_market": stock_market_data,
        "all_households": state.households,
        "avg_goods_price": avg_goods_price_for_market_data,
        "debt_data": debt_data_map,
        "deposit_data": deposit_data_map,
        "inflation": latest_indicators.get("inflation_rate", state.config_module.DEFAULT_INFLATION_RATE)
    }


class Phase0_PreSequence(IPhaseStrategy):
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # WO-109: Pre-Sequence Stabilization
        if state.bank and hasattr(state.bank, "generate_solvency_transactions"):
            stabilization_txs = state.bank.generate_solvency_transactions(state.government)
            if stabilization_txs:
                state.transactions.extend(stabilization_txs)
                state.logger.warning("STABILIZATION | Queued pre-sequence stabilization transactions.")

        # Events
        if self.world_state.event_system:
             context: EventContext = {
                 "households": state.households,
                 "firms": state.firms,
                 "markets": state.markets,
                 "government": state.government,
                 "central_bank": state.central_bank,
                 "bank": state.bank
             }
             self.world_state.event_system.execute_scheduled_events(state.time, context, self.world_state.stress_scenario_config)

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
        if state.government:
            state.government.update_public_opinion(state.households)

        # Sensory System
        sensory_context: SensoryContext = {
            "tracker": state.tracker,
            "government": state.government,
            "time": state.time
        }

        sensory_dto = GovernmentStateDTO(state.time, 0, 0, 0, 0, 0, 0)
        if self.world_state.sensory_system:
            sensory_dto = self.world_state.sensory_system.generate_government_sensory_dto(sensory_context)
        else:
             state.logger.error("SensorySystem not initialized!")

        if state.government:
            if state.injectable_sensory_dto and state.injectable_sensory_dto.tick == state.time:
                state.government.update_sensory_data(state.injectable_sensory_dto)
                state.logger.warning(
                    f"INJECTED_SENSORY_DATA | Overrode sensory data for tick {state.time} with custom DTO.",
                    extra={"tick": state.time, "tags": ["test_injection"]}
                )
            else:
                state.government.update_sensory_data(sensory_dto)

            # Government Policy Decision
            latest_gdp = state.tracker.get_latest_indicators().get("total_production", 0.0)
            market_data["total_production"] = latest_gdp
            state.government.make_policy_decision(market_data, state.time, state.central_bank)

            state.government.check_election(state.time)

        # Central Bank
        if state.central_bank and state.bank:
             state.central_bank.step(state.time)
             new_base_rate = state.central_bank.get_base_rate()
             state.bank.update_base_rate(new_base_rate)

        return state


class Phase1_Decision(IPhaseStrategy):
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        # Snapshot agents for learning (Pre-state)
        for f in state.firms:
            if f.is_active: f.pre_state_snapshot = f.get_agent_data()
        for h in state.households:
            if h.is_active: h.pre_state_snapshot = h.get_agent_data()

        # Prepare Market Data
        market_data = prepare_market_data(state)
        state.market_data = market_data

        firm_pre_states = {}
        household_pre_states = {}
        household_time_allocation = {}

        # Construct DTOs
        prices = {}
        volumes = {}
        asks = {}
        best_asks = {}

        for m_id, market in state.markets.items():
            if hasattr(market, "get_daily_avg_price"):
                 prices[m_id] = market.get_daily_avg_price()
            if hasattr(market, "get_daily_volume"):
                 volumes[m_id] = market.get_daily_volume()

            if hasattr(market, "sell_orders"):
                for item_id, orders in market.sell_orders.items():
                    asks[item_id] = orders
                    if orders:
                        if hasattr(market, "get_best_ask"):
                            best_asks[item_id] = market.get_best_ask(item_id)
                        else:
                            best_asks[item_id] = orders[0].price if orders else 0.0

        if state.stock_market:
            for firm in state.firms:
                if firm.is_active:
                    price = state.stock_market.get_stock_price(firm.id)
                    prices[f"stock_{firm.id}"] = price

        market_snapshot = MarketSnapshotDTO(
            prices=prices, volumes=volumes, asks=asks, best_asks=best_asks
        )

        gov = state.government
        bank = state.bank
        gov_policy = GovernmentPolicyDTO(
             income_tax_rate=getattr(gov, "income_tax_rate", 0.1),
             sales_tax_rate=getattr(state.config_module, "SALES_TAX_RATE", 0.05),
             corporate_tax_rate=getattr(gov, "corporate_tax_rate", 0.2),
             base_interest_rate=getattr(bank, "base_rate", 0.05) if bank else 0.05
        )

        macro_financial_context = None
        if getattr(state.config_module, "MACRO_PORTFOLIO_ADJUSTMENT_ENABLED", False):
            interest_rate_trend = 0.0
            if bank:
                interest_rate_trend = bank.base_rate - self.world_state.last_interest_rate
                self.world_state.last_interest_rate = bank.base_rate

            market_volatility = self.world_state.stock_tracker.get_market_volatility() if self.world_state.stock_tracker else 0.0

            # Gov sensory data needed for macro context.
            # Assuming government has it updated.
            # Or retrieve from sensory system.
            # We'll use dummy for now or previous tick data.
            macro_financial_context = MacroFinancialContext(
                inflation_rate=0.0,
                gdp_growth_rate=0.0,
                market_volatility=market_volatility,
                interest_rate_trend=interest_rate_trend
            )

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
                    state.government, state.reflux_system, stress_config,
                    market_snapshot=market_snapshot, government_policy=gov_policy
                )

                for order in firm_orders:
                    target_market = state.markets.get(order.market_id)
                    if target_market:
                        target_market.place_order(order, state.time)

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
                    state.markets, state.goods_data, market_data, state.time, state.government, macro_financial_context, stress_config,
                    market_snapshot=market_snapshot, government_policy=gov_policy
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
                        if self.world_state.firm_system:
                            self.world_state.firm_system.spawn_firm(state, household)
                        else:
                            state.logger.warning(f"SKIPPED_INVESTMENT | Agent {household.id} tried startup but firm_system missing.")
                        continue

                    target_market_id = order.market_id
                    if order.order_type in ["DEPOSIT", "WITHDRAW", "LOAN_REQUEST", "REPAYMENT"]:
                        target_market_id = "loan_market"
                    elif order.item_id in ["deposit", "currency"]:
                        target_market_id = "loan_market"

                    household_target_market = state.markets.get(target_market_id)

                    if household_target_market:
                        household_target_market.place_order(order, state.time)

        state.firm_pre_states = firm_pre_states
        state.household_pre_states = household_pre_states
        state.household_time_allocation = household_time_allocation

        # Commerce Planning
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
            "breeding_planner": self.world_state.breeding_planner,
            "household_time_allocation": household_time_allocation,
            "reflux_system": state.reflux_system,
            "market_data": consumption_market_data,
            "config": state.config_module,
            "time": state.time
        }

        if self.world_state.commerce_system:
            planned_cons, commerce_txs = self.world_state.commerce_system.plan_consumption_and_leisure(
                commerce_context, self.world_state.stress_scenario_config
            )
            state.planned_consumption = planned_cons
            state.transactions.extend(commerce_txs)

        return state


class Phase2_Matching(IPhaseStrategy):
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        matched_txs = []
        for market in state.markets.values():
            if isinstance(market, OrderBookMarket):
                matched_txs.extend(market.match_orders(state.time))

        if state.stock_market:
            stock_txs = state.stock_market.match_orders(state.time)
            matched_txs.extend(stock_txs)
            state.stock_market.clear_expired_orders(state.time)

        if "housing" in state.markets:
             housing_txs = state.markets["housing"].match_orders(state.time)
             matched_txs.extend(housing_txs)

        state.transactions.extend(matched_txs)
        return state


class Phase3_Transaction(IPhaseStrategy):
    def __init__(self, world_state: WorldState, action_processor: ActionProcessor):
        self.world_state = world_state
        self.action_processor = action_processor

    def execute(self, state: SimulationState) -> SimulationState:
        system_transactions = []
        system_transactions.extend(state.inter_tick_queue)
        state.inter_tick_queue.clear()

        if state.bank and hasattr(state.bank, "run_tick"):
            bank_txs = state.bank.run_tick(state.agents, state.time, reflux_system=state.reflux_system)
            system_transactions.extend(bank_txs)

        market_data_prev = state.market_data
        for firm in state.firms:
             if firm.is_active:
                 firm_txs = firm.generate_transactions(
                     government=state.government,
                     market_data=market_data_prev,
                     all_households=state.households,
                     current_time=state.time
                 )
                 system_transactions.extend(firm_txs)

        if self.world_state.finance_system:
             debt_txs = self.world_state.finance_system.service_debt(state.time)
             system_transactions.extend(debt_txs)

        if state.government:
            welfare_txs = state.government.run_welfare_check(list(state.agents.values()), market_data_prev, state.time)
            system_transactions.extend(welfare_txs)

            infra_txs = state.government.invest_infrastructure(state.time, state.reflux_system)
            if infra_txs:
                system_transactions.extend(infra_txs)

            edu_txs = state.government.run_public_education(state.households, state.config_module, state.time, state.reflux_system)
            if edu_txs:
                system_transactions.extend(edu_txs)

        state.transactions.extend(system_transactions)

        if self.world_state.transaction_processor:
            self.world_state.transaction_processor.execute(state)
        else:
            state.logger.error("TransactionProcessor not initialized.")

        return state


class Phase4_Lifecycle(IPhaseStrategy):
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        if self.world_state.lifecycle_manager:
            lifecycle_txs = self.world_state.lifecycle_manager.execute(state)
            if lifecycle_txs:
                state.inter_tick_queue.extend(lifecycle_txs)

        consumption_market_data = state.market_data

        commerce_context: CommerceContext = {
            "households": state.households,
            "agents": state.agents,
            "breeding_planner": self.world_state.breeding_planner,
            "household_time_allocation": state.household_time_allocation,
            "reflux_system": state.reflux_system,
            "market_data": consumption_market_data,
            "config": state.config_module,
            "time": state.time
        }

        if self.world_state.commerce_system:
            leisure_effects = self.world_state.commerce_system.finalize_consumption_and_leisure(
                commerce_context, state.planned_consumption
            )
            state.household_leisure_effects = leisure_effects

        return state


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

                     context: LearningUpdateContext = {
                        "reward": reward,
                        "next_agent_data": agent_data,
                        "next_market_data": market_data_for_learning
                     }
                     firm.update_learning(context)

                     decision_data = AIDecisionData(
                        run_id=state.agents.get(firm.id).run_id if hasattr(state.agents.get(firm.id), 'run_id') else 0,
                        tick=state.time,
                        agent_id=firm.id,
                        decision_type="VECTOR_V2",
                        decision_details={"reward": reward},
                        predicted_reward=None,
                        actual_reward=reward,
                     )
                     self.world_state.repository.save_ai_decision(decision_data)

        # Households
        for household in state.households:
             if household.is_active and household.id in state.household_pre_states:
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

                     context: LearningUpdateContext = {
                        "reward": reward,
                        "next_agent_data": agent_data,
                        "next_market_data": market_data_for_learning
                     }
                     household.update_learning(context)

                     decision_data = AIDecisionData(
                        run_id=state.agents.get(household.id).run_id if hasattr(state.agents.get(household.id), 'run_id') else 0,
                        tick=state.time,
                        agent_id=household.id,
                        decision_type="VECTOR_V2",
                        decision_details={"reward": reward},
                        predicted_reward=None,
                        actual_reward=reward,
                     )
                     self.world_state.repository.save_ai_decision(decision_data)

        if self.world_state.ma_manager:
            self.world_state.ma_manager.process_market_exits_and_entries(state.time)

        # Cleanup firms
        active_firms_before = len(state.firms)
        state.firms[:] = [f for f in state.firms if f.is_active]
        if len(state.firms) < active_firms_before:
             state.logger.info(f"CLEANUP | Removed {active_firms_before - len(state.firms)} inactive firms.")

        if state.government:
             state.government.finalize_tick(state.time)

        if state.reflux_system:
             state.reflux_system.distribute(state.households)

        if self.world_state.persistence_manager:
             self.world_state.persistence_manager.buffer_tick_state(self.world_state, state.transactions)
             if state.time % self.world_state.batch_save_interval == 0:
                 self.world_state.persistence_manager.flush_buffers(state.time)

        # Reset counters
        for h in state.households:
             if hasattr(h, "reset_consumption_counters"):
                 h.reset_consumption_counters()

        for f in state.firms:
            f.last_daily_expenses = f.expenses_this_tick
            f.last_sales_volume = f.sales_volume_this_tick
            f.sales_volume_this_tick = 0.0
            f.expenses_this_tick = 0.0
            f.revenue_this_tick = 0.0

        if self.world_state.generational_wealth_audit and state.time % 100 == 0:
             self.world_state.generational_wealth_audit.run_audit(state.households, state.time)

        if self.world_state.crisis_monitor:
             self.world_state.crisis_monitor.monitor(state.time, state.firms)

        for market in state.markets.values():
             market.clear_orders()

        if state.stock_market:
             state.stock_tracker.track_all_firms(state.firms, state.stock_market)

        return state
