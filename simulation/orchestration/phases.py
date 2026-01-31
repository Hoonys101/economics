from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import logging

from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import (
    SimulationState, MarketSnapshotDTO, GovernmentPolicyDTO,
    DecisionContext, MacroFinancialContext, AIDecisionData
)
from modules.government.dtos import MacroEconomicSnapshotDTO
from simulation.dtos import (
    GovernmentStateDTO, FiscalContext
)
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.markets.order_book_market import OrderBookMarket
from simulation.systems.api import (
    EventContext, SocialMobilityContext, SensoryContext,
    CommerceContext, LearningUpdateContext
)
from simulation.models import Transaction, Order
from modules.government.components.monetary_policy_manager import MonetaryPolicyManager
from simulation.orchestration.utils import prepare_market_data
from modules.government.proxy import GovernmentFiscalProxy


if TYPE_CHECKING:
    from simulation.world_state import WorldState
    from simulation.action_processor import ActionProcessor
    from simulation.metrics.economic_tracker import EconomicIndicatorTracker
    from simulation.dtos.scenario import StressScenarioConfig

logger = logging.getLogger(__name__)


class Phase0_PreSequence(IPhaseStrategy):
    def __init__(self, world_state: WorldState):
        self.world_state = world_state
        self.mp_manager = MonetaryPolicyManager(world_state.config_module)

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

        return state


