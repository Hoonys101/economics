from __future__ import annotations
from typing import List, Dict, Any
import logging

from simulation.models import Transaction
from simulation.core_agents import Household, Skill
from simulation.firms import Firm
from simulation.markets.order_book_market import OrderBookMarket
from simulation.core_markets import Market
from simulation.agents.bank import Bank
from simulation.loan_market import LoanMarket
from simulation.metrics.economic_tracker import EconomicIndicatorTracker # Import EconomicIndicatorTracker
from simulation.base_agent import BaseAgent # Import BaseAgent
from simulation.ai_model import AIEngineRegistry

# New imports for database
from simulation.db_manager import DBManager

logger = logging.getLogger(__name__)

class Simulation:
    """경제 시뮬레이션의 전체 흐름을 관리하고 조정하는 핵심 엔진 클래스.

    가계, 기업, 시장, 은행 등 모든 시뮬레이션 구성 요소를 초기화하고,
    각 시뮬레이션 틱(tick)마다 에이전트의 의사결정, 시장 거래, 생산 및 소비 활동을 순차적으로 실행합니다.
    """
    def __init__(self, households: List[Household], firms: List[Firm], ai_trainer: AIEngineRegistry, db_manager: DBManager, config_module: Any, logger: logging.Logger | None = None) -> None:
        """Simulation 클래스를 초기화합니다.

        Args:
            households (List[Household]): 시뮬레이션에 참여할 가계 에이전트 리스트.
            firms (List[Firm]): 시뮬레이션에 참여할 기업 에이전트 리스트.
            ai_trainer (AITrainingManager): AI 모델 훈련을 관리하는 인스턴스.
            db_manager (DBManager): 데이터 저장을 위한 DBManager 인스턴스.
            config_module (Any): 시뮬레이션 설정 모듈.
            logger (logging.Logger, optional): 로깅을 위한 Logger 인스턴스. 기본값은 None.
        """
        self.logger = logger if logger else logging.getLogger(__name__)
        self.households = households
        self.firms = firms
        self.agents: Dict[int, Any] = {}
        for h in households:
            self.agents[h.id] = h
        for f in firms:
            self.agents[f.id] = f
        self.next_agent_id = len(households) + len(firms)

        self.ai_trainer = ai_trainer
        self.config_module = config_module # Store config_module
        self.time: int = 0

        self.bank = Bank(id=self.next_agent_id, initial_assets=self.config_module.INITIAL_BANK_ASSETS)
        self.agents[self.bank.id] = self.bank
        self.next_agent_id += 1

        # Create a market for each good, plus labor and loan markets
        self.markets: Dict[str, Market] = {
            good_name: OrderBookMarket(market_id=good_name)
            for good_name in self.config_module.GOODS
        }
        self.markets['labor_market'] = OrderBookMarket(market_id='labor_market')
        self.markets['loan_market'] = LoanMarket(market_id='loan_market', bank=self.bank, config_module=self.config_module)

        # Pass the entire markets dictionary to each agent's decision engine
        for agent in self.households + self.firms:
            agent.decision_engine.markets = self.markets
            # Pass config_module to Firm constructor
            if isinstance(agent, Firm): # Only apply to Firm agents
                agent.config_module = self.config_module
        self.db_manager = db_manager # Use passed-in db_manager
        self.tracker = EconomicIndicatorTracker(config_module=config_module) # Store tracker instance

        # Save simulation run details
        import hashlib
        config_content = str(self.config_module.__dict__)
        config_hash = hashlib.sha256(config_content.encode()).hexdigest()
        self.run_id = self.db_manager.save_simulation_run(
            config_hash=config_hash,
            description="Economic simulation run with DB storage"
        )
        self.logger.info(f"Simulation run started with run_id: {self.run_id}", extra={'run_id': self.run_id})

    def finalize_simulation(self):
        """
        시뮬레이션 종료 시 DBManager 연결을 닫고, 시뮬레이션 종료 시간을 기록합니다.
        """
        self.db_manager.update_simulation_run_end_time(self.run_id)
        self.db_manager.close()
        self.logger.info("Simulation finalized and DBManager connection closed.")

    def run_tick(self) -> None:
        self.time += 1
        self.logger.info(f"--- Starting Tick {self.time} ---", extra={'tick': self.time, 'tags': ['tick_start']})

        # Reset hires_last_tick for all firms
        for firm in self.firms:
            firm.hires_last_tick = 0

        # 0. Clear markets for the new tick
        for market in self.markets.values():
            if isinstance(market, OrderBookMarket):
                market.clear_market_for_next_tick()

        market_data = self._prepare_market_data(self.tracker)
        all_transactions: List[Transaction] = []

        # 1. Firms make decisions and place orders (SELL orders for goods)
        for firm in self.firms:
            if firm.is_active:
                firm_orders = firm.make_decision(market_data, self.time)
                for order in firm_orders:
                    market = self.markets.get(order.market_id)
                    if market:
                        market.place_order(order, self.time)

        # 2. Households make decisions and place orders (BUY orders for goods)
        household_pre_states = {}
        for household in self.households:
            if household.is_active:
                # Store pre-decision states for learning
                pre_strategic_state = household.decision_engine.ai_engine._get_strategic_state(household.get_agent_data(), market_data)
                pre_tactical_state = household.decision_engine.ai_engine._get_tactical_state(household.decision_engine.ai_engine.chosen_intention, household.get_agent_data(), market_data) # chosen_intention will be set by decide_and_learn
                
                household_pre_states[household.id] = {
                    'pre_strategic_state': pre_strategic_state,
                    'pre_tactical_state': pre_tactical_state,
                    'chosen_intention': household.decision_engine.ai_engine.chosen_intention, # Store current chosen_intention
                    'chosen_tactic': household.decision_engine.ai_engine.last_chosen_tactic # Store current chosen_tactic
                }

                household_orders, chosen_tactic = household.make_decision(self.markets, self.goods_data, market_data, self.time)
                
                for order in household_orders:
                    # Get market from the order's market_id
                    market = self.markets.get(order.market_id)
                    if market:
                        market.place_order(order, self.time)
                    else:
                        self.logger.warning(f"Market '{order.market_id}' not found for order from agent {household.id}", extra={'tick': self.time})

        # 3. Match orders and execute transactions for all markets
        for market in self.markets.values():
            if isinstance(market, OrderBookMarket):
                all_transactions.extend(market.match_and_execute_orders(self.time))

        self.logger.debug(f"PROCESS_TRANSACTIONS_START | Tick {self.time}, Processing {len(all_transactions)} transactions.", extra={'tick': self.time, 'tags': ['debug_transaction']})
        for tx in all_transactions:
            self.logger.debug(f"TRANSACTION_DETAIL | Tick {self.time}, Type: {tx.transaction_type}, Item: {tx.item_id}, Price: {tx.price}, Quantity: {tx.quantity}", extra={'tick': self.time, 'tags': ['debug_transaction']})
        self._process_transactions(all_transactions)
        self.logger.debug(f"PROCESS_TRANSACTIONS_END | Tick {self.time}, Finished processing transactions.", extra={'tick': self.time, 'tags': ['debug_transaction']})

        # --- AI Learning Update for Households ---
        for household in self.households:
            if household.is_active and household.id in household_pre_states:
                pre_states = household_pre_states[household.id]
                pre_strategic_state = pre_states['pre_strategic_state']
                pre_tactical_state = pre_states['pre_tactical_state']
                chosen_intention = pre_states['chosen_intention']
                chosen_tactic = pre_states['chosen_tactic']

                # Get post-decision states for reward calculation and learning
                post_state_data = household.get_agent_data()
                agent_data = household.get_agent_data()
                market_data = self._prepare_market_data(self.tracker) # Re-prepare market data for post-transaction view

                # Calculate reward
                reward = household.decision_engine.ai_engine._calculate_reward(
                    household.get_pre_state_data(), post_state_data, agent_data, market_data
                )

                # Get next states for learning update
                next_strategic_state = household.decision_engine.ai_engine._get_strategic_state(agent_data, market_data)
                next_tactical_state = household.decision_engine.ai_engine._get_tactical_state(chosen_intention, agent_data, market_data)

                # Update learning
                household.decision_engine.ai_engine.update_learning(
                    strategic_state=pre_strategic_state,
                    chosen_intention=chosen_intention,
                    tactical_state=pre_tactical_state,
                    chosen_tactic=chosen_tactic,
                    reward=reward,
                    next_strategic_state=next_strategic_state,
                    next_tactical_state=next_tactical_state
                )
                self.db_manager.save_ai_decision(
                    run_id=self.run_id,
                    tick=self.time,
                    agent_id=household.id,
                    decision_type=chosen_intention.name if chosen_intention is not None else "UNKNOWN_DECISION", # Or a more specific decision type if available
                    decision_details={
                        "pre_strategic_state": pre_strategic_state,
                        "pre_tactical_state": pre_tactical_state,
                        "chosen_tactic": chosen_tactic.name if chosen_tactic else None, # Store tactic name
                        "next_strategic_state": next_strategic_state,
                        "next_tactical_state": next_tactical_state
                    },
                    predicted_reward=None, # If AI engine provides this, use it
                    actual_reward=reward
                )
                self.logger.debug(f"HOUSEHOLD_LEARNING_UPDATE | Household {household.id} updated learning. Reward: {reward:.2f}", extra={'tick': self.time, 'agent_id': household.id, 'reward': reward, 'tags': ['ai_learning']})
        # --- End AI Learning Update ---

        # --- GEMINI_PROPOSED_ADDITION_START: Firm Profit Calculation and History Update ---
        for firm in self.firms:
            if firm.is_active:
                current_profit = firm.revenue_this_turn - firm.expenses_this_tick
                firm.profit_history.append(current_profit)
                firm.revenue_this_turn = 0.0 # Reset for next tick
                firm.expenses_this_tick = 0.0 # Reset for next tick
                self.logger.debug(f"FIRM_PROFIT_UPDATE | Firm {firm.id} profit this tick: {current_profit:.2f}, profit_history: {list(firm.profit_history)}", extra={'tick': self.time, 'agent_id': firm.id, 'current_profit': current_profit, 'profit_history': list(firm.profit_history), 'tags': ['firm_profit']})
        # --- GEMINI_PROPOSED_ADDITION_END ---

        # --- Save transactions to DB ---
        for tx in all_transactions:
            self.db_manager.save_transaction(
                run_id=self.run_id,
                tick=self.time,
                buyer_id=tx.buyer_id,
                seller_id=tx.seller_id,
                item_id=tx.item_id,
                quantity=tx.quantity,
                price=tx.price,
                transaction_type=tx.transaction_type,
                loan_id=getattr(tx, 'loan_id', None) # Assuming loan_id might be an attribute for loan transactions
            )
        # --- End Save transactions to DB ---



        # 4. Firms produce goods
        for firm in self.firms:
            if firm.is_active:
                firm.produce(self.time)

        # 5. Households consume goods and update needs
        for household in self.households:
            if household.is_active:
                household.decide_and_consume(self.time)



        # 6. Firms update needs (e.g., liquidity, check for closure)
        for firm in self.firms:
            if firm.is_active:
                firm.update_needs(self.time)

        # 7. Handle agent lifecycle (e.g., death, firm closure, unemployment)
        self._handle_agent_lifecycle()

        # --- Save agent states to DB ---
        for household in self.households:
            self.db_manager.save_agent_state(
                run_id=self.run_id,
                tick=self.time,
                agent_id=household.id,
                agent_type="Household",
                assets=household.assets,
                inventory=household.inventory,
                needs=household.needs,
                is_employed=household.is_employed,
                employer_id=household.employer_id
            )
        for firm in self.firms:
            self.db_manager.save_agent_state(
                run_id=self.run_id,
                tick=self.time,
                agent_id=firm.id,
                agent_type="Firm",
                assets=firm.assets,
                inventory=firm.inventory,
                employees=[emp.id for emp in firm.employees] if firm.employees else [],
                production_targets=firm.production_targets,
                current_production=firm.current_production
            )
        # --- End Save agent states to DB ---

        # 8. Collect economic indicators
        self.tracker.update(self.markets, self.households, self.firms, self.time, all_transactions)

        # Save simulation state to DB
        global_economic_indicators = {
            key: value[-1] if isinstance(value, list) and value else None
            for key, value in self.tracker.metrics.items()
        }
        self.db_manager.save_simulation_state(
            run_id=self.run_id,
            tick=self.time,

            global_economic_indicators=global_economic_indicators
        )

        # 9. Update pre_state_data for all agents for the next tick
        for agent in self.agents.values():
            if isinstance(agent, BaseAgent) and agent.is_active:
                agent.update_pre_state_data()

        self.logger.info(f"--- End of Tick {self.time} ---", extra={'tick': self.time, 'tags': ['tick_end']})

    def close_db_manager(self):
        """
        시뮬레이션 종료 시 DBManager 연결을 닫습니다.
        """
        self.db_manager.close()
        self.logger.info("DBManager connection closed.")

    def _prepare_market_data(self, tracker: EconomicIndicatorTracker) -> Dict[str, Any]:
        """현재 틱의 시장 데이터를 에이전트의 의사결정을 위해 준비합니다.

        Returns:
            Dict[str, Any]: 현재 시장 상태를 포함하는 딕셔너리.
        """
        goods_market_data = {}
        # Iterate over all goods defined in the config to populate market data
        for good_name in self.config_module.GOODS:
            market = self.markets.get(good_name)
            if market and isinstance(market, OrderBookMarket):
                best_ask_price = market.get_best_ask(good_name)
                # Use a default/fallback price if no sell orders are in the market yet
                goods_market_data[f'{good_name}_current_sell_price'] = best_ask_price if best_ask_price is not None else self.config_module.GOODS[good_name].get('initial_price', 10.0)

        # The concept of a single 'avg_goods_price' is now less meaningful.
        # We will calculate it as a simple average across all goods markets for now.
        # This might need a more sophisticated approach later (e.g., a weighted average).
        total_price = 0
        count = 0
        for good_name in self.config_module.GOODS:
            price = goods_market_data.get(f'{good_name}_current_sell_price')
            if price is not None:
                total_price += price
                count += 1
        
        avg_goods_price_for_market_data = total_price / count if count > 0 else 10.0 # Fallback to 10.0

        self.logger.debug(f"PREPARE_MARKET_DATA | Tick {self.time}, avg_goods_price_for_market_data: {avg_goods_price_for_market_data:.2f}", extra={'tick': self.time, 'tags': ['market_data_debug']})

        return {
            "time": self.time,
            "goods_market": goods_market_data, # This now contains prices for all goods
            "loan_market": {"interest_rate": self.config_module.LOAN_INTEREST_RATE},
            "all_households": self.households,
            "avg_goods_price": avg_goods_price_for_market_data
        }

    def get_all_agents(self) -> List[Any]:
        """시뮬레이션에 참여하는 모든 활성 에이전트(가계, 기업, 은행 등)를 반환합니다.

        Returns:
            List[Any]: 활성 에이전트 객체들의 리스트.
        """
        all_agents = []
        for agent in self.agents.values():
            if getattr(agent, 'is_active', True) and hasattr(agent, 'value_orientation') and agent.value_orientation != "N/A":
                all_agents.append(agent)
        return all_agents

    def _process_transactions(self, transactions: List[Transaction]) -> None:
        """발생한 거래들을 처리하여 에이전트의 자산, 재고, 고용 상태 등을 업데이트합니다.

        Args:
            transactions (List[Transaction]): 처리할 거래(Transaction) 객체들의 리스트.
        """
        for tx in transactions:
            buyer = self.agents.get(tx.buyer_id)
            seller = self.agents.get(tx.seller_id)
            
            if not buyer or not seller:
                self.logger.debug(f"TRANSACTION_SKIP | Invalid buyer or seller for transaction {tx.item_id} at tick {self.time}", extra={'tick': self.time, 'tags': ['debug_transaction']})
                continue

            trade_value = tx.quantity * tx.price
            
            buyer.assets -= trade_value
            seller.assets += trade_value
            self.logger.debug(f"TRANSACTION_ASSET_CHANGE | Agent {buyer.id} assets: {buyer.assets:.2f}, Agent {seller.id} assets: {seller.assets:.2f}", extra={'tick': self.time, 'tags': ['debug_transaction']})
            
            if tx.transaction_type == "labor" or tx.transaction_type == "research_labor":
                if isinstance(seller, Household):
                    # If household was previously employed by a different firm, remove them from that firm's employee list
                    if seller.is_employed and seller.employer_id is not None and seller.employer_id != buyer.id:
                        previous_employer = self.agents.get(seller.employer_id)
                        if isinstance(previous_employer, Firm) and seller in previous_employer.employees:
                            previous_employer.employees.remove(seller)
                            self.logger.info(f"HOUSEHOLD_UNEMPLOYED_FROM_PREVIOUS | Household {seller.id} removed from previous Firm {previous_employer.id} employees.", extra={'tick': self.time, 'agent_id': seller.id, 'firm_id': previous_employer.id, 'tags': ['debug_employment']})
                    
                    seller.is_employed = True
                    seller.employer_id = buyer.id
                    seller.needs["labor_need"] = 0.0
                    self.logger.info(f"HOUSEHOLD_EMPLOYED | Household {seller.id} employed by Firm {buyer.id}. is_employed={seller.is_employed}, employer_id={seller.employer_id}", extra={'tick': self.time, 'agent_id': seller.id, 'firm_id': buyer.id, 'tags': ['debug_employment']})
                
                if isinstance(buyer, Firm):
                    if seller not in buyer.employees:
                        buyer.employees.append(seller)
                        self.logger.info(f"FIRM_EMPLOYEE_ADD | Firm {buyer.id} added Household {seller.id} to employees. Total: {len(buyer.employees)}", extra={'tick': self.time, 'agent_id': buyer.id, 'employee_id': seller.id, 'tags': ['debug_employment']})
                    buyer.cost_this_turn += trade_value

                    if tx.transaction_type == "research_labor":
                        research_skill = seller.skills.get("research", Skill("research")).value
                        buyer.productivity_factor += research_skill * self.config_module.RND_PRODUCTIVITY_MULTIPLIER
                        self.logger.info(f"FIRM_PRODUCTIVITY_INCREASE | Firm {buyer.id} productivity increased to {buyer.productivity_factor:.2f} due to research labor from {seller.id}", extra={'tick': self.time, 'agent_id': buyer.id, 'employee_id': seller.id, 'tags': ['debug_productivity']})

            elif tx.transaction_type == "goods":
                seller.inventory[tx.item_id] = max(0, seller.inventory.get(tx.item_id, 0) - tx.quantity)
                buyer.inventory[tx.item_id] = buyer.inventory.get(tx.item_id, 0) + tx.quantity
                self.logger.debug(f"TRANSACTION_INVENTORY_CHANGE | Item {tx.item_id}: Seller {seller.id} inventory: {seller.inventory.get(tx.item_id, 0):.2f}, Buyer {buyer.id} inventory: {buyer.inventory.get(tx.item_id, 0):.2f}", extra={'tick': self.time, 'tags': ['debug_transaction']})
                if isinstance(seller, Firm):
                    seller.revenue_this_turn += trade_value
                    self.logger.debug(f"FIRM_REVENUE | Firm {seller.id} revenue this turn: {seller.revenue_this_turn:.2f}", extra={'tick': self.time, 'agent_id': seller.id, 'tags': ['debug_firm']})
                if isinstance(buyer, Household):
                    buyer.current_consumption += tx.quantity
                    if tx.item_id == 'basic_food':
                        buyer.current_food_consumption += tx.quantity
                    self.logger.debug(f"HOUSEHOLD_CONSUMPTION | Household {buyer.id} consumed {tx.quantity:.2f} of {tx.item_id}. Total consumption: {buyer.current_consumption:.2f}", extra={'tick': self.time, 'agent_id': buyer.id, 'tags': ['debug_household']})

    def _handle_agent_lifecycle(self) -> None:
        """비활성화된 에이전트(사망한 가계, 폐업한 기업)를 시뮬레이션에서 제거하고,
        기업의 고용 상태를 업데이트하는 등 에이전트의 생명주기를 관리합니다.
        """
        self.logger.debug(f"LIFECYCLE_START | Starting agent lifecycle management at tick {self.time}", extra={'tick': self.time, 'tags': ['debug_lifecycle']})

        # Debugging: Log initial employment status
        for household in self.households:
            if household.is_active:
                self.logger.debug(f"LIFECYCLE_DEBUG | Household {household.id} is_employed: {household.is_employed}", extra={'tick': self.time, 'agent_id': household.id, 'tags': ['debug_lifecycle', 'employment_status']})

        # --- Mark households of inactive firms as unemployed ---
        inactive_firms = [f for f in self.firms if not f.is_active]
        for firm in inactive_firms:
            self.logger.info(f"FIRM_INACTIVE | Firm {firm.id} is inactive. Making employees unemployed.", extra={'tick': self.time, 'firm_id': firm.id, 'tags': ['debug_lifecycle']})
            for employee in firm.employees:
                if employee.is_active: # Check if employee is still in the simulation
                    employee.is_employed = False
                    employee.employer_id = None
                    self.logger.info(f"HOUSEHOLD_UNEMPLOYED | Household {employee.id} became unemployed due to firm {firm.id} closure.", extra={'tick': self.time, 'agent_id': employee.id, 'firm_id': firm.id, 'tags': ['unemployment', 'debug_employment']})
            firm.employees = []
            self.logger.debug(f"FIRM_EMPLOYEES_CLEARED | Firm {firm.id} employees cleared.", extra={'tick': self.time, 'firm_id': firm.id, 'tags': ['debug_lifecycle']})

        # --- Filter out inactive agents ---
        initial_household_count = len(self.households)
        initial_firm_count = len(self.firms)
        
        active_households = [h for h in self.households if h.is_active]
        active_firms = [f for f in self.firms if f.is_active]

        if len(active_households) < initial_household_count:
            self.logger.info(f"HOUSEHOLDS_REMOVED | {initial_household_count - len(active_households)} households removed.", extra={'tick': self.time, 'tags': ['debug_lifecycle']})
        if len(active_firms) < initial_firm_count:
            self.logger.info(f"FIRMS_REMOVED | {initial_firm_count - len(active_firms)} firms removed.", extra={'tick': self.time, 'tags': ['debug_lifecycle']})

        self.households = active_households
        self.firms = active_firms

        # --- Rebuild agents dictionary with only active agents ---
        self.agents = {agent.id: agent for agent in self.households + self.firms}
        self.agents[self.bank.id] = self.bank # Ensure bank is always in agents list
        self.logger.debug(f"AGENTS_DICT_REBUILT | Total active agents: {len(self.agents)}", extra={'tick': self.time, 'tags': ['debug_lifecycle']})

        # --- Update employee lists for active firms to remove inactive employees ---
        for firm in self.firms:
            initial_employee_count = len(firm.employees)
            # Only keep employees who are still active in the simulation
            active_employees = [emp for emp in firm.employees if emp.is_active and emp.id in self.agents]
            
            if len(active_employees) < initial_employee_count:
                self.logger.info(f"FIRM_EMPLOYEES_UPDATED | Firm {firm.id} removed {initial_employee_count - len(active_employees)} inactive employees.", extra={'tick': self.time, 'firm_id': firm.id, 'tags': ['debug_lifecycle']})
            
            firm.employees = active_employees
            # Verify employment status consistency
            for emp in firm.employees:
                if not emp.is_employed or emp.employer_id != firm.id:
                    self.logger.warning(f"EMPLOYMENT_INCONSISTENCY | Firm {firm.id} has employee {emp.id} but household is_employed={emp.is_employed}/employer_id={emp.employer_id}", extra={'tick': self.time, 'firm_id': firm.id, 'agent_id': emp.id, 'tags': ['debug_employment']})

        self.logger.debug(f"LIFECYCLE_END | Finished agent lifecycle management at tick {self.time}", extra={'tick': self.time, 'tags': ['debug_lifecycle']})
