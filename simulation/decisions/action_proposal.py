import logging
import random
from typing import Optional, Any, List
from simulation.models import Order
from modules.system.api import DEFAULT_CURRENCY

class ActionProposalEngine:
    """
    에이전트의 상태에 기반하여 현실적인 후보 행동(주문) 목록을 생성합니다.
    '어떤 행동들을 할 수 있는가?'에 대한 책임을 집니다.
    """

    def __init__(self, config_module: Any, n_action_samples: int=10, logger: Optional[logging.Logger]=None) -> None:
        self.config_module = config_module
        self.n_action_samples = n_action_samples
        self.logger = logger if logger else logging.getLogger(__name__)

    def propose_actions(self, agent: Any, current_time: int) -> List[List[Order]]:
        """
        에이전트 유형에 따라 적절한 행동 제안 메서드를 호출합니다.
        """
        agent_type = agent.__class__.__name__.lower()
        if agent_type == 'household':
            return self._propose_household_actions(agent, current_time)
        elif agent_type == 'firm':
            return self._propose_firm_actions(agent, current_time)
        return []

    def _propose_household_actions(self, agent: Any, current_time: int) -> List[List[Order]]:
        assets_val = 0.0
        if hasattr(agent, 'wallet'):
            assets_val = agent.wallet.get_balance(DEFAULT_CURRENCY)
        elif hasattr(agent, 'assets') and isinstance(agent.assets, dict):
            assets_val = agent.assets.get(DEFAULT_CURRENCY, 0.0)
        elif hasattr(agent, 'assets'):
            assets_val = float(agent.assets)
        self.logger.debug(f'DEBUG: Entering _propose_household_actions for Household {agent.id}. Assets: {assets_val:.2f}, is_employed: {agent.is_employed}', extra={'tick': current_time, 'agent_id': agent.id, 'tags': ['debug_propose_actions_entry']})
        '\n        가계 에이전트를 위한 다양한 후보 행동들을 생성합니다.\n        - 노동 시장 참여 (실직 상태이고 자산이 적을 경우)\n        - 상품 시장 참여 (구매)\n        '
        candidate_action_sets = []
        for _ in range(self.n_action_samples):
            orders = []
            explore_labor_market = False
            condition_assets_low = assets_val < self.config_module.HOUSEHOLD_ASSETS_THRESHOLD_FOR_LABOR_SUPPLY
            condition_random_check = random.random() < self.config_module.FORCED_LABOR_EXPLORATION_PROBABILITY
            self.logger.debug(f'DEBUG: Household {agent.id} labor conditions: is_employed={agent.is_employed}, assets={assets_val:.2f} < threshold={self.config_module.HOUSEHOLD_ASSETS_THRESHOLD_FOR_LABOR_SUPPLY} ({condition_assets_low}), random_check={condition_random_check}', extra={'tick': current_time, 'agent_id': agent.id, 'tags': ['debug_labor_conditions']})
            if not agent.is_employed and condition_assets_low:
                if condition_random_check:
                    explore_labor_market = True
            if explore_labor_market or (not agent.is_employed and random.random() < 0.5):
                self.logger.debug(f'DEBUG: Household {agent.id} is attempting to sell labor. explore_labor_market: {explore_labor_market}, is_employed: {agent.is_employed}', extra={'tick': current_time, 'agent_id': agent.id, 'tags': ['debug_labor_sell']})
                should_refuse = False
                if hasattr(agent, 'decision_engine') and hasattr(agent.decision_engine, 'context'):
                    pass
                desired_wage = self.config_module.LABOR_MARKET_MIN_WAGE * random.uniform(0.9, 1.3)
                orders.append(Order(agent_id=agent.id, side='SELL', item_id='labor', quantity=1, price_pennies=int(desired_wage * 100), price_limit=desired_wage, market_id='labor_market'))
            elif assets_val > 1:
                if hasattr(self.config_module, 'get'):
                    available_goods = self.config_module.get('simulation.household_consumable_goods', ['basic_food', 'luxury_food'])
                else:
                    available_goods = getattr(self.config_module, 'HOUSEHOLD_CONSUMABLE_GOODS', ['basic_food', 'luxury_food'])
                good_to_trade = random.choice(available_goods)
                spending_ratio = random.uniform(0.05, 0.3)
                budget = assets_val * spending_ratio
                price = agent.perceived_avg_prices.get(good_to_trade, self.config_module.GOODS_MARKET_SELL_PRICE)
                price = max(price, 0.01)
                max_quantity = budget / price
                if max_quantity > 1:
                    quantity = random.uniform(1, max_quantity)
                else:
                    quantity = random.uniform(max_quantity / 2, max_quantity)
                if quantity > 0:
                    order_price = price * random.uniform(0.95, 1.15)
                    orders.append(Order(agent_id=agent.id, side='BUY', item_id=good_to_trade, quantity=quantity, price_pennies=int(order_price * 100), price_limit=order_price, market_id='goods_market'))
            if orders:
                candidate_action_sets.append(orders)
        return candidate_action_sets

    def _propose_firm_actions(self, agent: Any, current_time: int) -> List[List[Order]]:
        """
        기업 에이전트를 위한 다양한 후보 행동들을 생성합니다.
        - 노동 시장 참여 (고용)
        - 상품 시장 참여 (판매)
        """
        candidate_action_sets = []
        for _ in range(self.n_action_samples):
            orders = []
            if random.random() < 0.5:
                offer_wage = self.config_module.INITIAL_WAGE * random.uniform(0.9, 1.1)
                orders.append(Order(agent_id=agent.id, side='BUY', item_id='labor', quantity=1, price_pennies=int(offer_wage * 100), price_limit=offer_wage, market_id='labor_market'))
            else:
                good_to_trade = agent.specialization
                if agent.get_quantity(good_to_trade) > 0:
                    price = self.config_module.GOODS_MARKET_SELL_PRICE * random.uniform(0.9, 1.1)
                    quantity = random.uniform(0.1, agent.get_quantity(good_to_trade))
                    orders.append(Order(agent_id=agent.id, side='SELL', item_id=good_to_trade, quantity=quantity, price_pennies=int(price * 100), price_limit=price, market_id='goods_market'))
            if orders:
                candidate_action_sets.append(orders)
        return candidate_action_sets

    def propose_forced_labor_action(self, household: Any, current_time: int, wage_factor: float) -> Order:
        """
        강제 탐험을 위한 노동 판매 행동을 제안합니다.
        """
        desired_wage = self.config_module.LABOR_MARKET_MIN_WAGE * random.uniform(0.9, 1.3) * wage_factor
        return Order(agent_id=household.id, side='SELL', item_id='labor', quantity=1, price_pennies=int(desired_wage * 100), price_limit=desired_wage, market_id='labor_market')