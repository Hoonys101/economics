# simulation/ai/firm_ai.py

from typing import Any, Dict, List, Tuple, TYPE_CHECKING

from .api import BaseAIEngine, Intention, Tactic

if TYPE_CHECKING:
    from simulation.ai_model import AIDecisionEngine

class FirmAI(BaseAIEngine):
    """
    기업 에이전트를 위한 AI 엔진.
    BaseAIEngine을 상속받아 기업에 특화된 상태, 행동, 보상 함수를 정의한다.
    """
    def __init__(self, agent_id: str, ai_decision_engine: 'AIDecisionEngine', gamma: float = 0.9, epsilon: float = 0.1, base_alpha: float = 0.1, learning_focus: float = 0.5):
        super().__init__(agent_id, ai_decision_engine, gamma, epsilon, base_alpha, learning_focus)


    def _discretize(self, value: float, bins: List[float]) -> int:
        """주어진 값을 구간(bin)에 따라 이산화하여 인덱스를 반환한다."""
        for i, b in enumerate(bins):
            if value <= b:
                return i
        return len(bins)

    def _get_strategic_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        기업의 거시적 상태를 정의한다.
        자산, 이윤, 시장 점유율, 재고 수준을 여러 단계로 이산화하여 상태를 표현한다.
        """
        # TODO: 이 구간 값들은 시뮬레이션의 스케일에 맞춰 동적으로 조정하거나, 통계 기반으로 설정해야 함
        asset_bins = [1000, 5000, 20000, 100000]
        profit_bins = [-100, 0, 500, 2000] # 이윤은 음수일 수 있음
        market_share_bins = [0.05, 0.1, 0.25, 0.5]
        inventory_bins = [5, 20, 100, 500]

        discretized_assets = self._discretize(agent_data.get('assets', 0), asset_bins)
        discretized_profit = self._discretize(agent_data.get('profit', 0), profit_bins)
        discretized_market_share = self._discretize(agent_data.get('market_share', 0), market_share_bins)
        discretized_inventory = self._discretize(agent_data.get('inventory', 0), inventory_bins)

        return (discretized_assets, discretized_profit, discretized_market_share, discretized_inventory)

    def _get_tactical_state(self, intention: Intention, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        선택된 Intention에 따른 기업의 세부 상태를 정의한다.
        각 Intention에 맞는 시장 데이터와 에이전트 데이터를 바탕으로 상태를 이산화한다.
        """
        assets = agent_data.get('assets', 0)
        my_price = agent_data.get('price', 1)

        if intention == Intention.MAXIMIZE_PROFIT:
            # 수요-공급 비율, 경쟁사 대비 가격, 이윤률
            # TODO: 'goods_market'에서 실제 데이터를 받아와야 함
            demand = market_data.get('goods', {}).get('demand', 1)
            supply = market_data.get('goods', {}).get('supply', 1)
            avg_price = market_data.get('goods', {}).get('avg_price', 1)
            profit_margin = agent_data.get('profit_margin', 0)

            demand_supply_ratio = demand / supply if supply > 0 else 1
            price_ratio = my_price / avg_price if avg_price > 0 else 1

            return (
                self._discretize(demand_supply_ratio, [0.8, 1.0, 1.2, 1.5]),
                self._discretize(price_ratio, [0.8, 1.0, 1.2, 1.5]),
                self._discretize(profit_margin, [0.05, 0.1, 0.2, 0.4])
            )

        elif intention == Intention.INCREASE_MARKET_SHARE:
            # 현재 시장 점유율, 경쟁사 대비 가격
            market_share = agent_data.get('market_share', 0)
            avg_price = market_data.get('goods', {}).get('avg_price', 1)
            price_ratio = my_price / avg_price if avg_price > 0 else 1

            return (
                self._discretize(market_share, [0.05, 0.1, 0.25, 0.5]),
                self._discretize(price_ratio, [0.8, 1.0, 1.2, 1.5])
            )

        elif intention == Intention.IMPROVE_PRODUCTIVITY:
            # 자본 투자 여력, 직원 훈련 여력
            # TODO: 투자 및 훈련 비용을 별도 market이나 config에서 가져와야 함
            capital_cost = 1000
            training_cost = 200
            
            capital_affordability = assets / capital_cost if capital_cost > 0 else 0
            training_affordability = assets / training_cost if training_cost > 0 else 0

            return (
                self._discretize(capital_affordability, [0.5, 1.0, 2.0, 5.0]),
                self._discretize(training_affordability, [1.0, 2.0, 5.0, 10.0])
            )

        return tuple()

    def _get_strategic_actions(self) -> List[Intention]:
        """
        기업이 선택할 수 있는 Intention 목록.
        """
        return [
            Intention.DO_NOTHING,
            Intention.MAXIMIZE_PROFIT,
            Intention.INCREASE_MARKET_SHARE,
            Intention.IMPROVE_PRODUCTIVITY,
        ]

    def _get_tactical_actions(self, intention: Intention) -> List[Tactic]:
        """
        주어진 Intention에 대해 기업이 선택할 수 있는 Tactic 목록.
        """
        if intention == Intention.MAXIMIZE_PROFIT:
            return [Tactic.ADJUST_PRICE, Tactic.ADJUST_PRODUCTION, Tactic.ADJUST_WAGES]
        elif intention == Intention.INCREASE_MARKET_SHARE:
            return [Tactic.LOWER_PRICE, Tactic.INCREASE_MARKETING]
        elif intention == Intention.IMPROVE_PRODUCTIVITY:
            return [Tactic.INVEST_IN_CAPITAL, Tactic.TRAIN_EMPLOYEES]
        return []

    def _calculate_reward(self, pre_state_data: Dict[str, Any], post_state_data: Dict[str, Any], agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """
        기업 행동의 결과로 얻어지는 보상을 계산한다.
        이윤 변화, 시장 점유율 변화에 가중치를 적용하고, 손실 및 파산에 페널티를 부과한다.
        """
        # 보상 및 페널티 가중치
        reward_weights = {
            'profit_change': 1.0,            # 이윤 변화량
            'market_share_change': 100.0,    # 시장 점유율 변화량 (작은 값이므로 가중치 높게)
            'loss_penalty': -200.0,           # 손실 발생 페널티
            'bankruptcy_penalty': -2000.0,    # 파산 페널티 (가장 큰 페널티)
        }

        # 1. 파산 페널티
        if post_state_data.get('assets', 0) <= 0:
            return reward_weights['bankruptcy_penalty']

        # 2. 이윤 변화 보상
        profit_change = post_state_data.get('profit', 0) - pre_state_data.get('profit', 0)
        reward = profit_change * reward_weights['profit_change']

        # 3. 시장 점유율 변화 보상
        market_share_change = post_state_data.get('market_share', 0) - pre_state_data.get('market_share', 0)
        reward += market_share_change * reward_weights['market_share_change']

        # 4. 손실 발생 페널티
        if post_state_data.get('profit', 0) < 0:
            reward += reward_weights['loss_penalty']

        # Integrate predicted reward from AIDecisionEngine
        if self.ai_decision_engine:
            predicted_reward = self.ai_decision_engine.get_predicted_reward(agent_data, market_data)
            # TODO: Refine how predicted_reward is integrated (e.g., weighting, thresholding)
            reward += predicted_reward * 0.05 # Add a small portion as a bonus
        
        return reward
