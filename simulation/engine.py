from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging
import hashlib
import random
from collections import deque

from simulation.models import Transaction, Order, StockOrder, RealEstateUnit
from simulation.core_agents import Household, Skill
from simulation.firms import Firm
from simulation.service_firms import ServiceFirm
from simulation.markets.order_book_market import OrderBookMarket
from simulation.core_markets import Market
from simulation.bank import Bank
from simulation.agents.government import Government
from simulation.agents.central_bank import CentralBank
from simulation.loan_market import LoanMarket
from simulation.markets.stock_market import StockMarket
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.metrics.inequality_tracker import InequalityTracker
from simulation.metrics.stock_tracker import StockMarketTracker, PersonalityStatisticsTracker
from simulation.ai_model import AIEngineRegistry
from simulation.ai.ai_training_manager import AITrainingManager
from simulation.systems.ma_manager import MAManager
from simulation.systems.reflux_system import EconomicRefluxSystem
from simulation.systems.demographic_manager import DemographicManager # Phase 19
from simulation.systems.immigration_manager import ImmigrationManager # Phase 20-3
from simulation.systems.inheritance_manager import InheritanceManager # Phase 22 (WO-049)
from simulation.systems.housing_system import HousingSystem # Phase 22.5
from simulation.systems.persistence_manager import PersistenceManager # Phase 22.5
from simulation.systems.firm_management import FirmSystem # Phase 22.5
from simulation.systems.technology_manager import TechnologyManager # Phase 23 (WO-053)
from simulation.systems.bootstrapper import Bootstrapper # WO-058
from simulation.systems.generational_wealth_audit import GenerationalWealthAudit
from simulation.decisions.housing_manager import HousingManager # For rank/tier helper
from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner
from simulation.systems.transaction_processor import TransactionProcessor # SoC Refactor
from modules.finance.system import FinanceSystem
from simulation.systems.api import (
    EventContext, SocialMobilityContext, SensoryContext, CommerceContext,
    LearningUpdateContext
)
from simulation.systems.social_system import SocialSystem
from simulation.systems.event_system import EventSystem
from simulation.systems.sensory_system import SensorySystem
from simulation.systems.commerce_system import CommerceSystem
from simulation.systems.labor_market_analyzer import LaborMarketAnalyzer
from simulation.components.agent_lifecycle import AgentLifecycleComponent

# Use the repository pattern for data access
from simulation.db.repository import SimulationRepository
from simulation.dtos import (
    AgentStateData,
    TransactionData,
    EconomicIndicatorData,
    AIDecisionData,
    MarketHistoryData,
    StockMarketHistoryData,
    WealthDistributionData,
    PersonalityStatisticsData,
    DecisionContext,
    GovernmentStateDTO,
    MacroFinancialContext,
)
# Phase 28
from simulation.dtos.scenario import StressScenarioConfig

logger = logging.getLogger(__name__)


from modules.common.config_manager.api import ConfigManager


