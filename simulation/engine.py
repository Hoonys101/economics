from __future__ import annotations
from typing import List, Dict, Any
import logging

from simulation.models import Transaction
from simulation.core_agents import Household, Skill
from simulation.firms import Firm
from simulation.markets import OrderBookMarket
from simulation.core_markets import Market
from simulation.agents.bank import Bank
from simulation.loan_market import LoanMarket
from simulation.ai_model import AITrainingManager
import config

# New imports for database
from simulation.db.repository import SimulationRepository

logger = logging.getLogger(__name__)

class EconomicIndicatorTracker:
    """경제 시뮬레이션의 주요 지표들을 추적하고 기록하는 클래스.

    매 틱마다 가계, 기업, 시장 데이터를 기반으로 실업률, 평균 가격, 총 자산 등을 계산하고 저장합니다.
    """
    def __init__(self, repository: SimulationRepository) -> None: # Add repository parameter
        """EconomicIndicatorTracker를 초기화합니다.

        metrics: 추적할 경제 지표들을 저장하는 딕셔너리.
        repository: 데이터를 저장할 SimulationRepository 인스턴스.
        all_fieldnames: CSV 파일 저장 시 사용될 모든 필드 이름 리스트 (이제 사용되지 않음).
        """
        self.metrics: Dict[str, List[float]] = {"goods_price_index": [], "unemployment_rate": [], "avg_wage": []}
        self.repository = repository # Store repository instance
        self.all_fieldnames: List[str] = [ # Keep for record structure, but not for CSV writing
            'time', 'total_household_assets', 'total_firm_assets', 'unemployment_rate',
            'food_avg_price', 'food_trade_volume', 'avg_goods_price', 'avg_wage',
            'total_production', 'total_consumption', 'total_food_consumption', 'total_inventory'
        ]
        self.logger = logging.getLogger(__name__)
        self.logger.debug("EconomicIndicatorTracker initialized.")

    def update(self, markets: Dict[str, Market], households: List[Household], firms: List[Firm], time: int, all_transactions: List[Transaction]) -> None:
        """현재 시뮬레이션 틱의 경제 지표를 계산하고 기록합니다.

        Args:
            markets (Dict[str, Market]): 현재 시뮬레이션의 모든 시장 인스턴스.
            households (List[Household]): 현재 시뮬레이션의 모든 가계 에이전트.
            firms (List[Firm]): 현재 시뮬레이션의 모든 기업 에이전트.
            time (int): 현재 시뮬레이션 틱.
            all_transactions (List[Transaction]): 현재 틱에서 발생한 모든 거래 내역.
        """
        self.logger.info(f"Starting tracker update for tick {time}", extra={'tick': time, 'tags': ['tracker']})
        record = {}
        record["time"] = time

        total_household_assets = sum(h.assets for h in households if getattr(h, 'is_active', True))
        total_firm_assets = sum(f.assets for f in firms if getattr(f, 'is_active', False))
        record["total_household_assets"] = total_household_assets
        record["total_firm_assets"] = total_firm_assets

        total_households = len([h for h in households if getattr(h, 'is_active', True)])
        unemployed_households = len([h for h in households if getattr(h, 'is_active', True) and not h.is_employed])
        unemployment_rate = (unemployed_households / total_households) * 100 if total_households > 0 else 0
        record["unemployment_rate"] = unemployment_rate

        food_transactions = [tx for tx in all_transactions if tx.item_id == 'food' and tx.transaction_type == 'goods']
        self.logger.debug(f"TRACKER_FOOD_TRANSACTIONS | Tick {time}, Food Transactions: {len(food_transactions)}", extra={'tick': time, 'tags': ['tracker']})
        if food_transactions:
            record["food_avg_price"] = sum(tx.price for tx in food_transactions) / len(food_transactions)
            record["food_trade_volume"] = sum(tx.quantity for tx in food_transactions)
        else:
            record["food_avg_price"] = 0.0
            record["food_trade_volume"] = 0.0

        goods_transactions = [tx for tx in all_transactions if tx.transaction_type == 'goods']
        if goods_transactions:
            avg_goods_price = sum(tx.price for tx in goods_transactions) / len(goods_transactions)
            record["avg_goods_price"] = avg_goods_price
        else:
            # If no goods transactions, carry over the last recorded avg_goods_price
            # or use a default if no history exists.
            last_avg_goods_price = self.repository.get_latest_economic_indicator('avg_goods_price')
            if last_avg_goods_price is not None:
                record["avg_goods_price"] = last_avg_goods_price
            else:
                record["avg_goods_price"] = config.GOODS_MARKET_SELL_PRICE # Fallback for first tick
        
        labor_transactions = [tx for tx in all_transactions if tx.transaction_type == 'labor']
        if labor_transactions:
            avg_wage = sum(tx.price for tx in labor_transactions) / len(labor_transactions)
            record["avg_wage"] = avg_wage
            self.logger.debug(f"TRACKER_LABOR_TRANSACTIONS | Tick {time}, Labor Transactions: {len(labor_transactions)}, Prices: {[tx.price for tx in labor_transactions]}", extra={'tick': time, 'tags': ['tracker', 'labor_debug']})
        else:
            record["avg_wage"] = 0.0
            self.logger.debug(f"TRACKER_LABOR_TRANSACTIONS | Tick {time}, No labor transactions.", extra={'tick': time, 'tags': ['tracker', 'labor_debug']})

        total_production = sum(f.current_production for f in firms if getattr(f, 'is_active', False))
        record["total_production"] = total_production

        total_consumption = sum(h.current_consumption for h in households if getattr(h, 'is_active', True))
        record["total_consumption"] = total_consumption

        total_food_consumption = sum(h.current_food_consumption for h in households if isinstance(h, Household) and getattr(h, 'is_active', True))
        record["total_food_consumption"] = total_food_consumption

        total_inventory = sum(sum(f.inventory.values()) for f in firms if getattr(f, 'is_active', False))
        record["total_inventory"] = total_inventory

        for field in self.all_fieldnames:
            record.setdefault(field, 0.0)

        self.repository.save_economic_indicator(record) # Save to database
        self.logger.debug(f"Finished update for tick {time}. Record saved to DB.", extra={'tick': time, 'tags': ['tracker']})