class Phase_Production(IPhaseStrategy):
    """
    Phase 0.5: Technology update and firm production.
    Ensures firms have updated inventory before the Decision phase.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        from simulation.systems.tech.api import FirmTechInfoDTO, HouseholdEducationDTO

        # 1. Calculate Human Capital Index
        active_households_dto = [
            HouseholdEducationDTO(is_active=h.is_active, education_level=getattr(h, 'education_level', 0))
            for h in state.households if h.is_active
        ]
        
        total_edu = sum(h['education_level'] for h in active_households_dto)
        active_count = len(active_households_dto)
        human_capital_index = total_edu / active_count if active_count > 0 else 1.0

        # 2. Update Technology System
        if self.world_state.technology_manager:
            active_firms_dto = [
                FirmTechInfoDTO(
                    id=f.id,
                    sector=f.sector,
                    is_visionary=getattr(f, 'is_visionary', False),
                    current_rd_investment=f.research_history.get("total_spent", 0.0) if hasattr(f, "research_history") else 0.0
                )
                for f in state.firms if f.is_active
            ]
            self.world_state.technology_manager.update(state.time, active_firms_dto, human_capital_index)

        # 3. Trigger Firm Production
        for firm in state.firms:
            if firm.is_active:
                firm.produce(state.time, technology_manager=self.world_state.technology_manager)

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

        # Construct Market Signals (Phase 2)
        from modules.system.api import MarketSignalDTO
        market_signals: Dict[str, MarketSignalDTO] = {}

        import math

        for m_id, market in state.markets.items():
            # Only process OrderBookMarkets that have items
            if isinstance(market, OrderBookMarket):
                # Identify all unique items in this market (buy or sell side)
                all_items = set(market.buy_orders.keys()) | set(market.sell_orders.keys()) | set(market.last_traded_prices.keys())

                for item_id in all_items:
                     price_history = list(market.price_history.get(item_id, []))
                     # Take last 7 ticks or less
                     history_7d = price_history[-7:]

                     # Volatility Calculation
                     volatility = 0.0
                     if len(history_7d) > 1:
                         mean = sum(history_7d) / len(history_7d)
                         variance = sum((p - mean) ** 2 for p in history_7d) / len(history_7d)
                         volatility = math.sqrt(variance)

                     # Check frozen status
                     min_p, max_p = market.get_dynamic_price_bounds(item_id)
                     # Treat as frozen if price is inf or circuit breaker active (heuristic)
                     # Since we don't have explicit state, we assume False unless proven otherwise.
                     is_frozen = False

                     signal = MarketSignalDTO(
                         market_id=m_id,
                         item_id=item_id,
                         best_bid=market.get_best_bid(item_id),
                         best_ask=market.get_best_ask(item_id),
                         last_traded_price=market.get_last_traded_price(item_id),
                         last_trade_tick=market.get_last_trade_tick(item_id) or -1,
                         price_history_7d=history_7d,
                         volatility_7d=volatility,
                         order_book_depth_buy=len(market.buy_orders.get(item_id, [])),
                         order_book_depth_sell=len(market.sell_orders.get(item_id, [])),
                         is_frozen=is_frozen
                     )
                     market_signals[item_id] = signal

        market_snapshot = MarketSnapshotDTO(
            tick=state.time,
            market_signals=market_signals,
            market_data=market_data # Legacy support
        )

        gov = state.government
        bank = state.bank
        gov_policy = GovernmentPolicyDTO(
             income_tax_rate=getattr(gov, "income_tax_rate", 0.1),
             sales_tax_rate=getattr(state.config_module, "SALES_TAX_RATE", 0.05),
             corporate_tax_rate=getattr(gov, "corporate_tax_rate", 0.2),
             base_interest_rate=getattr(bank, "base_rate", 0.05) if bank else 0.05
        )

        # Create Fiscal Context
        gov_proxy = GovernmentFiscalProxy(gov) if gov else None
        fiscal_context = FiscalContext(government=gov_proxy) if gov_proxy else None

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

        # Prepare Agent Registry (WO-138)
        agent_registry = {}
        if state.government:
            agent_registry["GOVERNMENT"] = state.government.id
        if state.central_bank:
            agent_registry["CENTRAL_BANK"] = state.central_bank.id
        if state.bank:
             agent_registry["BANK"] = state.bank.id

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

                # DTO Refactor: Expect DecisionOutputDTO
                decision_output = firm.make_decision(
                    state.markets, state.goods_data, market_data, state.time,
                    fiscal_context, stress_config,
                    market_snapshot=market_snapshot, government_policy=gov_policy,
                    agent_registry=agent_registry
                )

                # Check if it's new DTO or legacy tuple
                if hasattr(decision_output, 'orders'):
                    firm_orders = decision_output.orders
                    # metadata ignored or used if needed
                else:
                    # Fallback for unmigrated code (Tuple)
                    firm_orders, action_vector = decision_output

                for order in firm_orders:
                    target_market = state.markets.get(order.market_id)
                    if target_market:
                        # WO-024: Capture immediate transactions (e.g. LoanMarket)
                        new_txs = target_market.place_order(order, state.time)
                        if new_txs:
                            state.transactions.extend(new_txs)

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
                # DTO Refactor: Expect DecisionOutputDTO
                decision_output = household.make_decision(
                    state.markets, state.goods_data, market_data, state.time, fiscal_context, macro_financial_context, stress_config,
                    market_snapshot=market_snapshot, government_policy=gov_policy,
                    agent_registry=agent_registry
                )


                if hasattr(decision_output, 'orders'):
                    household_orders = decision_output.orders
                    metadata = decision_output.metadata

                    # Assume metadata contains action_vector if needed, or handle if it is the vector itself
                    # Since AIDrivenHouseholdDecisionEngine returns vector as second element,
                    # metadata should be that vector.

                    if hasattr(metadata, 'work_aggressiveness'):
                        action_vector = metadata
                        work_aggressiveness = action_vector.work_aggressiveness
                    else:
                         work_aggressiveness = 0.5
                else:
                    # Legacy Tuple
                    household_orders, action_vector = decision_output
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
                    # WO-053: Force deflationary pressure on basic_food
                    if hasattr(order, "item_id") and order.item_id == "basic_food" and order.side == "BUY": # Update order_type -> side
                         # Check for generic scenario parameter via config injection
                         deflationary_multiplier = getattr(state.config_module, "DEFLATIONARY_PRESSURE_MULTIPLIER", None)

                         if deflationary_multiplier is not None:
                             current_price = market_data.get("basic_food_current_sell_price", 5.0)
                             # Update price -> price_limit (OrderDTO) or use alias
                             # OrderDTO has 'price' property alias
                             # But Order dataclass (alias) might not if it's just OrderDTO
                             # OrderDTO has price property.
                             # But we might need to construct a new order if it's frozen?
                             # OrderDTO is frozen=True.
                             # So we must replace.
                             from dataclasses import replace
                             new_price = min(order.price, max(0.1, current_price * float(deflationary_multiplier)))
                             order = replace(order, price_limit=new_price)

                    if order.side == "INVEST" and order.market_id == "admin": # Update order_type -> side
                        if self.world_state.firm_system:
                            self.world_state.firm_system.spawn_firm(state, household)
                        else:
                            state.logger.warning(f"SKIPPED_INVESTMENT | Agent {household.id} tried startup but firm_system missing.")
                        continue

                    target_market_id = order.market_id
                    if order.side in ["DEPOSIT", "WITHDRAW", "LOAN_REQUEST", "REPAYMENT"]: # Update order_type -> side
                        target_market_id = "loan_market"
                    elif hasattr(order, "item_id") and order.item_id in ["deposit", "currency"]:
                        target_market_id = "loan_market"

                    household_target_market = state.markets.get(target_market_id)

                    if household_target_market:
                        # WO-024: Capture immediate transactions (e.g. LoanMarket)
                        new_txs = household_target_market.place_order(order, state.time)
                        if new_txs:
                            state.transactions.extend(new_txs)

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
            "market_data": consumption_market_data,
            "config": state.config_module,
            "time": state.time,
            "government": state.government
        }

        if self.world_state.commerce_system:
            planned_cons, commerce_txs = self.world_state.commerce_system.plan_consumption_and_leisure(
                commerce_context, self.world_state.stress_scenario_config
            )
            state.planned_consumption = planned_cons

            for tx in commerce_txs:
                if tx.transaction_type == "PHASE23_MARKET_ORDER":
                     # WO-053: Convert special transaction to Order
                     # Use new OrderDTO fields: side, price_limit
                     order = Order(
                         agent_id=tx.buyer_id,
                         item_id=tx.item_id,
                         quantity=tx.quantity,
                         price_limit=tx.price,
                         side="BUY",
                         market_id=tx.item_id
                     )
                     market = state.markets.get(tx.item_id)
                     if market:
                         new_txs = market.place_order(order, state.time)
                         if new_txs:
                             state.transactions.extend(new_txs)
                else:
                     state.transactions.append(tx)

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
            bank_txs = state.bank.run_tick(state.agents, state.time)
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

            infra_txs = state.government.invest_infrastructure(state.time, state.households)
            if infra_txs:
                system_transactions.extend(infra_txs)

            edu_txs = state.government.run_public_education(state.households, state.config_module, state.time)
            if edu_txs:
                system_transactions.extend(edu_txs)

        state.transactions.extend(system_transactions)

        # WO-024: Process Monetary Transactions (Credit Creation/Destruction)
        if state.government:
            state.government.process_monetary_transactions(state.transactions)

        if self.world_state.transaction_processor:
            self.world_state.transaction_processor.execute(state)
        else:
            state.logger.error("TransactionProcessor not initialized.")

        return state


class Phase_Bankruptcy(IPhaseStrategy):
    """
    Phase 4: Agent Decisions & Lifecycle (Bankruptcy Check)
    Agents make decisions. Bankrupt agents are identified here.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        if self.world_state.lifecycle_manager:
            lifecycle_txs = self.world_state.lifecycle_manager.execute(state)
            if lifecycle_txs:
                state.inter_tick_queue.extend(lifecycle_txs)
        return state

class Phase_Consumption(IPhaseStrategy):
    """
    Phase: Consumption Finalization.
    Formerly part of Phase4_Lifecycle.
    """
    def __init__(self, world_state: WorldState):
        self.world_state = world_state

    def execute(self, state: SimulationState) -> SimulationState:
        consumption_market_data = state.market_data

        commerce_context: CommerceContext = {
            "households": state.households,
            "agents": state.agents,
            "breeding_planner": self.world_state.breeding_planner,
            "household_time_allocation": state.household_time_allocation,
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