class Simulation:
    """경제 시뮬레이션의 전체 흐름을 관리하고 조정하는 핵심 엔진 클래스."""

    def __init__(
        self,
        config_manager: ConfigManager,
        config_module: Any,
        logger: logging.Logger,
        repository: SimulationRepository
    ) -> None:
        """
        초기화된 구성 요소들을 할당받습니다.
        실제 생성 로직은 SimulationInitializer에 의해 외부에서 수행됩니다.
        """
        self.config_manager = config_manager
        self.config_module = config_module
        self.logger = logger
        self.repository = repository

        # These attributes are populated by the SimulationInitializer
        self.time: int = 0
        self.run_id: int = 0
        self.households: List[Household] = []
        self.firms: List[Firm] = []
        self.agents: Dict[int, Any] = {}
        self.next_agent_id: int = 0
        self.markets: Dict[str, Market] = {}
        self.bank: Optional[Bank] = None
        self.government: Optional[Government] = None
        self.central_bank: Optional[CentralBank] = None
        self.stock_market: Optional[StockMarket] = None
        self.tracker: Optional[EconomicIndicatorTracker] = None
        self.inequality_tracker: Optional[InequalityTracker] = None
        self.stock_tracker: Optional[StockMarketTracker] = None
        self.personality_tracker: Optional[PersonalityStatisticsTracker] = None
        self.ai_training_manager: Optional[AITrainingManager] = None
        self.ma_manager: Optional[MAManager] = None
        self.reflux_system: Optional[EconomicRefluxSystem] = None
        self.demographic_manager: Optional[DemographicManager] = None
        self.immigration_manager: Optional[ImmigrationManager] = None
        self.inheritance_manager: Optional[InheritanceManager] = None
        self.housing_system: Optional[HousingSystem] = None
        self.persistence_manager: Optional[PersistenceManager] = None
        self.firm_system: Optional[FirmSystem] = None
        self.technology_manager: Optional[TechnologyManager] = None
        self.generational_wealth_audit: Optional[GenerationalWealthAudit] = None
        self.breeding_planner: Optional[VectorizedHouseholdPlanner] = None
        self.transaction_processor: Optional[TransactionProcessor] = None
        self.lifecycle_manager: Optional[Any] = None # To be AgentLifecycleManager
        self.goods_data: List[Dict[str, Any]] = []
        self.real_estate_units: List[RealEstateUnit] = []
        self.finance_system: Optional[FinanceSystem] = None
        self.ai_trainer: Optional[AIEngineRegistry] = None

        # New Systems
        self.social_system: Optional[SocialSystem] = None
        self.event_system: Optional[EventSystem] = None
        self.sensory_system: Optional[SensorySystem] = None
        self.commerce_system: Optional[CommerceSystem] = None
        self.labor_market_analyzer: Optional[LaborMarketAnalyzer] = None
        self.stress_scenario_config: Optional[StressScenarioConfig] = None # Phase 28

        # Attributes with default values
        self.batch_save_interval: int = 50
        self.household_time_allocation: Dict[int, float] = {}
        self.last_interest_rate: float = 0.0 # Will be set from bank

    def finalize_simulation(self):
        """시뮬레이션 종료 시 Repository 연결을 닫고, 시뮬레이션 종료 시간을 기록합니다."""
        self.persistence_manager.flush_buffers(self.time)  # Flush any remaining data
        self.repository.update_simulation_run_end_time(self.run_id)
        self.repository.close()
        self.logger.info("Simulation finalized and Repository connection closed.")



    # _update_social_ranks and _calculate_reference_standard moved to SocialSystem

    def run_tick(self, injectable_sensory_dto: Optional[GovernmentStateDTO] = None) -> None:
        # --- Gold Standard / Money Supply Verification (WO-016) ---
        if self.time == 0:
            self.baseline_money_supply = self._calculate_total_money()
            self.logger.info(
                f"MONEY_SUPPLY_BASELINE | Baseline Money Supply set to: {self.baseline_money_supply:.2f}",
                extra={"tick": self.time, "money_supply": self.baseline_money_supply}
            )

        self.time += 1
        self.logger.info(
            f"--- Starting Tick {self.time} ---",
            extra={"tick": self.time, "tags": ["tick_start"]},
        )

        # ===== Chaos Injection Events (via EventSystem) =====
        if self.event_system:
             context: EventContext = {
                 "households": self.households,
                 "firms": self.firms,
                 "markets": self.markets
             }
             self.event_system.execute_scheduled_events(self.time, context, self.stress_scenario_config)

        # WO-054: Government Public Education Logic (START OF TICK)
        self.government.run_public_education(self.households, self.config_module, self.time, self.reflux_system)

        if (
            self.time > 0
            and self.time % self.config_module.IMITATION_LEARNING_INTERVAL == 0
        ):
            self.ai_training_manager.run_imitation_learning_cycle(self.time)

        # Update Bank Tick (Interest Processing)
        # Phase 4: Pass current_tick to bank for credit jail logic
        # Phase 8-B: Pass reflux_system to capture bank profits
        if hasattr(self.bank, "run_tick") and "reflux_system" in self.bank.run_tick.__code__.co_varnames:
             self.bank.run_tick(self.agents, self.time, reflux_system=self.reflux_system)
        elif hasattr(self.bank, "run_tick") and "current_tick" in self.bank.run_tick.__code__.co_varnames:
             self.bank.run_tick(self.agents, self.time)
        else:
             self.bank.run_tick(self.agents)


        # Legacy call removed: self.government.update_monetary_policy(...)

        # Phase 14-1: Firm Profit Distribution (Operation Reflux)
        for firm in self.firms:
             firm.distribute_profit(self.agents, self.time)

        for firm in self.firms:
            firm.hires_last_tick = 0

        for market in self.markets.values():
            if isinstance(market, OrderBookMarket):
                market.clear_orders()

        # WO-057-Fix: Update tracker with the latest data before government decisions
        money_supply = self._calculate_total_money()
        self.tracker.track(self.time, self.households, self.firms, self.markets, money_supply=money_supply)

        # [WO-060] Update stock market reference prices at the start of the tick
        if self.stock_market is not None:
            active_firms = {f.id: f for f in self.firms if f.is_active}
            self.stock_market.update_reference_prices(active_firms)

        # Phase 17-4: Update Social Ranks & Calculate Reference Standard (via SocialSystem)
        market_data = self._prepare_market_data(self.tracker)
        
        if getattr(self.config_module, "ENABLE_VANITY_SYSTEM", False) and self.social_system:
            context: SocialMobilityContext = {
                "households": self.households
            }
            self.social_system.update_social_ranks(context)
            ref_std = self.social_system.calculate_reference_standard(context)
            market_data["reference_standard"] = ref_std

        # Phase 17-5: Leviathan Logic Integration
        # 1. Update Household Political Opinions
        for h in self.households:
            if h.is_active:
                h.update_political_opinion()

        # 2. Government Gathers Opinion
        self.government.update_public_opinion(self.households)

        # --- WO-057-B: Sensory Module Pipeline (via SensorySystem) ---
        sensory_context: SensoryContext = {
            "tracker": self.tracker,
            "government": self.government,
            "time": self.time
        }

        # Anti-Pattern Fix: Removed lazy initialization.
        # Systems MUST be initialized by SimulationInitializer.
        if self.sensory_system:
            sensory_dto = self.sensory_system.generate_government_sensory_dto(sensory_context)
        else:
            self.logger.error("SensorySystem not initialized! Check SimulationInitializer.")
            # Fallback to empty DTO to prevent crash if critical, but log error
            sensory_dto = GovernmentStateDTO(self.time, 0, 0, 0, 0, 0, 0)

        # Supply to Government
        if injectable_sensory_dto and injectable_sensory_dto.tick == self.time:
            self.government.update_sensory_data(injectable_sensory_dto)
            self.logger.warning(
                f"INJECTED_SENSORY_DATA | Overrode sensory data for tick {self.time} with custom DTO.",
                extra={"tick": self.time, "tags": ["test_injection"]}
            )
        else:
            self.government.update_sensory_data(sensory_dto)

        # --- WO-062: Macro-Financial Context for Households ---
        macro_financial_context = None
        if getattr(self.config_module, "MACRO_PORTFOLIO_ADJUSTMENT_ENABLED", False):
            interest_rate_trend = self.bank.base_rate - self.last_interest_rate
            self.last_interest_rate = self.bank.base_rate

            market_volatility = self.stock_tracker.get_market_volatility() if self.stock_tracker else 0.0

            macro_financial_context = MacroFinancialContext(
                inflation_rate=sensory_dto.inflation_sma,
                gdp_growth_rate=sensory_dto.gdp_growth_sma,
                market_volatility=market_volatility,
                interest_rate_trend=interest_rate_trend
            )

        # [DEBUG WO-057]
        latest_indicators = self.tracker.get_latest_indicators()
        self.logger.info(f"DEBUG_WO057 | Tick {self.time} | Indicators: {list(latest_indicators.keys())}")
        self.logger.info(f"DEBUG_WO057 | AvgPrice: {latest_indicators.get('avg_goods_price', 'MISSING')}")
        self.logger.info(f"DEBUG_WO057 | SensoryDTO: InfSMA={sensory_dto.inflation_sma:.4f}, UnempSMA={sensory_dto.unemployment_sma:.4f}, DebtRat={sensory_dto.current_gdp:.4f}")
        # -----------------------------------------

        # 3. Government Makes Policy Decision
        # Inject GDP for AI state
        latest_gdp = self.tracker.get_latest_indicators().get("total_production", 0.0)
        market_data["total_production"] = latest_gdp

        self.government.make_policy_decision(market_data, self.time, self.central_bank)

        # Monetary policy is updated AFTER the government's fiscal/AI decision
        # This allows the AI to influence the Central Bank's rate for the current tick
        self.central_bank.step(self.time)
        new_base_rate = self.central_bank.get_base_rate()
        self.bank.update_base_rate(new_base_rate)

        # 4. Election Check
        self.government.check_election(self.time)

        # Age firms
        for firm in self.firms:
            firm.age += 1

        # Service national debt
        self.finance_system.service_debt(self.time)

        # Phase 4: Welfare Check (Executes Subsidies based on Policy)
        self.government.run_welfare_check(list(self.agents.values()), market_data, self.time)

        # Snapshot agents for learning (Pre-state)
        for f in self.firms:
            if f.is_active: f.pre_state_snapshot = f.get_agent_data()
        for h in self.households:
            if h.is_active: h.pre_state_snapshot = h.get_agent_data()

        all_transactions: List[Transaction] = []

        firm_pre_states = {}
        for firm in self.firms:
            if firm.is_active:
                # Guard for AI-driven engines (RuleBased engines don't have ai_engine)
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

                # Phase 8-B: Pass reflux_system to firm.make_decision for CAPEX capture
                firm_orders, action_vector = firm.make_decision(self.markets, self.goods_data, market_data, self.time, self.government, self.reflux_system, self.stress_scenario_config)
                for order in firm_orders:
                    target_market = self.markets.get(order.market_id)
                    if target_market:
                        target_market.place_order(order, self.time)
                
                self.logger.debug(f"TRACE_ENGINE | Firm {firm.id} submitted {len(firm_orders)} orders to markets.")

        household_pre_states = {}
        household_time_allocation = {}  # Store time allocation for later use
        for household in self.households:
            if household.is_active:
                # Guard for AI-driven engines (RuleBased engines don't have ai_engine)
                if hasattr(household.decision_engine, 'ai_engine') and household.decision_engine.ai_engine:
                    pre_strategic_state = (
                        household.decision_engine.ai_engine._get_strategic_state(
                            household.get_agent_data(), market_data
                        )
                    )
                    household_pre_states[household.id] = {
                        "pre_strategic_state": pre_strategic_state, # Legacy support
                    }

                # make_decision return (orders, vector)
                household_orders, action_vector = household.make_decision(
                    self.markets, self.goods_data, market_data, self.time, self.government, macro_financial_context, self.stress_scenario_config
                )

                # Phase 5: Calculate Time Allocation (Hydraulic Model)
                # work_hours = work_agg * MAX_WORK_HOURS
                # leisure_hours = 24 - work_hours - SHOPPING_HOURS
                # Guard: RuleBased engines return tuple, not ActionVector DTO
                if hasattr(action_vector, 'work_aggressiveness'):
                    work_aggressiveness = action_vector.work_aggressiveness
                else:
                    work_aggressiveness = 0.5 # Default for RuleBased
                max_work_hours = self.config_module.MAX_WORK_HOURS
                shopping_hours = getattr(self.config_module, "SHOPPING_HOURS", 2.0)
                hours_per_tick = getattr(self.config_module, "HOURS_PER_TICK", 24.0)

                work_hours = work_aggressiveness * max_work_hours
                leisure_hours = max(0.0, hours_per_tick - work_hours - shopping_hours)

                household_time_allocation[household.id] = leisure_hours
                self.household_time_allocation[household.id] = leisure_hours

                for order in household_orders:
                    # [Phase 23.5 Fix] Handle INVEST orders for startup creation (Active Entrepreneurship)
                    if order.order_type == "INVEST" and order.market_id == "admin":
                        self.logger.info(f"FOUND_INVEST_ORDER | Agent {household.id} attempting startup via admin market.")
                        self.firm_system.spawn_firm(self, household)
                        continue

                    # Determine target market based on Order Type or ID
                    target_market_id = order.market_id

                    # Routing Logic for Deposit/Withdraw/Loan
                    if order.order_type in ["DEPOSIT", "WITHDRAW", "LOAN_REQUEST", "REPAYMENT"]:
                        target_market_id = "loan_market"
                    elif order.item_id in ["deposit", "currency"]: # Fallback
                        target_market_id = "loan_market"

                    household_target_market = self.markets.get(target_market_id)

                    if household_target_market:
                        household_target_market.place_order(order, self.time)
                    else:
                        self.logger.warning(
                            f"Market '{order.market_id}' not found for order from agent {household.id}",
                            extra={"tick": self.time},
                        )

                self.logger.debug(f"TRACE_ENGINE | Household {household.id} submitted {len(household_orders)} orders back to engine.")

        for market in self.markets.values():
            if isinstance(market, OrderBookMarket):
                all_transactions.extend(market.match_orders(self.time))

        # ---------------------------------------------------------
        # Stock Market Matching
        # ---------------------------------------------------------
        if self.stock_market is not None:
            # 주식 거래 매칭
            stock_transactions = self.stock_market.match_orders(self.time)
            self._process_stock_transactions(stock_transactions)
            all_transactions.extend(stock_transactions)
            self.stock_market.clear_expired_orders(self.time)

        self._process_transactions(all_transactions)

        # ---------------------------------------------------------
        # Activate Consumption Logic & Leisure Effects (via CommerceSystem)
        # ---------------------------------------------------------
        # Recalculate vacancy count for correct death classification
        current_vacancies = 0
        labor_market = self.markets.get("labor")
        if labor_market and isinstance(labor_market, OrderBookMarket):
             for item_orders in labor_market.buy_orders.values():
                 for order in item_orders:
                     current_vacancies += order.quantity

        consumption_market_data = market_data.copy()
        consumption_market_data["job_vacancies"] = current_vacancies

        commerce_context: CommerceContext = {
            "households": self.households,
            "agents": self.agents,
            "breeding_planner": self.breeding_planner,
            "household_time_allocation": household_time_allocation,
            "reflux_system": self.reflux_system,
            "market_data": consumption_market_data,
            "config": self.config_module,
            "time": self.time
        }

        if self.commerce_system:
            # Phase 28: Pass stress scenario config
            household_leisure_effects = self.commerce_system.execute_consumption_and_leisure(commerce_context, self.stress_scenario_config)
        else:
            self.logger.error("CommerceSystem not initialized! Skipping consumption cycle.")
            household_leisure_effects = {}

        # --- Phase 23: Technology Manager Update ---
        self.technology_manager.update(self.time, self)

        # Phase 17-3B: Process Housing (Mortgage, Rent, Maintenance, Foreclosure)
        self.housing_system.process_housing(self)
        self.housing_system.apply_homeless_penalty(self)

        # Phase 17-3B: Housing Market Matching
        if "housing" in self.markets:
             housing_transactions = self.markets["housing"].match_orders(self.time)
             all_transactions.extend(housing_transactions)

        # --- Phase 19: Population Dynamics ---
        # 🌟 Refactored: Delegate to AgentLifecycleManager
        if self.lifecycle_manager:
            self.lifecycle_manager.process_lifecycle_events(self)
        else:
            self.logger.error("LifecycleManager is not initialized!")

        # ---------------------------------------------------------
        # Activate Farm Logic (Production & Needs/Wages)
        # ---------------------------------------------------------
        for firm in self.firms:
             if firm.is_active:
                 # Phase 23: Pass Technology Manager for Productivity
                 firm.produce(self.time, technology_manager=self.technology_manager)
                 # Phase 4: Pass government and market_data for income tax withholding
                 # Phase 8-B: Pass reflux_system for expense capture
                 firm.update_needs(self.time, self.government, market_data, self.reflux_system)
                 
                 # 2a. 법인세(Corporate Tax) 징수 (이익이 발생한 경우)
                 # [LEVIATHAN UPDATE] use government.calculate_corporate_tax
                 if firm.is_active and firm.current_profit > 0:
                     tax_amount = self.government.calculate_corporate_tax(firm.current_profit)
                     firm.assets -= tax_amount
                     self.government.collect_tax(tax_amount, "corporate_tax", firm.id, self.time)

        # 2b. 정부 인프라 투자 (예산 충족 시)
        # Phase 8-B: Pass reflux_system to capture infrastructure spending
        if self.government.invest_infrastructure(self.time, self.reflux_system):
            # 인프라 투자 성공 시 모든 기업의 TFP 상향 조정
            tfp_boost = getattr(self.config_module, "INFRASTRUCTURE_TFP_BOOST", 0.05)
            for firm in self.firms:
                firm.productivity_factor *= (1.0 + tfp_boost)
            self.logger.info(
                f"GLOBAL_TFP_BOOST | All firms productivity increased by {tfp_boost*100:.1f}%",
                extra={"tick": self.time, "tags": ["government", "infrastructure"]}
            )


        # --- AI Learning Update (Unified) ---
        market_data_for_learning = self._prepare_market_data(self.tracker)

        # Firms
        for firm in self.firms:
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
                    run_id=self.run_id,
                    tick=self.time,
                    agent_id=firm.id,
                    decision_type="VECTOR_V2",
                    decision_details={"reward": reward},
                    predicted_reward=None,
                    actual_reward=reward,
                )
                self.repository.save_ai_decision(decision_data)

        # Households
        for household in self.households:
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
                    run_id=self.run_id,
                    tick=self.time,
                    agent_id=household.id,
                    decision_type="VECTOR_V2",
                    decision_details={"reward": reward},
                    predicted_reward=None,
                    actual_reward=reward,
                )
                self.repository.save_ai_decision(decision_data)

        # 8. M&A 및 파산 처리 (Corporate Metabolism)
        self.ma_manager.process_market_exits_and_entries(self.time)

        # 9. 비활성 기업 정리 (Cleanup Inactive Firms)
        # Remove inactive firms from the active processing list
        # They remain in self.agents for ID reference, but won't act in future ticks
        active_firms_count_before = len(self.firms)
        self.firms = [f for f in self.firms if f.is_active]
        
        if len(self.firms) < active_firms_count_before:
            self.logger.info(f"CLEANUP | Removed {active_firms_count_before - len(self.firms)} inactive firms from execution list.")

        # --- Handle Agent Lifecycle (Death, Liquidation) ---
        # 🌟 Refactored: This is now handled inside lifecycle_manager.process_lifecycle_events()

        # Entrepreneurship Check (Spawn new firms if needed)
        self.firm_system.check_entrepreneurship(self)

        # Phase 5: Finalize Government Stats for the tick
        self.government.finalize_tick(self.time)

        # Phase 8-B: Distribute Reflux Funds (Service Sector Income)
        # Must happen before state save so households see the income
        self.reflux_system.distribute(self.households)

        # Save all state at the end of the tick
        self.persistence_manager.buffer_tick_state(self, all_transactions)

        # Flush buffers to DB periodically
        if self.time % self.batch_save_interval == 0:
            self.persistence_manager.flush_buffers(self.time)

        # Reset consumption and income counters for next tick
        for h in self.households:
            if hasattr(h, "current_consumption"):
                h.current_consumption = 0.0
            if hasattr(h, "current_food_consumption"):
                h.current_food_consumption = 0.0

            # Reset Income Accumulators
            if hasattr(h, "labor_income_this_tick"):
                h.labor_income_this_tick = 0.0
            if hasattr(h, "capital_income_this_tick"):
                h.capital_income_this_tick = 0.0

        # Reset/Update Firm Counters for Solvency Logic
        for f in self.firms:
            # Snapshot for next tick's decision
            f.last_daily_expenses = f.expenses_this_tick
            f.last_sales_volume = f.sales_volume_this_tick
            # Reset current counters
            f.sales_volume_this_tick = 0.0
            f.expenses_this_tick = 0.0 # Reset expenses as well
            f.revenue_this_tick = 0.0 # Reset revenue

        # --- Gold Standard / Money Supply Verification (WO-016) ---
        if self.time >= 1:
            # Phase 23.5: Final Solvency Check (Clear negative artifacts)
            self.bank.check_solvency(self.government)

            current_money = self._calculate_total_money()
            expected_money = getattr(self, "baseline_money_supply", 0.0)
            if hasattr(self.government, "get_monetary_delta"):
                expected_money += self.government.get_monetary_delta()

            delta = current_money - expected_money

            # Log Level: Info normally, Warning if delta is significant (> 1.0)
            msg = f"MONEY_SUPPLY_CHECK | Current: {current_money:.2f}, Expected: {expected_money:.2f}, Delta: {delta:.4f}"
            extra_data = {"tick": self.time, "current": current_money, "expected": expected_money, "delta": delta, "tags": ["money_supply"]}

            if abs(delta) > 1.0:
                 self.logger.warning(msg, extra=extra_data)
            else:
                 self.logger.info(msg, extra=extra_data)

        # WO-058: Generational Wealth Audit
        if self.time % 100 == 0:
             self.generational_wealth_audit.run_audit(self.households, self.time)

        self.logger.info(
            f"--- Ending Tick {self.time} ---",
            extra={"tick": self.time, "tags": ["tick_end"]},
        )

        # Clear markets for next tick
        for market in self.markets.values():
            market.clear_orders()

        # Track stock market
        if self.stock_market is not None:
            self.stock_tracker.track_all_firms([f for f in self.firms if f.is_active], self.stock_market)


    def _prepare_market_data(self, tracker: EconomicIndicatorTracker) -> Dict[str, Any]:
        """현재 틱의 시장 데이터를 에이전트의 의사결정을 위해 준비합니다."""
        goods_market_data: Dict[str, Any] = {}

        # [Bank Info Injection for AI]
        # In a real scenario, this would be queried from LoanMarket or Bank directly.
        # Here we inject the bank instance wrapper or summary map.
        debt_data_map = {}
        deposit_data_map = {}
        for agent_id in self.agents:
            if isinstance(self.agents[agent_id], Household) or isinstance(self.agents[agent_id], Firm):
                debt_data_map[agent_id] = self.bank.get_debt_summary(agent_id)
                deposit_data_map[agent_id] = self.bank.get_deposit_balance(agent_id)

        for good_name in self.config_module.GOODS:
            market = self.markets.get(good_name)
            if market and isinstance(market, OrderBookMarket):
                # 1. 이번 틱의 평균 체결가 (거래가 있었다면 가장 정확)
                avg_price = market.get_daily_avg_price()
                
                # 2. 거래가 없었다면 호가창의 최저 매도가(Best Ask)
                if avg_price <= 0:
                    avg_price = market.get_best_ask(good_name) or 0
                
                # 3. 호가도 없다면 이전 틱의 기록된 가격 (Tracker)
                if avg_price <= 0:
                    latest = tracker.get_latest_indicators()
                    # Tracker 필드명은 {item_id}_avg_price 형식을 따름 (EconomicIndicatorTracker 참고)
                    avg_price = latest.get(f"{good_name}_avg_price", 0)
                
                # 4. 모두 없다면 설정 파일의 초기 가격
                if avg_price <= 0:
                    avg_price = self.config_module.GOODS[good_name].get("initial_price", 10.0)
                
                goods_market_data[f"{good_name}_current_sell_price"] = avg_price

        # Include Labor Market Data (Use historical data as the order book is cleared)
        latest_indicators = tracker.get_latest_indicators()
        avg_wage = latest_indicators.get("labor_avg_price", self.config_module.LABOR_MARKET_MIN_WAGE)
        
        labor_market = self.markets.get("labor")
        best_wage_offer = 0.0
        if labor_market and isinstance(labor_market, OrderBookMarket):
            # Best bid in the labor market is the highest wage offered by a firm
            best_wage_offer = labor_market.get_best_bid("labor") or 0.0
            # If the market currently has no orders, fall back to historical avg
            if best_wage_offer <= 0:
                best_wage_offer = avg_wage

        # Operation Forensics (WO-021): Calculate Job Vacancies
        # Sum of quantities of all buy orders in the labor market
        job_vacancies = 0
        if labor_market and isinstance(labor_market, OrderBookMarket):
             # buy_orders is Dict[item_id, List[Order]]
             # In labor market, item_id is usually "labor" or "research_labor"
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
        for good_name in self.config_module.GOODS:
            price = goods_market_data.get(f"{good_name}_current_sell_price")
            if price is not None:
                total_price += price
                count += 1

        avg_goods_price_for_market_data = total_price / count if count > 0 else 10.0

        # 주식 시장 데이터 추가
        stock_market_data = {}
        if self.stock_market:
            for firm in self.firms:
                firm_item_id = f"stock_{firm.id}"
                # StockMarket 클래스의 메서드는 정수 firm.id를 사용함
                price = self.stock_market.get_daily_avg_price(firm.id)
                if price <= 0:
                    price = self.stock_market.get_best_ask(firm.id) or 0
                if price <= 0:
                    # 장기 기록이나 장부가를 fallback으로 사용 가능
                    price = firm.assets / firm.total_shares if firm.total_shares > 0 else 10.0
                stock_market_data[firm_item_id] = {"avg_price": price}

        # Calculate Avg Rent Price (Phase 20-3)
        rent_prices = [u.rent_price for u in self.real_estate_units if u.owner_id is not None]
        avg_rent = sum(rent_prices) / len(rent_prices) if rent_prices else self.config_module.INITIAL_RENT_PRICE

        # Inject Housing Market Data
        housing_market_data = {
            "avg_rent_price": avg_rent
        }

        return {
            "time": self.time,
            "goods_market": goods_market_data,
            "housing_market": housing_market_data, # Phase 20-3
            "loan_market": {"interest_rate": self.bank.base_rate}, # Use bank base rate
            "stock_market": stock_market_data,
            "all_households": self.households,
            "avg_goods_price": avg_goods_price_for_market_data,
            "debt_data": debt_data_map, # Injected Debt Data
            "deposit_data": deposit_data_map, # Injected Deposit Data
            "inflation": latest_indicators.get("inflation_rate", self.config_module.DEFAULT_INFLATION_RATE) # Phase 28: Inject inflation for AI
        }

    def _calculate_total_money(self) -> float:
        """
        Calculates the total money supply in the system.
        Money_Total = Household_Assets + Firm_Assets + Bank_Reserves + Reflux_Balance
        (Government assets are excluded as it is the issuer)
        """
        total = 0.0

        # 1. Households
        for h in self.households:
            if h.is_active:
                total += h.assets

        # 2. Firms
        for f in self.firms:
            if f.is_active:
                total += f.assets

        # 3. Bank Reserves
        total += self.bank.assets

        # 4. Reflux System Balance (Undistributed)
        if hasattr(self, "reflux_system"):
            total += self.reflux_system.balance

        return total


    def get_all_agents(self) -> List[Any]:
        """시뮬레이션에 참여하는 모든 활성 에이전트(가계, 기업, 은행 등)를 반환합니다."""
        all_agents = []
        for agent in self.agents.values():
            if (
                getattr(agent, "is_active", True)
                and hasattr(agent, "value_orientation")
                and agent.value_orientation != "N/A"
            ):
                all_agents.append(agent)
        return all_agents

    def _process_transactions(self, transactions: List[Transaction]) -> None:
        """발생한 거래들을 처리하여 에측된 가계/기업 상태 등을 업데이트합니다."""
        # SoC Refactor: Logic moved to TransactionProcessor
        market_data_cb = lambda: self._prepare_market_data(self.tracker).get("goods_market", {})
        self.transaction_processor.process(
            transactions=transactions,
            agents=self.agents,
            government=self.government,
            current_time=self.time,
            market_data_callback=market_data_cb
        )

    def _process_stock_transactions(self, transactions: List[Transaction]) -> None:
        """Process stock transactions."""
        for tx in transactions:
            buyer_id = tx.buyer_id
            seller_id = tx.seller_id
            buyer = self.agents.get(buyer_id)
            seller = self.agents.get(seller_id)
            # Correct firm_id parsing from stock_{id}
            try:
                firm_id = int(tx.item_id.split("_")[1])
            except (IndexError, ValueError):
                continue

            if buyer and seller:
                cost = tx.price * tx.quantity

                # Buyer: Update assets and Portfolio
                buyer.assets -= cost
                buyer.portfolio.add(firm_id, tx.quantity, tx.price)
                # Sync legacy dict
                buyer.shares_owned[firm_id] = buyer.portfolio.holdings[firm_id].quantity

                # Seller: Update assets
                seller.assets += cost

                # Update treasury shares if firm is the seller (SEO)
                if isinstance(seller, Firm) and seller.id == firm_id:
                    seller.treasury_shares -= tx.quantity
                elif hasattr(seller, "portfolio"):
                    # Secondary market trade
                    seller.portfolio.remove(firm_id, tx.quantity)
                
                # Sync Legacy Dictionaries for Seller
                if hasattr(seller, "shares_owned"):
                    if firm_id in seller.portfolio.holdings:
                        seller.shares_owned[firm_id] = seller.portfolio.holdings[firm_id].quantity
                    elif firm_id in seller.shares_owned:
                        del seller.shares_owned[firm_id]

                # Synchronize Market Shareholder Registry (CRITICAL for Dividends)
                if self.stock_market:
                    # Sync Buyer
                    self.stock_market.update_shareholder(buyer.id, firm_id, buyer.portfolio.holdings[firm_id].quantity)
                    # Sync Seller
                    if hasattr(seller, "portfolio") and firm_id in seller.portfolio.holdings:
                        self.stock_market.update_shareholder(seller.id, firm_id, seller.portfolio.holdings[firm_id].quantity)
                    else:
                        self.stock_market.update_shareholder(seller.id, firm_id, 0.0)

                self.logger.info(
                    f"STOCK_TX | Buyer: {buyer.id}, Seller: {seller.id}, Firm: {firm_id}, Qty: {tx.quantity}, Price: {tx.price}",
                    extra={"tick": self.time, "tags": ["stock_market", "transaction"]}
                )