class Simulation:
    """경제 시뮬레이션의 전체 흐름을 관리하고 조정하는 핵심 엔진 클래스.

    가계, 기업, 시장, 은행 등 모든 시뮬레이션 구성 요소를 초기화하고,
    각 시뮬레이션 틱(tick)마다 에이전트의 의사결정, 시장 거래, 생산 및 소비 활동을 순차적으로 실행합니다.
    """
    def __init__(self, households: List[Household], firms: List[Firm], goods_data: List[Dict[str, Any]], ai_trainer: AITrainingManager, repository: SimulationRepository, logger: logging.Logger | None = None) -> None:
        """Simulation 클래스를 초기화합니다.

        Args:
            households (List[Household]): 시뮬레이션에 참여할 가계 에이전트 리스트.
            firms (List[Firm]): 시뮬레이션에 참여할 기업 에이전트 리스트.
            goods_data (List[Dict[str, Any]]): 시뮬레이션 내 모든 재화에 대한 정보.
            ai_trainer (AITrainingManager): AI 모델 훈련을 관리하는 인스턴스.
            repository (SimulationRepository): 데이터 저장을 위한 Repository 인스턴스.
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
        self.goods_data = goods_data
        self.next_agent_id = len(households) + len(firms)

        self.bank = Bank(id=self.next_agent_id, initial_assets=config.INITIAL_BANK_ASSETS)
        self.agents[self.bank.id] = self.bank
        self.next_agent_id += 1

        self.markets: Dict[str, Market] = {
            'goods_market': OrderBookMarket(market_id='goods_market'),
            'labor_market': OrderBookMarket(market_id='labor_market'),
            'loan_market': LoanMarket(market_id='loan_market', bank=self.bank)
        }

        for household in self.households:
            household.decision_engine.goods_market = self.markets['goods_market']
            household.decision_engine.labor_market = self.markets['labor_market']
            household.decision_engine.loan_market = self.markets['loan_market']
        for firm in self.firms:
            firm.decision_engine.goods_market = self.markets['goods_market']
            firm.decision_engine.labor_market = self.markets['labor_market']
            firm.decision_engine.loan_market = self.markets['loan_market']
        self.repository = repository # Use passed-in repository
        self.tracker = EconomicIndicatorTracker(self.repository) # Pass repository to tracker
        self.ai_trainer = ai_trainer
        self.time: int = 0

    def run_tick(self, repository: SimulationRepository) -> None:
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

        # 1. Households make decisions and place orders
        for household in self.households:
            if household.is_active:
                household_orders = household.make_decision(market_data, self.time)
                for order in household_orders:
                    market = self.markets.get(order.market_id)
                    if market:
                        market.place_order(order)

        # 2. Firms make decisions and place orders
        for firm in self.firms:
            if firm.is_active:
                firm_orders = firm.make_decision(market_data, self.time)
                for order in firm_orders:
                    market = self.markets.get(order.market_id)
                    if market:
                        market.place_order(order)

        # 3. Match orders and execute transactions for all markets
        for market in self.markets.values():
            if isinstance(market, OrderBookMarket):
                all_transactions.extend(market.match_and_execute_orders(self.time))

        self.logger.debug(f"PROCESS_TRANSACTIONS_START | Tick {self.time}, Processing {len(all_transactions)} transactions.", extra={'tick': self.time, 'tags': ['debug_transaction']})
        for tx in all_transactions:
            self.logger.debug(f"TRANSACTION_DETAIL | Tick {self.time}, Type: {tx.transaction_type}, Item: {tx.item_id}, Price: {tx.price}, Quantity: {tx.quantity}", extra={'tick': self.time, 'tags': ['debug_transaction']})
        self._process_transactions(all_transactions)
        self.logger.debug(f"PROCESS_TRANSACTIONS_END | Tick {self.time}, Finished processing transactions.", extra={'tick': self.time, 'tags': ['debug_transaction']})

        # --- GEMINI_TEMP_CHANGE_START: Save transactions to repository ---
        for tx in all_transactions:
            repository.save_transaction({
                'time': self.time,
                'buyer_id': tx.buyer_id,
                'seller_id': tx.seller_id,
                'item_id': tx.item_id,
                'quantity': tx.quantity,
                'price': tx.price,
                'market_id': tx.market_id,
                'transaction_type': tx.transaction_type
            })
        # --- GEMINI_TEMP_CHANGE_END ---

        # --- GEMINI_TEMP_CHANGE_START: Save market history to repository ---
        for market_id, market in self.markets.items():
            if isinstance(market, OrderBookMarket):
                market_transactions = [tx for tx in all_transactions if tx.market_id == market_id]
                
                avg_price = 0.0
                trade_volume = 0.0
                if market_transactions:
                    total_price_quantity = sum(tx.price * tx.quantity for tx in market_transactions)
                    total_quantity = sum(tx.quantity for tx in market_transactions)
                    if total_quantity > 0:
                        avg_price = total_price_quantity / total_quantity
                    trade_volume = total_quantity

                # For goods market, we can get best ask/bid for specific items
                # For labor market, best ask/bid might not be item-specific in the same way
                best_ask = None
                best_bid = None
                if market_id == 'goods_market':
                    # Assuming 'food' is a key item in goods market
                    best_ask = market.get_best_ask('food')
                    best_bid = market.get_best_bid('food')
                elif market_id == 'labor_market':
                    best_ask = market.get_best_ask('labor')
                    best_bid = market.get_best_bid('labor')


                self.repository.save_market_history({
                    'time': self.time,
                    'market_id': market_id,
                    'item_id': 'food' if market_id == 'goods_market' else ('labor' if market_id == 'labor_market' else None), # Specify item_id if relevant
                    'avg_price': avg_price,
                    'trade_volume': trade_volume,
                    'best_ask': best_ask,
                    'best_bid': best_bid
                })
        # --- GEMINI_TEMP_CHANGE_END ---

        # 4. Firms produce goods
        for firm in self.firms:
            if firm.is_active:
                firm.produce(self.time)

        # 5. Households consume goods and update needs
        for household in self.households:
            if household.is_active:
                # For simplicity, households consume food based on their survival need
                # More complex consumption logic can be added to HouseholdDecisionEngine
                food_needed = household.needs["survival_need"] / config.SURVIVAL_NEED_INCREASE_RATE # Rough estimate
                if household.inventory.get('food', 0) > 0 and food_needed > 0:
                    consume_quantity = min(food_needed, household.inventory['food'])
                    household.consume('food', consume_quantity, self.time)
                household.update_needs(self.time)

        # 6. Firms update needs (e.g., liquidity, check for closure)
        for firm in self.firms:
            if firm.is_active:
                firm.update_needs(self.time)

        # 7. Handle agent lifecycle (e.g., death, firm closure, unemployment)
        self._handle_agent_lifecycle()

        # --- GEMINI_TEMP_CHANGE_START: Save agent states to repository ---
        for household in self.households:
            self.repository.save_agent_state({
                'time': self.time,
                'agent_id': household.id,
                'agent_type': 'household',
                'assets': household.assets,
                'is_active': household.is_active,
                'is_employed': household.is_employed,
                'employer_id': household.employer_id,
                'needs_survival': household.needs.get('survival_need'),
                'needs_labor': household.needs.get('labor_need'),
                'inventory_food': household.inventory.get('food'),
                'current_production': None, # Households don't produce
                'num_employees': None # Households don't have employees
            })
        for firm in self.firms:
            self.repository.save_agent_state({
                'time': self.time,
                'agent_id': firm.id,
                'agent_type': 'firm',
                'assets': firm.assets,
                'is_active': firm.is_active,
                'is_employed': None, # Firms are not employed
                'employer_id': None, # Firms don't have employers
                'needs_survival': None, # Firms don't have survival needs
                'needs_labor': None, # Firms don't have labor needs
                'inventory_food': firm.inventory.get('food'),
                'current_production': firm.current_production,
                'num_employees': len(firm.employees)
            })
        # --- GEMINI_TEMP_CHANGE_END ---

        # 8. Collect economic indicators
        self.tracker.update(self.markets, self.households, self.firms, self.time, all_transactions)

        self.logger.info(f"--- End of Tick {self.time} ---", extra={'tick': self.time, 'tags': ['tick_end']})

    def close_repository(self):
        """
        시뮬레이션 종료 시 Repository 연결을 닫습니다.
        """
        self.repository.close()
        self.logger.info("Repository connection closed.")

    def _prepare_market_data(self, tracker: EconomicIndicatorTracker) -> Dict[str, Any]:
        """현재 틱의 시장 데이터를 에이전트의 의사결정을 위해 준비합니다.

        Returns:
            Dict[str, Any]: 현재 시장 상태를 포함하는 딕셔너리.
        """
        goods_market_data = {}
        goods_market = self.markets.get('goods_market')

        if goods_market:
            for good in self.goods_data:
                item_id = good['id']
                best_ask_price = goods_market.get_best_ask(item_id)
                
                if best_ask_price is not None:
                    goods_market_data[f'{item_id}_current_sell_price'] = best_ask_price
                else:
                    goods_market_data[f'{item_id}_current_sell_price'] = config.GOODS_MARKET_SELL_PRICE

        # Get avg_goods_price from the tracker's last recorded value
        # If first tick or no previous data, use GOODS_MARKET_SELL_PRICE as fallback
        avg_goods_price_for_market_data = tracker.repository.get_latest_economic_indicator('avg_goods_price')
        if avg_goods_price_for_market_data is None:
            avg_goods_price_for_market_data = config.GOODS_MARKET_SELL_PRICE

        avg_wage_for_market_data = tracker.repository.get_latest_economic_indicator('avg_wage')
        if avg_wage_for_market_data is None or avg_wage_for_market_data == 0:
            avg_wage_for_market_data = config.BASE_WAGE
        
        self.logger.debug(f"PREPARE_MARKET_DATA | Tick {self.time}, avg_goods_price_for_market_data: {avg_goods_price_for_market_data:.2f}", extra={'tick': self.time, 'tags': ['market_data_debug']})

        return {
            "time": self.time,
            "goods_market": goods_market_data,
            "loan_market": {"interest_rate": config.LOAN_INTEREST_RATE},
            "all_households": self.households,
            "goods_data": self.goods_data,
            "avg_goods_price": avg_goods_price_for_market_data # Added avg_goods_price
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
                        buyer.productivity_factor += research_skill * config.RND_PRODUCTIVITY_MULTIPLIER
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
                    if tx.item_id == 'food':
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