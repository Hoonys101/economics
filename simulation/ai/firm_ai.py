import logging
from typing import Any, Dict, List, Tuple, TYPE_CHECKING, Optional

from .api import BaseAIEngine, Intention, Tactic, Aggressiveness

if TYPE_CHECKING:
    from simulation.ai_model import AIDecisionEngine

logger = logging.getLogger(__name__)


class FirmAI(BaseAIEngine):
    """
    기업 에이전트를 위한 AI 엔진.
    BaseAIEngine을 상속받아 기업에 특화된 상태, 행동, 보상 함수를 정의한다.
    """

    def __init__(
        self,
        agent_id: str,
        ai_decision_engine: "AIDecisionEngine",
        gamma: float = 0.9,
        epsilon: float = 0.1,
        base_alpha: float = 0.1,
        learning_focus: float = 0.5,
    ):
        super().__init__(agent_id, gamma, epsilon, base_alpha, learning_focus)
        self.ai_decision_engine: AIDecisionEngine | None = None
        self.set_ai_decision_engine(ai_decision_engine)
        self.last_chosen_tactic: Optional[Tuple[Tactic, Aggressiveness]] = None
        self.chosen_intention: Intention | None = None

    def set_ai_decision_engine(self, engine: "AIDecisionEngine"):
        """
        AIDecisionEngine 인스턴스를 외부에서 주입받아 설정합니다.
        """
        self.ai_decision_engine = engine

    def _get_strategic_state(
        self, agent_data: Dict[str, Any], market_data: Dict[str, Any]
    ) -> Tuple:
        """
        기업의 거시적 상태를 정의한다.
        수익성, 재고 수준, 노동력 확보 수준을 이산화하여 상태를 표현한다.
        """
        # 수익성 (예: 5단계)
        profit_bins = [-1000.0, -100.0, 0.0, 1000.0, 5000.0]
        profit = agent_data.get("assets", 0) - agent_data.get(
            "pre_assets", agent_data.get("assets", 0)
        )
        discretized_profit = self._discretize(profit, profit_bins)

        # 재고 수준 (목표 대비 비율, 예: 5단계)
        inventory = agent_data.get("inventory", {})
        item_id = agent_data.get("specialization", "food")
        current_inventory = inventory.get(item_id, 0)
        target_inventory = agent_data.get("production_target", 1)
        inventory_ratio = (
            current_inventory / target_inventory if target_inventory > 0 else 0
        )
        inventory_bins = [
            0.5,
            1.0,
            1.5,
            2.0,
        ]  # 목표 대비 50% 미만, 50-100%, 100-150%, 150-200%, 200% 초과
        discretized_inventory = self._discretize(inventory_ratio, inventory_bins)

        # 노동력 확보 수준 (필요 대비 현재, 예: 5단계)
        needed_labor = agent_data.get("needed_labor", 1)
        num_employees = len(agent_data.get("employees", []))
        labor_ratio = num_employees / needed_labor if needed_labor > 0 else 1
        labor_bins = [0.5, 0.8, 1.0, 1.2]
        discretized_labor = self._discretize(labor_ratio, labor_bins)

        return (discretized_profit, discretized_inventory, discretized_labor)

    def _get_tactical_state(
        self,
        intention: Intention,
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> Tuple:
        """
        선택된 Intention에 따른 기업의 세부 상태를 정의한다.
        """
        if intention == Intention.MAXIMIZE_PROFIT:
            # 시장 경쟁 상황 (경쟁사 수, 평균 가격 등)
            num_competitors = market_data.get("num_firms", 1) - 1
            avg_price = market_data.get("avg_goods_price", 10)
            discretized_competitors = self._discretize(num_competitors, [1.0, 3.0, 5.0, 10.0])
            discretized_price = self._discretize(
                agent_data.get("last_prices", {}).get(
                    agent_data.get("specialization"), 10
                )
                / avg_price,
                [0.8, 1.0, 1.2, 1.5],
            )
            return (discretized_competitors, discretized_price)

        elif intention == Intention.INCREASE_MARKET_SHARE:
            # 시장 점유율
            market_share = agent_data.get("market_share", 0)
            discretized_market_share = self._discretize(
                market_share, [0.1, 0.2, 0.4, 0.6]
            )
            return (discretized_market_share,)

        elif intention == Intention.IMPROVE_PRODUCTIVITY:
            # 현재 생산성
            productivity = agent_data.get("productivity_factor", 1)
            discretized_productivity = self._discretize(
                productivity, [1.0, 1.2, 1.5, 2.0]
            )
            return (discretized_productivity,)

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

    def _get_tactical_actions(self, intention: Intention) -> List[Tuple[Tactic, Aggressiveness]]:
        """
        주어진 Intention에 대해 기업이 선택할 수 있는 Tactic과 Aggressiveness 조합 목록.
        """
        actions = []
        if intention == Intention.MAXIMIZE_PROFIT:
            tactics = [
                Tactic.ADJUST_PRICE,
                Tactic.ADJUST_PRODUCTION,
                Tactic.ADJUST_WAGES,
                Tactic.PRICE_INCREASE_SMALL,
                Tactic.PRICE_INCREASE_MEDIUM,
                Tactic.PRICE_DECREASE_SMALL,
                Tactic.PRICE_DECREASE_MEDIUM,
                Tactic.PRICE_HOLD,
            ]
            for tactic in tactics:
                actions.append((tactic, Aggressiveness.NORMAL))
            return actions
        elif intention == Intention.INCREASE_MARKET_SHARE:
            for tactic in [Tactic.LOWER_PRICE, Tactic.INCREASE_MARKETING]:
                actions.append((tactic, Aggressiveness.NORMAL))
            return actions
        elif intention == Intention.IMPROVE_PRODUCTIVITY:
            for tactic in [Tactic.INVEST_IN_CAPITAL, Tactic.TRAIN_EMPLOYEES]:
                actions.append((tactic, Aggressiveness.NORMAL))
            return actions
        return []

    def _calculate_reward(
        self,
        pre_state_data: Dict[str, Any],
        post_state_data: Dict[str, Any],
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> float:
        """
        기업 행동의 결과로 얻어지는 보상을 계산한다.
        수익, 시장 점유율, 생산성 변화 등을 종합적으로 고려한다.
        """
        reward_weights = {
            "profit": 1.0,
            "market_share_growth": 100.0,
            "productivity_growth": 200.0,
            "bankruptcy_penalty": -10000.0,
            "revenue_change": 0.5,  # Added revenue change weight
        }

        if not post_state_data.get("is_active", True):
            return reward_weights["bankruptcy_penalty"]

        # 1. 수익 기반 보상
        profit = post_state_data.get("assets", 0) - pre_state_data.get("assets", 0)
        reward = profit * reward_weights["profit"]

        # 1.1. 매출 변화 기반 보상 (추가)
        revenue_change = post_state_data.get(
            "revenue_this_turn", 0
        ) - pre_state_data.get(
            "revenue_this_turn", 0
        )  # Assuming pre_revenue_this_turn is available
        reward += revenue_change * reward_weights["revenue_change"]

        # 2. 시장 점유율 증가 보상
        market_share_growth = post_state_data.get(
            "market_share", 0
        ) - pre_state_data.get("market_share", 0)
        reward += market_share_growth * reward_weights["market_share_growth"]

        # 3. 생산성 증가 보상
        productivity_growth = post_state_data.get(
            "productivity_factor", 1
        ) - pre_state_data.get("productivity_factor", 1)
        reward += productivity_growth * reward_weights["productivity_growth"]

        return reward
