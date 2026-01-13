from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging
import hashlib
import random

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
from simulation.decisions.housing_manager import HousingManager # For rank/tier helper
from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner
from simulation.systems.transaction_processor import TransactionProcessor # SoC Refactor

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
)

logger = logging.getLogger(__name__)


class Simulation:
    """경제 시뮬레이션의 전체 흐름을 관리하고 조정하는 핵심 엔진 클래스."""

    def __init__(
        self,
        households: List[Household],
        firms: List[Firm],
        ai_trainer: AIEngineRegistry,
        repository: SimulationRepository,
        config_module: Any,
        goods_data: List[Dict[str, Any]],
        logger: logging.Logger | None = None,
    ) -> None:
        """Simulation 클래스를 초기화합니다."""
        self.logger = logger if logger else logging.getLogger(__name__)
        self.households = households
        self.firms = firms
        self.goods_data = goods_data
        self.agents: Dict[int, Any] = {h.id: h for h in households}
        self.agents.update({f.id: f for f in firms})
        self.next_agent_id = len(households) + len(firms)

        self.ai_trainer = ai_trainer
        self.config_module = config_module
        self.time: int = 0

        self.batch_save_interval = 50 # WO-051: Hardcoded I/O Optimization

        self.bank = Bank(
            id=self.next_agent_id,
            initial_assets=self.config_module.INITIAL_BANK_ASSETS,
            config_module=self.config_module
        )
        self.agents[self.bank.id] = self.bank
        self.next_agent_id += 1

        # 정부 에이전트 초기화
        self.government = Government(
            id=self.next_agent_id, 
            initial_assets=0.0, 
            config_module=self.config_module
        )
        self.agents[self.government.id] = self.government
        self.next_agent_id += 1

        # Tracker initialization (Done below, but CentralBank needs it)
        # So we move Tracker init up or init CentralBank later.
        # Moving Tracker init up.
        self.tracker = EconomicIndicatorTracker(config_module=config_module)

        # Economic Reflux System (Phase 8-B) - Moved up for init usage
        self.reflux_system = EconomicRefluxSystem()

        # Central Bank Initialization (Phase 10)
        self.central_bank = CentralBank(
            tracker=self.tracker,
            config_module=self.config_module
        )
        # Central Bank is not in self.agents dict as it's a special system agent
        # similar to how markets are handled, or we can add it if needed.
        # But it doesn't participate in normal transactions.

        # Phase 17-3A: Initialize Real Estate Units
        self.real_estate_units: List[RealEstateUnit] = [
            RealEstateUnit(id=i, estimated_value=self.config_module.INITIAL_PROPERTY_VALUE,
                           rent_price=self.config_module.INITIAL_RENT_PRICE)
            for i in range(self.config_module.NUM_HOUSING_UNITS)
        ]

        # Distribute to top 20% households
        top_20_count = len(self.households) // 5
        top_households = sorted(self.households, key=lambda h: h.assets, reverse=True)[:top_20_count]

        for i, hh in enumerate(top_households):
            if i < len(self.real_estate_units):
                unit = self.real_estate_units[i]
                unit.owner_id = hh.id
                hh.owned_properties.append(unit.id)
                # Owner occupies their own unit initially
                unit.occupant_id = hh.id
                hh.residing_property_id = unit.id
                hh.is_homeless = False

        self.markets: Dict[str, Market] = {
            good_name: OrderBookMarket(market_id=good_name)
            for good_name in self.config_module.GOODS
        }
        self.markets["labor"] = OrderBookMarket(market_id="labor")
        self.markets["loan_market"] = LoanMarket(
            market_id="loan_market", bank=self.bank, config_module=self.config_module
        )
        # Pass agents reference to LoanMarket for credit check
        self.markets["loan_market"].agents_ref = self.agents
        
        self.stock_market: Optional[StockMarket] = None
        # 주식 시장 초기화
        if getattr(self.config_module, "STOCK_MARKET_ENABLED", False):
            self.stock_market = StockMarket(
                config_module=self.config_module,
                logger=self.logger,
            )
            self.markets["stock_market"] = self.stock_market
        else:
            self.stock_market = None

        # Phase 17-3B: Housing Market & Initial Sales
        self.markets["housing"] = OrderBookMarket(market_id="housing")
        
        # Government places SELL orders for unowned properties (80 units)
        for unit in self.real_estate_units:
            if unit.owner_id is None:
                # Sell Order: item_id="unit_{id}", price=estimated_value, qty=1
                sell_order = Order(
                    agent_id=self.government.id, # Government ID
                    item_id=f"unit_{unit.id}",
                    price=unit.estimated_value,
                    quantity=1.0,
                    market_id="housing",
                    order_type="SELL"
                )
                if "housing" in self.markets:
                    self.markets["housing"].place_order(sell_order, self.time)

        # 2. 에이전트 욕구 업데이트 (Update Needs)
        # Fix Money Leak: Pass reflux_system to capture initial expenses (e.g. Marketing)
        # Also pass government for consistency (though tax usually requires profit/income)
        for agent in self.households + self.firms:
            if isinstance(agent, Firm):
                 agent.update_needs(self.time, self.government, None, self.reflux_system)
            else:
                 agent.update_needs(self.time)
            
        # 3. 에이전트 의사결정 및 행동 (Decisions & Actions)
        for agent in self.households + self.firms:
            agent.decision_engine.markets = self.markets
            agent.decision_engine.goods_data = self.goods_data
            if isinstance(agent, Firm):
                agent.config_module = self.config_module

        self.repository = repository
        # self.tracker = EconomicIndicatorTracker(config_module=config_module) # Moved up
        
        # 추가 지표 Tracker 초기화
        self.inequality_tracker = InequalityTracker(config_module=config_module)
        self.stock_tracker = StockMarketTracker(config_module=config_module)
        self.personality_tracker = PersonalityStatisticsTracker(config_module=config_module)
        
        self.ai_training_manager = AITrainingManager(
            self.households, self.config_module
        )
        
        # M&A Manager System
        self.ma_manager = MAManager(self, self.config_module)

        # Phase 19: Demographic Manager
        self.demographic_manager = DemographicManager(config_module=self.config_module)

        # Phase 20-3: Immigration Manager
        self.immigration_manager = ImmigrationManager(config_module=self.config_module)

        # Phase 22: Inheritance Manager
        self.inheritance_manager = InheritanceManager(config_module=self.config_module)

        # Phase 22.5: Housing System (Refactored)
        self.housing_system = HousingSystem(config_module=self.config_module)

        # Phase 22.5: Persistence Manager (Refactored)
        self.persistence_manager = PersistenceManager(
            run_id=0, # Placeholder, will be set after run_id is generated below
            config_module=self.config_module,
            repository=self.repository
        )

        # Phase 22.5: Firm System (Refactored)
        self.firm_system = FirmSystem(config_module=self.config_module)

        # Phase 23: Technology Manager
        self.technology_manager = TechnologyManager(config_module=self.config_module, logger=self.logger)

        # WO-051: Vectorized Planner Initialization
        self.breeding_planner = VectorizedHouseholdPlanner(self.config_module)

        # SoC Refactor: Transaction Processor
        self.transaction_processor = TransactionProcessor(self.config_module)

        # Time allocation tracking
        self.household_time_allocation: Dict[int, float] = {}

        config_content = str(self.config_module.__dict__)
        config_hash = hashlib.sha256(config_content.encode()).hexdigest()
        self.run_id = self.repository.save_simulation_run(
            config_hash=config_hash,
            description="Economic simulation run with DB storage",
        )
        self.persistence_manager.run_id = self.run_id
        self.logger.info(
            f"Simulation run started with run_id: {self.run_id}",
            extra={"run_id": self.run_id},
        )

    def finalize_simulation(self):
        """시뮬레이션 종료 시 Repository 연결을 닫고, 시뮬레이션 종료 시간을 기록합니다."""
        self.persistence_manager.flush_buffers(self.time)  # Flush any remaining data
        self.repository.update_simulation_run_end_time(self.run_id)
        self.repository.close()
        self.logger.info("Simulation finalized and Repository connection closed.")



    def _update_social_ranks(self):
        """Phase 17-4: Update Social Rank (Percentile)"""
        # 1. Calculate Scores
        scores = []
        # Temporary instance for helper
        hm = HousingManager(None, self.config_module)

        for h in self.households:
            if not h.is_active: continue

            consumption_score = h.current_consumption * 10.0 # Weight consumption
            housing_tier = hm.get_housing_tier(h)
            housing_score = housing_tier * 1000.0 # Tier 1=1000, Tier 3=3000

            total_score = consumption_score + housing_score
            scores.append((h.id, total_score))

        # 2. Sort and Assign Rank
        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
        n = len(sorted_scores)
        if n == 0: return

        for rank_idx, (hid, _) in enumerate(sorted_scores):
            # Rank 0 (Top) -> Percentile 1.0
            # Rank N-1 (Bottom) -> Percentile 0.0
            percentile = 1.0 - (rank_idx / n)
            agent = self.agents.get(hid)
            if agent:
                agent.social_rank = percentile

    def _calculate_reference_standard(self) -> Dict[str, float]:
        """Phase 17-4: Calculate Top 20% Average Standard"""
        active_households = [h for h in self.households if h.is_active]
        if not active_households:
            return {"avg_consumption": 0.0, "avg_housing_tier": 0.0}

        top_20_count = max(1, int(len(active_households) * 0.20))
        sorted_hh = sorted(active_households, key=lambda h: getattr(h, "social_rank", 0.0), reverse=True)
        top_20 = sorted_hh[:top_20_count]

        # Temp helper
        hm = HousingManager(None, self.config_module)

        avg_cons = sum(h.current_consumption for h in top_20) / len(top_20)
        avg_tier = sum(hm.get_housing_tier(h) for h in top_20) / len(top_20)

        return {
            "avg_consumption": avg_cons,
            "avg_housing_tier": avg_tier
        }

    def run_tick(self) -> None:
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

        # 1c. 통화 정책 업데이트 (Central Bank) - Phase 10
        self.central_bank.step(self.time)
        new_base_rate = self.central_bank.get_base_rate()
        self.bank.update_base_rate(new_base_rate)

        # Legacy call removed: self.government.update_monetary_policy(...)

        # Phase 14-1: Firm Profit Distribution (Operation Reflux)
        for firm in self.firms:
             firm.distribute_profit(self.agents, self.time)

        for firm in self.firms:
            firm.hires_last_tick = 0

        for market in self.markets.values():
            if isinstance(market, OrderBookMarket):
                market.clear_orders()

        # Phase 17-4: Update Social Ranks & Calculate Reference Standard
        if getattr(self.config_module, "ENABLE_VANITY_SYSTEM", False):
            self._update_social_ranks()

        market_data = self._prepare_market_data(self.tracker)
        
        # Inject Reference Standard
        if getattr(self.config_module, "ENABLE_VANITY_SYSTEM", False):
            ref_std = self._calculate_reference_standard()
            market_data["reference_standard"] = ref_std

        # Phase 17-5: Leviathan Logic Integration
        # 1. Update Household Political Opinions
        for h in self.households:
            if h.is_active:
                h.update_political_opinion()

        # 2. Government Gathers Opinion
        self.government.update_public_opinion(self.households)

        # 3. Government Makes Policy Decision
        # Inject GDP for AI state
        latest_gdp = self.tracker.get_latest_indicators().get("total_production", 0.0)
        market_data["total_production"] = latest_gdp

        self.government.make_policy_decision(market_data, self.time)

        # 4. Election Check
        self.government.check_election(self.time)

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
                firm_orders, action_vector = firm.make_decision(self.markets, self.goods_data, market_data, self.time, self.government, self.reflux_system)
                for order in firm_orders:
                    target_market = self.markets.get(order.market_id)
                    if target_market:
                        if order.market_id == "stock_market" and isinstance(target_market, StockMarket):
                            # Convert Order to StockOrder for stock market compatibility
                            try:
                                firm_id_str = order.item_id.split("_")[-1]
                                firm_id = int(firm_id_str)
                                s_order = StockOrder(
                                    agent_id=order.agent_id,
                                    order_type=order.order_type,
                                    firm_id=firm_id,
                                    quantity=order.quantity,
                                    price=order.price
                                )
                                target_market.place_order(s_order, self.time)
                            except (ValueError, IndexError):
                                self.logger.error(f"Invalid stock item_id pattern: {order.item_id}")
                        else:
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
                    self.markets, self.goods_data, market_data, self.time, self.government
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
                        if target_market_id == "stock_market" and isinstance(household_target_market, StockMarket):
                            # Convert Order to StockOrder
                            try:
                                firm_id_str = order.item_id.split("_")[-1]
                                firm_id = int(firm_id_str)
                                s_order = StockOrder(
                                    agent_id=order.agent_id,
                                    order_type=order.order_type,
                                    firm_id=firm_id,
                                    quantity=order.quantity,
                                    price=order.price
                                )
                                household_target_market.place_order(s_order, self.time)
                            except (ValueError, IndexError):
                                self.logger.error(f"Invalid stock item_id pattern: {order.item_id}")
                        else:
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
            # 기업 기준가 업데이트
            firms_dict = {f.id: f for f in self.firms if f.is_active}
            self.stock_market.update_reference_prices(firms_dict)
            
            # 주식 거래 매칭
            stock_transactions = self.stock_market.match_orders(self.time)
            all_transactions.extend(stock_transactions)
            
            # 만료된 주문 정리
            self.stock_market.clear_expired_orders(self.time)

        self._process_transactions(all_transactions)

        # ---------------------------------------------------------
        # Activate Consumption Logic & Leisure Effects
        # ---------------------------------------------------------
        # After transactions, households have goods in inventory.
        # Now they must consume them to satisfy needs.
        household_leisure_effects = {} # Store utility for AI reward injection

        # Recalculate vacancy count for correct death classification
        current_vacancies = 0
        labor_market = self.markets.get("labor")
        if labor_market and isinstance(labor_market, OrderBookMarket):
             for item_orders in labor_market.buy_orders.values():
                 for order in item_orders:
                     current_vacancies += order.quantity

        # Create a consumption-specific market data context
        consumption_market_data = market_data.copy()
        consumption_market_data["job_vacancies"] = current_vacancies

        # WO-051: Vectorized Consumption Logic
        # Pre-calculate consumption/purchase decisions for all households
        batch_decisions = self.breeding_planner.decide_consumption_batch(self.households, consumption_market_data)
        consume_list = batch_decisions.get('consume', [0] * len(self.households))
        buy_list = batch_decisions.get('buy', [0] * len(self.households))
        food_price = batch_decisions.get('price', 5.0)  # Default food price

        for i, household in enumerate(self.households):
             if household.is_active:

                 # 1. Consumption (Vectorized Optimization)
                 # Replace decide_and_consume with vectorized result application
                 consumed_items = {}

                 # 1a. Fast Consumption (Basic Food)
                 if i < len(consume_list):
                     c_amt = consume_list[i]
                     if c_amt > 0:
                         household.consume("basic_food", c_amt, self.time)
                         consumed_items["basic_food"] = c_amt

                 # 1b. Fast Purchase (Survival Rescue - Logic Map Item 3)
                 if i < len(buy_list):
                     b_amt = buy_list[i]
                     if b_amt > 0:
                         cost = b_amt * food_price
                         if household.assets >= cost:
                             household.assets -= cost
                             household.inventory["basic_food"] = household.inventory.get("basic_food", 0) + b_amt
                             # To prevent money destruction, we route this to Reflux System (Sink)
                             self.reflux_system.capture(cost, source=f"Household_{household.id}", category="emergency_food")
                             self.logger.debug(
                                 f"VECTOR_BUY | Household {household.id} bought {b_amt:.1f} food (Fast Track)",
                                 extra={"agent_id": household.id, "tags": ["consumption", "vector_buy"]}
                             )
                             # Consume immediately if they were starving and bought it?
                             # The planner separates buy/consume. If they bought, they might consume next tick
                             # or we can force consume now if consumption was 0?
                             # Vector planner logic for consumption relies on Inventory > 0.
                             # If inventory was 0, c_amt is 0.
                             # If we buy now, we should probably allow immediate consumption.
                             if c_amt == 0:
                                 consume_now = min(b_amt, getattr(self.config_module, "FOOD_CONSUMPTION_QUANTITY", 1.0))
                                 household.consume("basic_food", consume_now, self.time)
                                 consumed_items["basic_food"] = consume_now

                 # 2. Phase 5: Leisure Effect Application
                 leisure_hours = household_time_allocation.get(household.id, 0.0)
                 effect_dto = household.apply_leisure_effect(leisure_hours, consumed_items)
                 
                 # 3. Lifecycle Update [BUGFIX: WO-Diag-003]
                 household.update_needs(self.time, consumption_market_data)

                 # Store utility for reward injection
                 household_leisure_effects[household.id] = effect_dto.utility_gained

                 # Apply XP to Children (if Parenting)
                 if effect_dto.leisure_type == "PARENTING" and effect_dto.xp_gained > 0:
                     for child_id in household.children_ids:
                         # Children might be in self.agents
                         child = self.agents.get(child_id)
                         if child and isinstance(child, Household) and child.is_active:
                             child.education_xp += effect_dto.xp_gained
                             self.logger.debug(
                                 f"PARENTING_XP_TRANSFER | Parent {household.id} -> Child {child_id}. XP: {effect_dto.xp_gained:.4f}",
                                 extra={"agent_id": household.id, "tags": ["LEISURE_EFFECT", "parenting"]}
                             )

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
        # 1. Aging
        self.demographic_manager.process_aging(self.households, self.time)

        # 2. Reproduction Decision (Vectorized WO-051)
        birth_requests = []

        # Filter Candidates: Active, Age 20-45 (Loose filter for extraction), Female? (Design says Agents are Households, Gender is attribute)
        # Spec says "20 <= age <= 45".
        # We can pass all active households to batch planner, and let it filter by age/solvency.
        # But for efficiency, we pass active households.

        active_households = [h for h in self.households if h.is_active]
        if active_households:
            decisions = self.breeding_planner.decide_breeding_batch(active_households)

            for h, decision in zip(active_households, decisions):
                if decision:
                    birth_requests.append(h)

        # 3. Execution
        new_children = self.demographic_manager.process_births(self, birth_requests)

        # 4. Registration
        for child in new_children:
            self.households.append(child)
            self.agents[child.id] = child
            child.decision_engine.markets = self.markets
            child.decision_engine.goods_data = self.goods_data
            # self.ai_training_manager.agents references self.households, so no need to append again
            # self.ai_training_manager.agents.append(child)

            # Brain inheritance is handled inside DemographicManager.process_births
            # but we need to ensure AI training manager tracks it?
            # It just iterates self.households, so appending is enough.

            # Update Stock Market Shareholder Registry
            if self.stock_market:
                for firm_id, qty in child.shares_owned.items():
                    self.stock_market.update_shareholder(child.id, firm_id, qty)

        # --- Phase 20-3: Immigration Check ---
        new_immigrants = self.immigration_manager.process_immigration(self)
        for imm in new_immigrants:
            self.households.append(imm)
            self.agents[imm.id] = imm
            imm.decision_engine.markets = self.markets
            imm.decision_engine.goods_data = self.goods_data
            # No need to explicitly add to ai_training_manager as it refs self.households

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

        # Update tracker with the latest data after transactions and consumption
        money_supply = self._calculate_total_money()
        self.tracker.track(self.time, self.households, self.firms, self.markets, money_supply=money_supply)

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


        for firm in self.firms:
            if firm.is_active and firm.id in firm_pre_states:
                post_state_data = firm.get_agent_data()
                agent_data = firm.get_agent_data()
                market_data = self._prepare_market_data(self.tracker)
                
                # Calculate Reward using new method for Firms (Brand Valuation)
                reward = firm.decision_engine.ai_engine.calculate_reward(
                    firm, firm.get_pre_state_data(), agent_data
                )
                
                # Update Learning V2
                firm.decision_engine.ai_engine.update_learning_v2(
                    reward=reward,
                    next_agent_data=agent_data,
                    next_market_data=market_data,
                )
                
                decision_data = AIDecisionData(
                    run_id=self.run_id,
                    tick=self.time,
                    agent_id=firm.id,
                    decision_type="VECTOR_V2",
                    decision_details={
                       "reward": reward
                    },
                    predicted_reward=None,
                    actual_reward=reward,
                )
                self.repository.save_ai_decision(decision_data)
                self.logger.debug(
                    f"FIRM_LEARNING_UPDATE | Firm {firm.id} updated learning. Reward: {reward:.2f}",
                    extra={
                        "tick": self.time,
                        "agent_id": firm.id,
                        "reward": reward,
                        "tags": ["ai_learning"],
                    },
                )

        # --- AI Learning Update for Households ---
        for household in self.households:
            if household.is_active and household.id in household_pre_states:
                post_state_data = household.get_agent_data()
                agent_data = household.get_agent_data()
                market_data = self._prepare_market_data(self.tracker)
                
                # Inject Phase 5 Leisure Utility into agent_data for Reward Calculation
                leisure_utility = household_leisure_effects.get(household.id, 0.0)
                agent_data["leisure_utility"] = leisure_utility

                # Calculate Reward
                reward = household.decision_engine.ai_engine._calculate_reward(
                    household.get_pre_state_data(),
                    post_state_data,
                    agent_data,
                    market_data,
                )
                
                # Update Learning V2
                household.decision_engine.ai_engine.update_learning_v2(
                    reward=reward,
                    next_agent_data=agent_data,
                    next_market_data=market_data,
                )

                decision_data = AIDecisionData(
                    run_id=self.run_id,
                    tick=self.time,
                    agent_id=household.id,
                    decision_type="VECTOR_V2",
                    decision_details={
                        "reward": reward
                    },
                    predicted_reward=None,
                    actual_reward=reward,
                )
                self.repository.save_ai_decision(decision_data)
                self.logger.debug(
                    f"HOUSEHOLD_LEARNING_UPDATE | Household {household.id} updated learning. Reward: {reward:.2f}",
                    extra={
                        "tick": self.time,
                        "agent_id": household.id,
                        "reward": reward,
                        "tags": ["ai_learning"],
                    },
                )

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
        # Added as per requirement (previously missing in run_tick)
        self._handle_agent_lifecycle()

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

        self.logger.info(
            f"--- Ending Tick {self.time} ---",
            extra={"tick": self.time, "tags": ["tick_end"]},
        )

        # Clear markets for next tick
        for market in self.markets.values():
            market.clear_orders()


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





    def _handle_agent_lifecycle(self) -> None:
        """비활성화된 에이전트를 청산하고 시뮬레이션에서 제거합니다."""
        
        # 1. 파산 기업 청산 (Firm Liquidation)
        inactive_firms = [f for f in self.firms if not f.is_active]
        for firm in inactive_firms:
            self.logger.info(
                f"FIRM_LIQUIDATION | Starting liquidation for Firm {firm.id}. "
                f"Assets: {firm.assets:.2f}, Inventory: {sum(firm.inventory.values()):.2f}",
                extra={"agent_id": firm.id, "tags": ["liquidation"]}
            )
            
            # 1a. 직원 해고
            for employee in firm.employees:
                if employee.is_active:
                    employee.is_employed = False
                    employee.employer_id = None
            firm.employees = []
            
            # 1b. 재고 소멸 (시장에 매도하는 대신 간단히 소멸)
            total_inventory_value = sum(
                qty * firm.last_prices.get(item_id, 10.0) 
                for item_id, qty in firm.inventory.items()
            )
            firm.inventory.clear()
            
            # 1c. 자본재 소멸
            firm.capital_stock = 0.0
            
            # 1d. 현금을 주주(가계)에게 분배
            total_cash = firm.assets
            if total_cash > 0:
                outstanding_shares = firm.total_shares - firm.treasury_shares
                if outstanding_shares > 0:
                    for household in self.households:
                        if household.is_active and firm.id in household.shares_owned:
                            share_ratio = household.shares_owned[firm.id] / outstanding_shares
                            distribution = total_cash * share_ratio
                            household.assets += distribution
                            self.logger.info(
                                f"LIQUIDATION_DISTRIBUTION | Household {household.id} received "
                                f"{distribution:.2f} from Firm {firm.id} liquidation",
                                extra={"agent_id": household.id, "tags": ["liquidation"]}
                            )
                else:
                    # No active shareholders: Escheat to Government (Money Destruction)
                    from simulation.agents.government import Government
                    if isinstance(self.government, Government):
                        self.government.collect_tax(total_cash, "liquidation_escheatment", firm.id, self.time)
            
            # 1e. 주주들의 해당 기업 주식 보유량 삭제
            for household in self.households:
                if firm.id in household.shares_owned:
                    del household.shares_owned[firm.id]
                    # [Mitosis] Update registry
                    if self.stock_market:
                        self.stock_market.update_shareholder(household.id, firm.id, 0)
            
            firm.assets = 0.0
            self.logger.info(
                f"FIRM_LIQUIDATION_COMPLETE | Firm {firm.id} fully liquidated.",
                extra={"agent_id": firm.id, "tags": ["liquidation"]}
            )

        # 2. 사망 가계 청산 (Household Liquidation)
        inactive_households = [h for h in self.households if not h.is_active]
        for household in inactive_households:
            # Phase 22: Inheritance (WO-049)
            # Replaces Phase 19 DemographicManager logic and standard liquidation
            if hasattr(self, "inheritance_manager"):
                self.inheritance_manager.process_death(household, self.government, self)
            
            # Remaining cleanup (Inventory/Metadata)
            household.inventory.clear()
            # Shares should be cleared by InheritanceManager, but double check
            household.shares_owned.clear()
            household.portfolio.holdings.clear()

            # [Mitosis] Clear shareholder registry for this household
            if self.stock_market:
                for firm_id in list(self.stock_market.shareholders.keys()):
                     self.stock_market.update_shareholder(household.id, firm_id, 0)

        # 3. 시뮬레이션에서 비활성 에이전트 제거
        self.households = [h for h in self.households if h.is_active]
        self.firms = [f for f in self.firms if f.is_active]

        self.agents = {agent.id: agent for agent in self.households + self.firms}
        self.agents[self.bank.id] = self.bank

        # 4. 기업 직원 리스트 정리 (이미 제거된 가계 참조 제거)
        for firm in self.firms:
            firm.employees = [
                emp for emp in firm.employees if emp.is_active and emp.id in self.agents
            ]
