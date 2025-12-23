from __future__ import annotations
from typing import List, Dict, Any
import logging
import hashlib

from simulation.models import Transaction
from simulation.core_agents import Household, Skill
from simulation.firms import Firm
from simulation.markets.order_book_market import OrderBookMarket
from simulation.core_markets import Market
from simulation.agents.bank import Bank
from simulation.loan_market import LoanMarket
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.ai_model import AIEngineRegistry
from simulation.ai.ai_training_manager import AITrainingManager

# Updated import to use the repository pattern
# Updated import to use the repository pattern
from simulation.db.repository import SimulationRepository
from simulation.dtos import (
    AgentStateData,
    TransactionData,
    EconomicIndicatorData,
    AIDecisionData,
    MarketHistoryData,
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
            id=self.next_agent_id, initial_assets=self.config_module.INITIAL_BANK_ASSETS
        )
        self.agents[self.bank.id] = self.bank
        self.next_agent_id += 1

        self.markets: Dict[str, Market] = {
            good_name: OrderBookMarket(market_id=good_name)
            for good_name in self.config_module.GOODS
        }
        self.markets["labor"] = OrderBookMarket(market_id="labor")
        self.markets["loan_market"] = LoanMarket(
            market_id="loan_market", bank=self.bank, config_module=self.config_module
        )

        for agent in self.households + self.firms:
            agent.decision_engine.markets = self.markets
            agent.decision_engine.goods_data = self.goods_data
            if isinstance(agent, Firm):
                agent.config_module = self.config_module

        self.repository = repository
        self.tracker = EconomicIndicatorTracker(config_module=config_module)
        self.ai_training_manager = AITrainingManager(
            self.households, self.config_module
        )

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
            )

            if isinstance(agent, Household):
                agent_dto.agent_type = "household"
                agent_dto.is_employed = agent.is_employed
                agent_dto.employer_id = agent.employer_id
                agent_dto.needs_survival = agent.needs.get("survival", 0)
                agent_dto.needs_labor = agent.needs.get("labor_need", 0)
                agent_dto.inventory_food = agent.inventory.get("food", 0)
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
        indicators = self.tracker.get_latest_indicators()
        if indicators:
            # indicators is a dict, convert to DTO
            indicator_dto = EconomicIndicatorData(
                run_id=self.run_id,
                time=self.time,
                unemployment_rate=indicators.get("unemployment_rate"),
                avg_wage=indicators.get("avg_wage"),
                food_avg_price=indicators.get("food_avg_price"),
                food_trade_volume=indicators.get("food_trade_volume"),
                avg_goods_price=indicators.get("avg_goods_price"),
                total_production=indicators.get("total_production"),
                total_consumption=indicators.get("total_consumption"),
                total_household_assets=indicators.get("total_household_assets"),
                total_firm_assets=indicators.get("total_firm_assets"),
                total_food_consumption=indicators.get("total_food_consumption"),
                total_inventory=indicators.get("total_inventory"),
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

        for firm in self.firms:
            firm.hires_last_tick = 0

        for market in self.markets.values():
            if isinstance(market, OrderBookMarket):
                market.clear_market_for_next_tick()

        market_data = self._prepare_market_data(self.tracker)
        
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
                firm_orders, action_vector = firm.make_decision(self.markets, self.goods_data, market_data, self.time)
                for order in firm_orders:
                    target_market: Market | None = self.markets.get(order.market_id)
                    if target_market:
                        target_market.place_order(order, self.time)

        household_pre_states = {}
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
                    self.markets, self.goods_data, market_data, self.time
                )
                for order in household_orders:
                    household_target_market: Market | None = self.markets.get(order.market_id)
                    if household_target_market:
                        household_target_market.place_order(order, self.time)
                    else:
                        self.logger.warning(
                            f"Market '{order.market_id}' not found for order from agent {household.id}",
                            extra={"tick": self.time},
                        )

        for market in self.markets.values():
            if isinstance(market, OrderBookMarket):
                all_transactions.extend(market.match_orders(self.time))

        self._process_transactions(all_transactions)
        print(f"DEBUG: Tick {self.time} Processed {len(all_transactions)} transactions. Buyers: {[tx.buyer_id for tx in all_transactions[:5]]}")

        # ---------------------------------------------------------
        # Activate Consumption Logic
        # ---------------------------------------------------------
        # After transactions, households have goods in inventory.
        # Now they must consume them to satisfy needs.
        for household in self.households:
             if household.is_active:
                 household.decide_and_consume(self.time)

        # ---------------------------------------------------------
        # Activate Farm Logic (Production & Needs/Wages)
        # ---------------------------------------------------------
        for firm in self.firms:
             if firm.is_active:
                 firm.produce(self.time)
                 firm.update_needs(self.time)

        # Update tracker with the latest data after transactions and consumption
        self.tracker.track(self.time, self.households, self.firms, self.markets)

        for firm in self.firms:
            if firm.is_active and firm.id in firm_pre_states:
                post_state_data = firm.get_agent_data()
                agent_data = firm.get_agent_data()
                market_data = self._prepare_market_data(self.tracker)
                
                # Calculate Reward
                reward = firm.decision_engine.ai_engine._calculate_reward(
                    firm.get_pre_state_data(), post_state_data, agent_data, market_data
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

        # Save all state at the end of the tick
        self._save_state_to_db(all_transactions)

        # Flush buffers to DB periodically
        if self.time % self.batch_save_interval == 0:
            self._flush_buffers_to_db()

        self.logger.info(
            f"--- Ending Tick {self.time} ---",
            extra={"tick": self.time, "tags": ["tick_end"]},
        )

    def _prepare_market_data(self, tracker: EconomicIndicatorTracker) -> Dict[str, Any]:
        """현재 틱의 시장 데이터를 에이전트의 의사결정을 위해 준비합니다."""
        goods_market_data = {}
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

        goods_market_data["labor"] = {
            "avg_wage": avg_wage,
            "best_wage_offer": best_wage_offer
        }

        total_price = 0.0
        count = 0.0
        for good_name in self.config_module.GOODS:
            price = goods_market_data.get(f"{good_name}_current_sell_price")
            if price is not None:
                total_price += price
                count += 1

        avg_goods_price_for_market_data = total_price / count if count > 0 else 10.0

        return {
            "time": self.time,
            "goods_market": goods_market_data,
            "loan_market": {"interest_rate": self.config_module.LOAN_INTEREST_RATE},
            "all_households": self.households,
            "avg_goods_price": avg_goods_price_for_market_data,
        }

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

            buyer.assets -= trade_value
            seller.assets += trade_value

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

            elif tx.transaction_type == "goods":
                seller.inventory[tx.item_id] = max(
                    0, seller.inventory.get(tx.item_id, 0) - tx.quantity
                )
                buyer.inventory[tx.item_id] = (
                    buyer.inventory.get(tx.item_id, 0) + tx.quantity
                )
                if isinstance(seller, Firm):
                    seller.revenue_this_turn += trade_value
                if isinstance(buyer, Household):
                    buyer.current_consumption += tx.quantity
                    if tx.item_id == "basic_food":
                        buyer.current_food_consumption += tx.quantity

    def _handle_agent_lifecycle(self) -> None:
        """비활성화된 에이전트를 시뮬레이션에서 제거하고 고용 상태를 업데이트합니다."""
        inactive_firms = [f for f in self.firms if not f.is_active]
        for firm in inactive_firms:
            for employee in firm.employees:
                if employee.is_active:
                    employee.is_employed = False
                    employee.employer_id = None
            firm.employees = []

        self.households = [h for h in self.households if h.is_active]
        self.firms = [f for f in self.firms if f.is_active]

        self.agents = {agent.id: agent for agent in self.households + self.firms}
        self.agents[self.bank.id] = self.bank

        for firm in self.firms:
            firm.employees = [
                emp for emp in firm.employees if emp.is_active and emp.id in self.agents
            ]
