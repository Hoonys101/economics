# simulation/ai/api.py

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

# 새로 추가될 모듈 임포트
from .q_table_manager import QTableManager
from .action_selector import ActionSelector
from .learning_tracker import LearningTracker
from .enums import (
    Intention,
    Tactic,
    Personality,
    Aggressiveness,
)  # Import enums from new file

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from simulation.ai_model import (
        AIDecisionEngine,
    )  # For type hinting only, to avoid circular import


# BaseAIEngine 추상 클래스 정의 (수정)
class BaseAIEngine(ABC):
    """
    모든 AI 에이전트(가계, 기업)의 공통적인 학습 메커니즘을 추상화한 기본 클래스.
    Q-러닝 알고리즘의 핵심 기능과 학습 프로세스를 정의한다.
    관심사 분리를 위해 QTableManager, ActionSelector, LearningTracker를 조합한다.
    """

    def __init__(
        self,
        agent_id: str,
        gamma: float = 0.9,
        epsilon: float = 0.1,
        base_alpha: float = 0.1,
        learning_focus: float = 0.5,
        ai_decision_engine: Optional["AIDecisionEngine"] = None,
    ) -> None:
        """
        BaseAIEngine의 생성자.
        :param agent_id: 이 AI 엔진이 속한 에이전트의 고유 ID.
        :param gamma: 감가율 (할인율) - 미래 보상의 현재 가치를 얼마나 중요하게 여길지.
        :param epsilon: 탐험율 - 무작위 행동을 선택할 확률.
        :param base_alpha: 기본 학습률.
        :param learning_focus: 학습 초점 (0.0 ~ 1.0, 1.0에 가까울수록 전략 학습에 집중).
        """
        self.agent_id = agent_id
        self.gamma = gamma
        self.base_alpha = base_alpha
        self.learning_focus = learning_focus  # 새로운 파라미터
        self.ai_decision_engine = ai_decision_engine  # AIDecisionEngine 인스턴스 저장

        self.q_table_manager_strategy: QTableManager = QTableManager()  # 전략 Q-테이블
        self.q_table_manager_tactic: QTableManager = QTableManager()  # 전술 Q-테이블

        self.action_selector: ActionSelector = ActionSelector(epsilon=epsilon)
        self.learning_tracker: LearningTracker = LearningTracker()
        self.chosen_intention: Optional[Intention] = None
        self.last_chosen_tactic: Optional[Tuple[Tactic, Aggressiveness]] = None

    def _discretize(self, value: float, bins: List[float]) -> int:
        """주어진 값을 구간(bin)에 따라 이산화하여 인덱스를 반환한다."""
        for i, b in enumerate(bins):
            if value <= b:
                return i
        return len(bins)

    @abstractmethod
    def _get_strategic_state(
        self, agent_data: Dict[str, Any], market_data: Dict[str, Any]
    ) -> Tuple:
        """
        전략 AI가 사용할 에이전트의 거시적 상태를 반환한다.
        """
        pass

    @abstractmethod
    def _get_tactical_state(
        self,
        intention: Intention,
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> Tuple:
        """
        전술 AI가 사용할 에이전트의 세부 상태를 반환한다.
        """
        pass

    @abstractmethod
    def _get_strategic_actions(self) -> List[Intention]:
        """
        전략 AI가 선택할 수 있는 Intention 목록을 정의한다.
        """
        pass

    @abstractmethod
    def _get_tactical_actions(
        self, intention: Intention
    ) -> List[Tuple[Tactic, Aggressiveness]]:
        """
        주어진 Intention에 대해 전술 AI가 선택할 수 있는 (Tactic, Aggressiveness) 조합 목록을 정의한다.
        """
        pass

    def _calculate_wealth(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """
        에이전트의 순자산(Total Wealth)을 계산한다.
        Wealth = Cash (Assets) + Sum(Inventory * MarketPrice)
        """
        cash_data = agent_data.get("assets", 0.0)
        if isinstance(cash_data, dict):
            from modules.system.api import DEFAULT_CURRENCY
            cash = cash_data.get(DEFAULT_CURRENCY, 0.0)
        else:
            cash = float(cash_data)

        inventory = agent_data.get("inventory", {})
        
        # 시장 가격 데이터를 활용하여 재고 가치 평가
        # market_data["goods_market"] 에는 {item_id_current_sell_price: price} 형태의 데이터가 있음
        goods_prices = market_data.get("goods_market", {})
        inventory_value = 0.0
        
        for item_id, qty in inventory.items():
            if item_id == "labor": # 노동력은 재고 자산으로 치지 않음 (또는 이미 Cash로 전환됨)
                continue
            
            # 1. 시장 가격 조회
            price_key = f"{item_id}_current_sell_price"
            market_price = goods_prices.get(price_key, market_data.get("avg_goods_price", 0.0))
            
            # [Patch] 2. 최소 가치 보장 (생산 원가 vs 시장가 중 높은 것 선택)
            # AI가 "고용=손해"로 오판하는 것을 방지하기 위해, 시장가가 없어도 생산 원가만큼은 가치로 인정
            production_cost = 10.0 # 임시 하드코딩 (Config나 Goods Data에서 가져오는 것이 이상적임)
            
            valuation_price = max(market_price, production_cost)
            
            inventory_value += qty * valuation_price
            
        return cash + inventory_value

    def _calculate_reward(
        self,
        pre_state_data: Dict[str, Any],
        post_state_data: Dict[str, Any],
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> float:
        """
        기본적인 보상 계산: 순자산(Wealth)의 증분.
        하위 클래스에서 욕구 해소 등을 추가하여 확장할 수 있다.
        """
        pre_wealth = self._calculate_wealth(pre_state_data, market_data)
        post_wealth = self._calculate_wealth(post_state_data, market_data)
        
        return post_wealth - pre_wealth

    def decide_and_learn(
        self,
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
        pre_state_data: Dict[str, Any],
        personality: Optional[Personality] = None,
    ) -> Tuple[Tactic, Aggressiveness]:
        """
        AI의 의사결정 흐름을 관장하고 학습을 수행한다.
        :param agent_data: 현재 턴의 에이전트 데이터.
        :param market_data: 현재 턴의 시장 데이터.
        :param pre_state_data: 이전 턴의 에이전트 데이터 (보상 계산용).
        :param personality: (선택 사항) 에이전트의 특성.
        :return: 최종 선택된 (Tactic, Aggressiveness) 튜플.
        """
        # 1. 전략 AI 의사결정
        strategic_state = self._get_strategic_state(agent_data, market_data)
        strategic_actions = self._get_strategic_actions()
        logger.debug(
            f"AI_DECISION | Agent {self.agent_id} - Strategic State: {strategic_state}, Strategic Actions: {[action.name for action in strategic_actions]}",
            extra={"tags": ["ai_decision"]},
        )

        chosen_intention = self.action_selector.choose_action(
            self.q_table_manager_strategy,
            strategic_state,
            strategic_actions,
            personality=personality,
        )
        self.chosen_intention = chosen_intention  # Store chosen intention
        logger.debug(
            f"AI_DECISION | Agent {self.agent_id} - Chosen Intention: {chosen_intention.name if chosen_intention else 'None'}",
            extra={"tags": ["ai_decision"]},
        )

        if chosen_intention is None:
            return (Tactic.DO_NOTHING, Aggressiveness.NORMAL)

        # 2. 전술 AI 의사결정
        tactical_state = self._get_tactical_state(
            chosen_intention, agent_data, market_data
        )
        tactical_actions = self._get_tactical_actions(chosen_intention)
        # 로그 메시지 수정: 튜플을 올바르게 로깅
        log_tactical_actions = [(a[0].name, a[1].name) for a in tactical_actions]
        logger.debug(
            f"AI_DECISION | Agent {self.agent_id} - Tactical State for {chosen_intention.name}: {tactical_state}, Tactical Actions: {log_tactical_actions}",
            extra={"tags": ["ai_decision"]},
        )

        # 전술 선택에는 personality를 사용하지 않음
        chosen_tactic_tuple = self.action_selector.choose_action(
            self.q_table_manager_tactic, tactical_state, tactical_actions
        )
        self.last_chosen_tactic = chosen_tactic_tuple  # Store chosen tactic tuple
        # 로그 메시지 수정: 튜플을 올바르게 로깅
        log_chosen_tactic = (
            (chosen_tactic_tuple[0].name, chosen_tactic_tuple[1].name)
            if chosen_tactic_tuple
            else ("None", "None")
        )
        logger.debug(
            f"AI_DECISION | Agent {self.agent_id} - Chosen Tactic for {chosen_intention.name}: {log_chosen_tactic}",
            extra={"tags": ["ai_decision"]},
        )

        if chosen_tactic_tuple is None:
            return (Tactic.DO_NOTHING, Aggressiveness.NORMAL)

        return chosen_tactic_tuple

    def update_learning(
        self,
        tick: int,  # 틱 정보 추가
        strategic_state: Tuple,
        chosen_intention: Intention,
        tactical_state: Tuple,
        chosen_tactic_tuple: Tuple[Tactic, Aggressiveness],
        reward: float,
        next_strategic_state: Tuple,
        next_tactical_state: Tuple,
        is_strategic_failure: bool = False,
        is_tactical_failure: bool = False,
    ) -> None:
        """
        계층적 Q-러닝의 학습을 수행한다.
        """
        # 동적 학습 초점 (Dynamic Learning Focus)
        alpha_strategy = self.base_alpha * self.learning_focus
        alpha_tactic = self.base_alpha * (1.0 - self.learning_focus)

        # 고급 학습 메커니즘: 손실 크기 기반 학습 (Dynamic Learning Focus)
        if is_strategic_failure:  # 큰 손실
            alpha_strategy *= 2.0  # 예시
        elif is_tactical_failure:  # 작은 손실
            alpha_tactic *= 2.0  # 예시

        # 학습 강도 조절 (Learning Intensity Adjustment) - 연속 실패 횟수 기반
        alpha_strategy_adjusted = self.learning_tracker.get_learning_alpha(
            alpha_strategy, chosen_intention
        )
        alpha_tactic_adjusted = self.learning_tracker.get_learning_alpha(
            alpha_tactic, chosen_tactic_tuple
        )

        # 1. 전술 Q-테이블 업데이트
        q_change_tactic = self.q_table_manager_tactic.update_q_table(
            tactical_state,
            chosen_tactic_tuple,
            reward,
            next_tactical_state,
            self._get_tactical_actions(chosen_intention),
            alpha_tactic_adjusted,
            self.gamma,
        )
        # 전술 성공 시 연속 실패 카운트 리셋
        if reward > 0:  # 성공의 기준은 보상이 0보다 큰 경우로 가정
            self.learning_tracker.reset_consecutive_failure(chosen_tactic_tuple)
        else:  # 실패 시 연속 실패 카운트 기록
            self.learning_tracker.record_failure(
                chosen_tactic_tuple,
                is_strategic_failure=is_strategic_failure,
                state_at_failure=tactical_state,
                reward_at_failure=reward,
            )

        # 2. 전략 Q-테이블 업데이트
        q_change_strategy = self.q_table_manager_strategy.update_q_table(
            strategic_state,
            chosen_intention,
            reward,
            next_strategic_state,
            self._get_strategic_actions(),
            alpha_strategy_adjusted,
            self.gamma,
        )
        # 전략 성공 시 연속 실패 카운트 리셋
        if reward > 0:  # 성공의 기준은 보상이 0보다 큰 경우로 가정
            self.learning_tracker.reset_consecutive_failure(chosen_intention)
        else:  # 실패 시 연속 실패 카운트 기록
            self.learning_tracker.record_failure(
                chosen_intention,
                is_strategic_failure=is_strategic_failure,
                state_at_failure=strategic_state,
                reward_at_failure=reward,
            )

        # 3. 학습 진행 상황 추적
        total_q_change = q_change_tactic + q_change_strategy
        self.learning_tracker.track_learning_progress(
            tick, self.agent_id, total_q_change, reward
        )

    def load_models(self, db_path: str) -> None:
        """데이터베이스에서 모든 Q-테이블을 로드한다."""
        self.q_table_manager_strategy.load_from_db(
            db_path, self.agent_id, "strategy", Intention
        )
        self.q_table_manager_tactic.load_from_db(
            db_path, self.agent_id, "tactic", Tactic
        )

    def set_ai_decision_engine(self, ai_decision_engine: "AIDecisionEngine") -> None:
        """
        AIDecisionEngine 인스턴스를 설정한다.
        """
        self.ai_decision_engine = ai_decision_engine
