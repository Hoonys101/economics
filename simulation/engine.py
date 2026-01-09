from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging
import hashlib
import random

from simulation.models import Transaction, Order, StockOrder
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

        # Buffers for batch database writes
        self.agent_state_buffer: List[AgentStateData] = []
        self.transaction_buffer: List[TransactionData] = []
        self.economic_indicator_buffer: List[EconomicIndicatorData] = []
        self.market_history_buffer: List[MarketHistoryData] = []
        self.batch_save_interval = (
            self.config_module.BATCH_SAVE_INTERVAL
        )  # Define this in config.py

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

        # Central Bank Initialization (Phase 10)
        self.central_bank = CentralBank(
            tracker=self.tracker,
            config_module=self.config_module
        )
        # Central Bank is not in self.agents dict as it's a special system agent
        # similar to how markets are handled, or we can add it if needed.
        # But it doesn't participate in normal transactions.

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

        # 2. 에이전트 욕구 업데이트 (Update Needs)
        for agent in self.households + self.firms:
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

        # Economic Reflux System (Phase 8-B)
        self.reflux_system = EconomicRefluxSystem()

        # Time allocation tracking
        self.household_time_allocation: Dict[int, float] = {}

        config_content = str(self.config_module.__dict__)
        config_hash = hashlib.sha256(config_content.encode()).hexdigest()
        self.run_id = self.repository.save_simulation_run(
            config_hash=config_hash,
            description="Economic simulation run with DB storage",
        )
        self.logger.info(
            f"Simulation run started with run_id: {self.run_id}",
            extra={"run_id": self.run_id},
        )

    def finalize_simulation(self):
        """시뮬레이션 종료 시 Repository 연결을 닫고, 시뮬레이션 종료 시간을 기록합니다."""
        self._flush_buffers_to_db()  # Flush any remaining data
        self.repository.update_simulation_run_end_time(self.run_id)
        self.repository.close()
        self.logger.info("Simulation finalized and Repository connection closed.")

    def _save_state_to_db(self, transactions: List[Transaction]):
        """매 틱의 시뮬레이션 상태를 데이터베이스에 저장합니다."""
        self.logger.debug(
            f"DB_SAVE_START | Buffering state for tick {self.time}",
            extra={"tick": self.time, "tags": ["db_buffer"]},
        )

        # 1. Buffer agent states
        for agent in self.agents.values():
            if not getattr(agent, "is_active", False):
                continue

            agent_dto = AgentStateData(
                run_id=self.run_id,
                time=self.time,
                agent_id=agent.id,
                agent_type="",
                assets=agent.assets,
                is_active=agent.is_active,
                generation=getattr(agent, "generation", 0),
            )

            if isinstance(agent, Household):
                agent_dto.agent_type = "household"
                agent_dto.is_employed = agent.is_employed
                agent_dto.employer_id = agent.employer_id
                agent_dto.needs_survival = agent.needs.get("survival", 0)
                agent_dto.needs_labor = agent.needs.get("labor_need", 0)
                agent_dto.inventory_food = agent.inventory.get("food", 0)

                # Experiment: Time Allocation Tracking
                time_leisure = self.household_time_allocation.get(agent.id, 0.0)
                shopping_hours = getattr(self.config_module, "SHOPPING_HOURS", 2.0)
                hours_per_tick = getattr(self.config_module, "HOURS_PER_TICK", 24.0)

                agent_dto.time_leisure = time_leisure
                agent_dto.time_worked = max(0.0, hours_per_tick - time_leisure - shopping_hours)

            elif isinstance(agent, Firm):
                agent_dto.agent_type = "firm"
                agent_dto.inventory_food = agent.inventory.get("food", 0)
                agent_dto.current_production = agent.current_production
                agent_dto.num_employees = len(agent.employees)
            else:  # Skip bank or other types for now
                continue

            self.agent_state_buffer.append(agent_dto)

        # 2. Buffer transactions
        for tx in transactions:
            tx_dto = TransactionData(
                run_id=self.run_id,
                time=self.time,
                buyer_id=tx.buyer_id,
                seller_id=tx.seller_id,
                item_id=tx.item_id,
                quantity=tx.quantity,
                price=tx.price,
                market_id=tx.market_id,
                transaction_type=tx.transaction_type,
            )
            self.transaction_buffer.append(tx_dto)

        # 3. Buffer economic indicators
        # The following block replaces the original `indicators = self.tracker.get_latest_indicators()` and subsequent `if indicators:` block.
        # It also includes new calculations for income aggregation.
        
        # Calculate indicators directly or retrieve from tracker
        # Note: unemployment_rate, avg_wage, food_avg_price, food_trade_volume, avg_goods_price
        # are typically calculated by the tracker. We need to ensure they are available.
        # For now, we'll assume self.tracker.get_latest_indicators() provides them.
        
        # Get latest indicators from tracker
        tracker_indicators = self.tracker.get_latest_indicators()
        
        total_production = sum(
            agent.current_production
            for agent in self.firms + self.households
            if getattr(agent, "current_production", None) is not None
        )
        total_consumption = sum(
            getattr(agent, "last_tick_food_consumption", 0) for agent in self.households
        )
        total_household_assets = sum(agent.assets for agent in self.households)
        # Total Firm Assets should only include Firms?
        # Correction: The list comprehension above iterates households + firms but checks isinstance Firm.
        # Ideally: sum(firm.assets for firm in self.firms)
        total_firm_assets = sum(firm.assets for firm in self.firms)

        total_food_consumption = sum(
            getattr(agent, "last_tick_food_consumption", 0) for agent in self.households
        )
        total_inventory = sum(
            sum(agent.inventory.values()) for agent in self.households + self.firms
        )
        avg_survival_need = (
            sum(agent.needs["survival"] for agent in self.households)
            / len(self.households)
            if self.households
            else 0.0
        )
        
        # Phase 14-1: Income Aggregation
        total_labor_income = sum(
            getattr(h, "labor_income_this_tick", 0.0) for h in self.households
        )
        total_capital_income = sum(
            getattr(h, "capital_income_this_tick", 0.0) for h in self.households
        )

        # Create DTO using calculated values and values from tracker
        indicator_dto = EconomicIndicatorData(
            run_id=self.run_id, # Use self.run_id directly
            time=self.time,
            unemployment_rate=tracker_indicators.get("unemployment_rate"),
            avg_wage=tracker_indicators.get("avg_wage"),
            food_avg_price=tracker_indicators.get("food_avg_price"),
            food_trade_volume=tracker_indicators.get("food_trade_volume"),
            avg_goods_price=tracker_indicators.get("avg_goods_price"),
            total_production=total_production,
            total_consumption=total_consumption,
            total_household_assets=total_household_assets,
            total_firm_assets=total_firm_assets,
            total_food_consumption=total_food_consumption,
            total_inventory=total_inventory,
            avg_survival_need=avg_survival_need,
            total_labor_income=total_labor_income,
            total_capital_income=total_capital_income,
        )
        self.economic_indicator_buffer.append(indicator_dto)
        
        # 4. Buffer market history
        for market_id, market in self.markets.items():
            if isinstance(market, OrderBookMarket):
                # For OrderBookMarket, we can track multiple items if they exist
                # Currently, each market name corresponds to a good name, or 'labor_market'
                items = list(market.buy_orders.keys()) + list(market.sell_orders.keys())
                # Add historical items too if any
                items = list(set(items))
                
                if not items and market_id in self.config_module.GOODS:
                    items = [market_id]
                for item_id in items:
                    all_bids = market.get_all_bids(item_id)
                    all_asks = market.get_all_asks(item_id)
                    
                    avg_bid = sum(o.price for o in all_bids) / len(all_bids) if all_bids else 0.0
                    avg_ask = sum(o.price for o in all_asks) / len(all_asks) if all_asks else 0.0
                    
                    best_bid = max(o.price for o in all_bids) if all_bids else 0.0
                    worst_bid = min(o.price for o in all_bids) if all_bids else 0.0
                    
                    best_ask = min(o.price for o in all_asks) if all_asks else 0.0
                    worst_ask = max(o.price for o in all_asks) if all_asks else 0.0
                    
                    history_dto = MarketHistoryData(
                        time=self.time,
                        market_id=market_id,
                        item_id=item_id,
                        avg_price=market.get_daily_avg_price(),
                        trade_volume=market.get_daily_volume(),
                        best_ask=best_ask,
                        best_bid=best_bid,
                        avg_ask=avg_ask,
                        avg_bid=avg_bid,
                        worst_ask=worst_ask,
                        worst_bid=worst_bid
                    )
                    self.market_history_buffer.append(history_dto)

        self.logger.debug(
            f"DB_SAVE_END | Finished buffering state for tick {self.time}",
            extra={"tick": self.time, "tags": ["db_buffer"]},
        )

    def _flush_buffers_to_db(self):
        """버퍼에 쌓인 데이터를 데이터베이스에 일괄 저장합니다."""
        if (
            not self.agent_state_buffer
            and not self.transaction_buffer
            and not self.economic_indicator_buffer
            and not self.market_history_buffer
        ):
            return

        self.logger.info(
            f"DB_FLUSH_START | Flushing buffers to DB at tick {self.time}",
            extra={"tick": self.time, "tags": ["db_flush"]},
        )

        if self.agent_state_buffer:
            self.repository.save_agent_states_batch(
                self.agent_state_buffer
            )
            self.agent_state_buffer.clear()

        if self.transaction_buffer:
            self.repository.save_transactions_batch(
                self.transaction_buffer
            )
            self.transaction_buffer.clear()

        if self.economic_indicator_buffer:
            self.repository.save_economic_indicators_batch(
                self.economic_indicator_buffer
            )
            self.economic_indicator_buffer.clear()

        if self.market_history_buffer:
            self.repository.save_market_history_batch(
                self.market_history_buffer
            )
            self.market_history_buffer.clear()

        self.logger.info(
            f"DB_FLUSH_END | Finished flushing buffers to DB at tick {self.time}",
            extra={"tick": self.time, "tags": ["db_flush"]},
        )

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

        market_data = self._prepare_market_data(self.tracker)
        
        # Phase 4: Welfare Check
        # run_welfare_check(agents, market_data, current_tick)
        # Note: market_data needs 'total_production' (GDP) for stimulus check
        latest_gdp = self.tracker.get_latest_indicators().get("total_production", 0.0)
        market_data["total_production"] = latest_gdp # Inject for Government
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
                work_aggressiveness = action_vector.work_aggressiveness
                max_work_hours = self.config_module.MAX_WORK_HOURS
                shopping_hours = getattr(self.config_module, "SHOPPING_HOURS", 2.0)
                hours_per_tick = getattr(self.config_module, "HOURS_PER_TICK", 24.0)

                work_hours = work_aggressiveness * max_work_hours
                leisure_hours = max(0.0, hours_per_tick - work_hours - shopping_hours)

                household_time_allocation[household.id] = leisure_hours
                self.household_time_allocation[household.id] = leisure_hours

                for order in household_orders:
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

        for household in self.households:
             if household.is_active:
                 # 1. Consumption
                 consumed_items = household.decide_and_consume(self.time, consumption_market_data)

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

        # --- Mitosis Processing (Agent Evolution) ---
        # Inserted after consumption reset (which is actually after consumption logic in original flow)
        # Spec says: After consumption counter reset, Before _handle_agent_lifecycle

        # NOTE: Original code had consumption counter reset at the END of run_tick.
        # But for Mitosis to see updated needs/assets after consumption, it should be here or after.
        # The spec says "After consumption counter reset". This implies we might need to move the reset earlier
        # or do Mitosis at the end. However, usually counters are reset for the *next* tick.
        # Let's put Mitosis here, before lifecycle management.

        new_children = []
        # Count active households for dynamic threshold
        current_pop = len([h for h in self.households if h.is_active])

        for household in list(self.households): # Iterate copy in case of modification issues
            if not household.is_active:
                continue

            child = household.check_mitosis(
                current_population=current_pop,
                target_population=self.config_module.TARGET_POPULATION,
                new_id=self.next_agent_id
            )

            if child:
                self.next_agent_id += 1
                new_children.append((household, child))
                current_pop += 1

        # Register new children and inherit brains
        for parent, child in new_children:
            self.households.append(child)
            self.agents[child.id] = child
            child.decision_engine.markets = self.markets
            child.decision_engine.goods_data = self.goods_data
            # self.ai_training_manager.agents references self.households, so no need to append again
            # self.ai_training_manager.agents.append(child)

            # Brain Inheritance (Q-Table + Personality)
            self.ai_training_manager.inherit_brain(parent, child)

            # Update Stock Market Shareholder Registry
            if self.stock_market:
                for firm_id, qty in child.shares_owned.items():
                    self.stock_market.update_shareholder(child.id, firm_id, qty)

        # ---------------------------------------------------------
        # Activate Farm Logic (Production & Needs/Wages)
        # ---------------------------------------------------------
        for firm in self.firms:
             if firm.is_active:
                 firm.produce(self.time)
                 # Phase 4: Pass government and market_data for income tax withholding
                 # Phase 8-B: Pass reflux_system for expense capture
                 firm.update_needs(self.time, self.government, market_data, self.reflux_system)
                 
                 # 2a. 법인세(Corporate Tax) 징수 (이익이 발생한 경우)
                 if firm.is_active and firm.current_profit > 0:
                     corporate_tax_rate = getattr(self.config_module, "CORPORATE_TAX_RATE", 0.2)
                     tax_amount = firm.current_profit * corporate_tax_rate
                     firm.assets -= tax_amount
                     self.government.collect_tax(tax_amount, "corporate_tax", firm.id, self.time)

        # Update tracker with the latest data after transactions and consumption
        self.tracker.track(self.time, self.households, self.firms, self.markets)

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
        self._check_entrepreneurship()

        # Phase 5: Finalize Government Stats for the tick
        self.government.finalize_tick(self.time)

        # Phase 8-B: Distribute Reflux Funds (Service Sector Income)
        # Must happen before state save so households see the income
        self.reflux_system.distribute(self.households)

        # Save all state at the end of the tick
        self._save_state_to_db(all_transactions)

        # Flush buffers to DB periodically
        if self.time % self.batch_save_interval == 0:
            self._flush_buffers_to_db()

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

        return {
            "time": self.time,
            "goods_market": goods_market_data,
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
        """발생한 거래들을 처리하여 에이전트의 자산, 재고, 고용 상태 등을 업데이트합니다."""
        for tx in transactions:
            buyer = self.agents.get(tx.buyer_id)
            seller = self.agents.get(tx.seller_id)

            if not buyer or not seller:
                continue

            trade_value = tx.quantity * tx.price
            sales_tax_rate = getattr(self.config_module, "SALES_TAX_RATE", 0.05)
            income_tax_rate = getattr(self.config_module, "INCOME_TAX_RATE", 0.1)

            # --- 1. 기본 자산 이동 및 세금 처리 ---
            if tx.transaction_type in ["goods", "stock"]:
                # 거래세(부가가치세) 적용: 매수자가 추가로 지불
                tax_amount = trade_value * sales_tax_rate
                buyer.assets -= (trade_value + tax_amount)
                seller.assets += trade_value
                self.government.collect_tax(tax_amount, f"sales_tax_{tx.transaction_type}", buyer.id, self.time)
            
            elif tx.transaction_type in ["labor", "research_labor"]:
                # 소득세 적용 (INCOME_TAX_PAYER 설정에 따름)
                tax_payer = getattr(self.config_module, "INCOME_TAX_PAYER", "HOUSEHOLD")

                # Phase 4: Progressive Tax
                # Calculate Survival Cost for Tax Bracket
                avg_food_price = 0.0
                goods_market_data = self._prepare_market_data(self.tracker).get("goods_market", {})
                if "basic_food_current_sell_price" in goods_market_data:
                    avg_food_price = goods_market_data["basic_food_current_sell_price"]
                else:
                    avg_food_price = getattr(self.config_module, "GOODS_INITIAL_PRICE", {}).get("basic_food", 5.0)
                daily_food_need = getattr(self.config_module, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 1.0)
                survival_cost = max(avg_food_price * daily_food_need, 10.0)

                tax_amount = self.government.calculate_income_tax(trade_value, survival_cost)
                
                if tax_payer == "FIRM":
                    # 기업이 세금을 추가로 납부 (가계는 trade_value 전액 수령)
                    buyer.assets -= (trade_value + tax_amount)
                    seller.assets += trade_value
                    self.government.collect_tax(tax_amount, "income_tax_firm", buyer.id, self.time)
                else:
                    # 가계가 세금을 납부 (원천징수, 기본값)
                    buyer.assets -= trade_value
                    seller.assets += (trade_value - tax_amount)
                    self.government.collect_tax(tax_amount, "income_tax_household", seller.id, self.time)
            
            else:
                # 기타 거래 (대출 등) - 현재는 세금 없음
                buyer.assets -= trade_value
                seller.assets += trade_value

            # --- 2. 유형별 특수 로직 ---
            if (
                tx.transaction_type == "labor"
                or tx.transaction_type == "research_labor"
            ):
                if isinstance(seller, Household):
                    if (
                        seller.is_employed
                        and seller.employer_id is not None
                        and seller.employer_id != buyer.id
                    ):
                        previous_employer = self.agents.get(seller.employer_id)
                        if (
                            isinstance(previous_employer, Firm)
                            and seller in previous_employer.employees
                        ):
                            previous_employer.employees.remove(seller)

                    seller.is_employed = True
                    seller.employer_id = buyer.id
                    seller.current_wage = tx.price # Store wage
                    seller.needs["labor_need"] = 0.0

                    # Track Labor Income (Net) - for first hiring, assuming payment
                    # Note: Usually actual payment is in Firm.update_needs.
                    # But if this transaction involves money transfer (it does below),
                    # we should record it.
                    # However, logic above:
                    # buyer.assets -= ...
                    # seller.assets += (trade_value - tax_amount)
                    # So seller received net income.
                    if hasattr(seller, "labor_income_this_tick"):
                        net_income = trade_value - tax_amount
                        seller.labor_income_this_tick += net_income

                if isinstance(buyer, Firm):
                    if seller not in buyer.employees:
                        buyer.employees.append(seller)
                    buyer.employee_wages[seller.id] = tx.price # Store wage
                    buyer.cost_this_turn += trade_value

                    if tx.transaction_type == "research_labor":
                        research_skill = seller.skills.get(
                            "research", Skill("research")
                        ).value
                        buyer.productivity_factor += (
                            research_skill
                            * self.config_module.RND_PRODUCTIVITY_MULTIPLIER
                        )

            elif tx.transaction_type == "dividend":
                # Firm (Seller) pays Household (Buyer)
                # Correction: distribute_dividends sets Seller=Firm, Buyer=Household.
                # Standard logic above: Buyer pays Seller.
                # We need REVERSE logic for Dividend.

                # Firm (Seller) pays Dividend
                seller.assets -= trade_value

                # Household (Buyer) receives Dividend
                buyer.assets += trade_value

                if isinstance(buyer, Household) and hasattr(buyer, "capital_income_this_tick"):
                    buyer.capital_income_this_tick += trade_value

            elif tx.transaction_type == "goods":
                good_info = self.config_module.GOODS.get(tx.item_id, {})
                is_service = good_info.get("is_service", False)

                if is_service:
                    # 서비스인 경우 인벤토리를 거치지 않고 즉시 소비 처리
                    if isinstance(buyer, Household):
                        buyer.consume(tx.item_id, tx.quantity, self.time)
                else:
                    seller.inventory[tx.item_id] = max(
                        0, seller.inventory.get(tx.item_id, 0) - tx.quantity
                    )

                    # WO-030: Route Raw Materials to input_inventory
                    is_raw_material = tx.item_id in getattr(self.config_module, "RAW_MATERIAL_SECTORS", [])

                    if is_raw_material and isinstance(buyer, Firm):
                        # Add to input_inventory
                        buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity
                        # No quality tracking for input_inventory yet in this spec
                    else:
                        # Regular inventory update
                        # Phase 15: Transfer Quality (Weighted Average)
                        current_qty = buyer.inventory.get(tx.item_id, 0)

                        # Determine existing quality
                        existing_quality = 1.0
                        if isinstance(buyer, Household):
                            existing_quality = buyer.inventory_quality.get(tx.item_id, 1.0)
                        elif isinstance(buyer, Firm):
                            existing_quality = buyer.inventory_quality.get(tx.item_id, 1.0)

                        # Transaction Quality (passed from Market)
                        tx_quality = tx.quality if hasattr(tx, 'quality') else 1.0

                        # Calculate new WA Quality
                        total_new_qty = current_qty + tx.quantity
                        new_avg_quality = ((current_qty * existing_quality) + (tx.quantity * tx_quality)) / total_new_qty

                        # Update Buyer Quality
                        if isinstance(buyer, Household):
                            buyer.inventory_quality[tx.item_id] = new_avg_quality
                        elif isinstance(buyer, Firm):
                            buyer.inventory_quality[tx.item_id] = new_avg_quality

                        # Update Quantity
                        buyer.inventory[tx.item_id] = total_new_qty

                if isinstance(seller, Firm):
                    seller.revenue_this_turn += trade_value
                
                if isinstance(buyer, Household):
                    # 서비스는 consume()에서 이미 처리되었으므로 비서비스 상품만 여기서 추가
                    if not is_service:
                        buyer.current_consumption += tx.quantity
                        if tx.item_id == "basic_food":
                            buyer.current_food_consumption += tx.quantity

                # Track Sales Volume for Solvency Logic
                if isinstance(seller, Firm):
                    seller.sales_volume_this_tick += tx.quantity

            elif tx.transaction_type == "stock":
                # 주식 거래 처리
                # item_id 형식: "stock_{firm_id}"
                firm_id = int(tx.item_id.split("_")[1])
                
                # 매도자의 주식 감소
                if isinstance(seller, Household):
                    current_shares = seller.shares_owned.get(firm_id, 0)
                    seller.shares_owned[firm_id] = max(0, current_shares - tx.quantity)
                    if seller.shares_owned[firm_id] == 0:
                        del seller.shares_owned[firm_id]
                elif isinstance(seller, Firm) and seller.id == firm_id:
                    # 자사주 매각
                    seller.treasury_shares = max(0, seller.treasury_shares - tx.quantity)
                
                # 매수자의 주식 증가
                if isinstance(buyer, Household):
                    current_shares = buyer.shares_owned.get(firm_id, 0)
                    buyer.shares_owned[firm_id] = current_shares + tx.quantity
                elif isinstance(buyer, Firm) and buyer.id == firm_id:
                    # 자사주 매입 (Buyback)
                    buyer.treasury_shares += tx.quantity

                # [Mitosis] Update Shareholder Registry in StockMarket
                if self.stock_market:
                    # Update Seller
                    if isinstance(seller, Household):
                        self.stock_market.update_shareholder(seller.id, firm_id, seller.shares_owned.get(firm_id, 0))
                    # Update Buyer
                    if isinstance(buyer, Household):
                        self.stock_market.update_shareholder(buyer.id, firm_id, buyer.shares_owned.get(firm_id, 0))


    def spawn_firm(self, founder_household: "Household") -> Optional["Firm"]:
        """
        부유한 가계가 새로운 기업을 설립합니다.

        Args:
            founder_household: 창업주 가계 에이전트

        Returns:
            생성된 Firm 객체 또는 None (실패 시)
        """
        startup_cost = getattr(self.config_module, "STARTUP_COST", 30000.0)

        # 1. 자본 차감
        # Using assets as cash proxy
        if founder_household.assets < startup_cost:
            return None
        founder_household.assets -= startup_cost

        # 2. 새 기업 ID 생성
        max_id = max([a.id for a in self.agents.values()], default=0)
        new_firm_id = max_id + 1

        # 3. 업종 선택 (Blue Ocean Strategy)
        # Refactored: Dynamic list from config
        specializations = list(self.config_module.GOODS.keys())
        is_visionary = False
        sector = "OTHER"

        # WO-023: Visionary Mutation (Configurable)
        mutation_rate = getattr(self.config_module, "VISIONARY_MUTATION_RATE", 0.05)
        if random.random() < mutation_rate:
            is_visionary = True
            
        # Blue Ocean Logic: If Visionary, look for empty markets
        if is_visionary:
            active_specs = {f.specialization for f in self.firms if f.is_active}
            # Find any specialization not in active_specs
            potential_blue_oceans = [s for s in specializations if s not in active_specs]
            
            if potential_blue_oceans:
                specialization = random.choice(potential_blue_oceans)
            else:
                # If no blue ocean, fallback to consumer_goods if defined, else random
                if "consumer_goods" in specializations:
                     specialization = "consumer_goods"
                else:
                     specialization = random.choice(specializations)
        else:
             # Standard Entrepreneur: Random Choice
             specialization = random.choice(specializations)
             
        # Refactored: Map Specialization to Sector using Config
        goods_config = self.config_module.GOODS.get(specialization, {})
        sector = goods_config.get("sector", "OTHER")

        # WO-030: Increase Initial Capital for Manufacturing Firms (Input Constraints)
        has_inputs = bool(goods_config.get("inputs"))
        if has_inputs:
             startup_cost *= 1.5

        # 4. AI 설정
        from simulation.ai.firm_ai import FirmAI
        from simulation.ai.service_firm_ai import ServiceFirmAI
        from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine

        value_orientation = random.choice([
            self.config_module.VALUE_ORIENTATION_WEALTH_AND_NEEDS,
            self.config_module.VALUE_ORIENTATION_NEEDS_AND_GROWTH,
        ])
        # Use ai_trainer instead of ai_manager
        ai_decision_engine = self.ai_trainer.get_engine(value_orientation)

        is_service = specialization in getattr(self.config_module, "SERVICE_SECTORS", [])

        if is_service:
            firm_ai = ServiceFirmAI(agent_id=str(new_firm_id), ai_decision_engine=ai_decision_engine)
        else:
            firm_ai = FirmAI(agent_id=str(new_firm_id), ai_decision_engine=ai_decision_engine)

        firm_decision_engine = AIDrivenFirmDecisionEngine(firm_ai, self.config_module, self.logger)

        # 5. Firm 생성
        if is_service:
            new_firm = ServiceFirm(
                id=new_firm_id,
                initial_capital=startup_cost,
                initial_liquidity_need=getattr(self.config_module, "INITIAL_FIRM_LIQUIDITY_NEED_MEAN", 50.0),
                specialization=specialization,
                productivity_factor=random.uniform(8.0, 12.0),
                decision_engine=firm_decision_engine,
                value_orientation=value_orientation,
                config_module=self.config_module,
                logger=self.logger,
                sector=sector,
                is_visionary=is_visionary,
            )
        else:
            new_firm = Firm(
                id=new_firm_id,
                initial_capital=startup_cost,
                initial_liquidity_need=getattr(self.config_module, "INITIAL_FIRM_LIQUIDITY_NEED_MEAN", 50.0),
                specialization=specialization,
                productivity_factor=random.uniform(8.0, 12.0),
                decision_engine=firm_decision_engine,
                value_orientation=value_orientation,
                config_module=self.config_module,
                logger=self.logger,
                sector=sector,
                is_visionary=is_visionary,
            )
        new_firm.founder_id = founder_household.id
        # Set loan market if available in simulation
        if "loan_market" in self.markets:
            new_firm.decision_engine.loan_market = self.markets["loan_market"]

        # 6. 리스트에 추가
        self.firms.append(new_firm)
        self.agents[new_firm.id] = new_firm

        # Add to AI training manager
        self.ai_training_manager.agents.append(new_firm)

        self.logger.info(
            f"STARTUP | Household {founder_household.id} founded Firm {new_firm_id} "
            f"(Specialization: {specialization}, Capital: {startup_cost})",
            extra={"tick": self.time, "agent_id": new_firm_id, "tags": ["entrepreneurship"]}
        )

        return new_firm

    def _check_entrepreneurship(self):
        """
        매 틱마다 창업 조건을 확인하고 신규 기업을 생성합니다.
        """
        min_firms = getattr(self.config_module, "MIN_FIRMS_THRESHOLD", 5)
        startup_cost = getattr(self.config_module, "STARTUP_COST", 15000.0)
        spirit = getattr(self.config_module, "ENTREPRENEURSHIP_SPIRIT", 0.05)
        capital_multiplier = getattr(self.config_module, "STARTUP_CAPITAL_MULTIPLIER", 1.5)

        active_firms_count = sum(1 for f in self.firms if f.is_active)

        # Hard Trigger: 기업 수가 최소치 이하
        if active_firms_count < min_firms:
            trigger_probability = 0.5  # 50% 창업 확률 (위기 상황)
        else:
            trigger_probability = spirit  # 일반 창업 확률 (5%)

        # 부유한 가계 필터링 (use 'assets' property as cash proxy, but 'cash' property might not exist on household directly in this version? Household inherits from BaseAgent which has 'assets'. Instructions used 'cash'. Household code uses 'assets'. 'cash' is likely alias or just assets.)
        # Checking Household code: it uses self.assets. It doesn't seem to have 'cash' property.
        # I will replace .cash with .assets as per standard agent.

        wealthy_households = [
            h for h in self.households
            if h.is_active and h.assets > startup_cost * capital_multiplier
        ]

        import random
        for household in wealthy_households:
            if random.random() < trigger_probability:
                # Use assets instead of cash for spawn_firm call inside too
                # Need to update spawn_firm implementation to use assets if cash is not available.
                # Actually, I'll update spawn_firm implementation above to use assets.
                self.spawn_firm(household)
                break  # 한 틱에 하나씩만 창업

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
            # 2a. 상속세 징수 (잔여 자산 정부 귀속)
            inheritance_tax_rate = getattr(self.config_module, "INHERITANCE_TAX_RATE", 1.0)
            tax_amount = household.assets * inheritance_tax_rate
            self.government.collect_tax(tax_amount, "inheritance_tax", household.id, self.time)
            
            self.logger.info(
                f"HOUSEHOLD_LIQUIDATION | Household {household.id} liquidated. "
                f"Tax Collected: {tax_amount:.2f}, Inventory: {sum(household.inventory.values()):.2f}",
                extra={"agent_id": household.id, "tags": ["liquidation", "tax"]}
            )
            
            household.assets = 0.0
            household.inventory.clear()
            household.shares_owned.clear()

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
