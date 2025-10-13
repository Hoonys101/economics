from __future__ import annotations
import logging
from typing import List, Dict, Any, TYPE_CHECKING, Optional, Tuple

from simulation.decisions import DecisionEngine
from simulation.ai.household_ai import HouseholdAI
from simulation.core_markets import Market, Order
from simulation.markets.order_book_market import OrderBookMarket
from simulation.ai.enums import Tactic
from simulation.ai_model import AIEngineRegistry

if TYPE_CHECKING:
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class HouseholdDecisionEngine(DecisionEngine):
    """
    가계 에이전트의 의사결정을 담당하는 구체적인 엔진.
    AI를 사용하여 전술(Tactic)을 결정하고, 효용 기반으로 최적의 소비를 계산하여
    실제 시장 주문으로 변환한다.
    """

    def __init__(self, agent_id: int, value_orientation: str, ai_engine_registry: AIEngineRegistry, ai_engine: HouseholdAI = None, logger: Optional[logging.Logger] = None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.agent: Optional[Household] = None
        if ai_engine:
            self.ai_engine = ai_engine
        else:
            self.ai_engine = HouseholdAI(agent_id=agent_id)
            self.ai_engine_registry = ai_engine_registry
            ai_decision_engine_instance = self.ai_engine_registry.get_engine(value_orientation)
            self.ai_engine.set_ai_decision_engine(ai_decision_engine_instance)

    def set_agent(self, agent: Household):
        self.agent = agent

    def make_decisions(self, agent: Household, markets: Dict[str, Market], goods_data: List[Dict[str, Any]], market_data: Dict[str, Any], current_time: int) -> Tuple[List[Order], Tactic]:
        agent_data = agent.get_agent_data()
        pre_state_data = agent.get_pre_state_data()
        chosen_tactic = self.ai_engine.decide_and_learn(agent_data, market_data, pre_state_data)
        orders = self._execute_tactic(chosen_tactic, agent, markets, current_time)
        return orders, chosen_tactic

    def _execute_tactic(self, tactic: Tactic, agent: Household, markets: Dict[str, Market], current_time: int) -> List[Order]:
        logger.debug(f"HOUSEHOLD_TACTIC | Agent {agent.id} chose Tactic: {tactic.name}", extra={'tick': current_time, 'agent_id': agent.id, 'tactic': tactic.name})
        
        if tactic == Tactic.EVALUATE_CONSUMPTION_OPTIONS:
            return self._find_optimal_consumption_bundle(agent, markets, current_time)
        
        elif tactic == Tactic.PARTICIPATE_LABOR_MARKET:
            labor_market = markets.get('labor_market')
            if labor_market:
                desired_wage = agent.get_desired_wage()
                return [Order(agent.id, 'SELL', 'labor', 1, desired_wage, labor_market.id)]
        
        return []

    def _get_consumption_candidates(self, markets: Dict[str, Market]) -> Dict[str, float]:
        """
        구매 가능한 모든 소비재와 그 가격 목록을 반환한다.
        """
        candidates = {}
        for good_name in self.agent.config_module.GOODS:
            market = markets.get(good_name)
            if market and isinstance(market, OrderBookMarket):
                price = market.get_best_ask(good_name)
                if price is not None:
                    candidates[good_name] = price
        return candidates

    def _calculate_utility_gain(self, agent: Household, good_name: str, quantity: float) -> float:
        """
        특정 재화를 주어진 양만큼 소비했을 때 얻는 총 효용 증가량을 계산한다.
        """
        utility_gain = 0
        good_spec = agent.config_module.GOODS.get(good_name)
        if not good_spec:
            return 0

        for need, effect in good_spec['utility_effects'].items():
            current_need_level = agent.needs.get(need, 0)
            # 효용은 필요 수준이 높을수록 더 크게 느껴진다 (한계 효용 체감의 역)
            # 간단한 모델로, 현재 필요 수준에 비례하여 효용을 계산
            utility_gain += (current_need_level * effect * quantity)
            
        return utility_gain

    def _find_optimal_consumption_bundle(self, agent: Household, markets: Dict[str, Market], current_time: int) -> List[Order]:
        """
        예산 제약 하에서 총 효용을 극대화하는 최적의 소비 조합(구매할 상품 목록)을 찾는다.
        """
        orders = []
        budget = agent.assets
        
        candidates = self._get_consumption_candidates(markets)
        if not candidates:
            return []

        # 1. 각 후보 재화의 '비용 대비 효용' (Utility per Dollar) 계산
        utility_per_dollar = {}
        for good, price in candidates.items():
            # 1단위 구매 시 효용을 계산하여 가성비 평가
            utility = self._calculate_utility_gain(agent, good, 1)
            if price > 0:
                utility_per_dollar[good] = utility / price
            else:
                utility_per_dollar[good] = float('inf') # 가격이 0이면 가성비 무한대

        # 2. 가성비가 높은 순으로 재화 정렬
        sorted_goods = sorted(utility_per_dollar.items(), key=lambda item: item[1], reverse=True)
        
        self.logger.debug(f"CONSUMPTION_CANDIDATES | Agent {agent.id}: Budget={budget:.2f}, Candidates={sorted_goods}", extra={'tick': current_time, 'agent_id': agent.id})

        # 3. 예산 내에서 가성비가 가장 좋은 상품부터 구매 시도
        for good, _ in sorted_goods:
            price = candidates[good]
            if budget < price:
                continue # 이 상품은 1개도 살 수 없음

            # 간단한 모델: 가장 가성비 좋은 상품 1개만 구매 시도
            quantity_to_buy = 1.0
            
            if budget >= price * quantity_to_buy:
                orders.append(Order(agent.id, 'BUY', good, quantity_to_buy, price, good))
                budget -= price * quantity_to_buy # 예산 업데이트
                self.logger.debug(f"HOUSEHOLD_DECISION | Agent {agent.id} placed BUY order for {quantity_to_buy:.2f} {good} at {price:.2f}.", extra={'tick': current_time, 'agent_id': agent.id, 'item': good})
                # Removed 'break' to allow purchasing multiple different goods (1 unit each) 

        return orders
