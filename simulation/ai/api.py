# simulation/ai/api.py

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
# import random # ActionSelector로 이동

# 새로 추가될 모듈 임포트
from .q_table_manager import QTableManager
from .action_selector import ActionSelector
from .learning_tracker import LearningTracker
from .enums import Intention, Tactic, Personality # Import enums from new file

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from simulation.ai_model import AIDecisionEngine # For type hinting only, to avoid circular import

# BaseAIEngine 추상 클래스 정의 (수정)
class BaseAIEngine(ABC):
    """
    모든 AI 에이전트(가계, 기업)의 공통적인 학습 메커니즘을 추상화한 기본 클래스.
    Q-러닝 알고리즘의 핵심 기능과 학습 프로세스를 정의한다.
    관심사 분리를 위해 QTableManager, ActionSelector, LearningTracker를 조합한다.
    """
    def __init__(self, agent_id: str, gamma: float = 0.9, epsilon: float = 0.1, base_alpha: float = 0.1, learning_focus: float = 0.5, ai_decision_engine: Optional['AIDecisionEngine'] = None):
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
        self.learning_focus = learning_focus # 새로운 파라미터
        self.ai_decision_engine = ai_decision_engine # AIDecisionEngine 인스턴스 저장

        self.q_table_manager_strategy = QTableManager() # 전략 Q-테이블
        self.q_table_manager_tactic = QTableManager()   # 전술 Q-테이블

        self.action_selector = ActionSelector(epsilon=epsilon)
        self.learning_tracker = LearningTracker()

    @abstractmethod
    def _get_strategic_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        전략 AI가 사용할 에이전트의 거시적 상태를 반환한다.
        """
        pass

    @abstractmethod
    def _get_tactical_state(self, intention: Intention, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
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
    def _get_tactical_actions(self, intention: Intention) -> List[Tactic]:
        """
        주어진 Intention에 대해 전술 AI가 선택할 수 있는 Tactic 목록을 정의한다.
        """
        pass

    @abstractmethod
    def _calculate_reward(self, pre_state_data: Dict[str, Any], post_state_data: Dict[str, Any], agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """
        행동의 결과로 얻어지는 보상을 계산한다.
        자산 변화율과 욕구 감소율을 기반으로 한다.
        AIDecisionEngine의 예측 보상을 선택적으로 통합한다.
        """
        pass

    def decide_and_learn(self, agent_data: Dict[str, Any], market_data: Dict[str, Any], pre_state_data: Dict[str, Any], personality: Optional[Personality] = None) -> Tactic:
        """
        AI의 의사결정 흐름을 관장하고 학습을 수행한다.
        :param agent_data: 현재 턴의 에이전트 데이터.
        :param market_data: 현재 턴의 시장 데이터.
        :param pre_state_data: 이전 턴의 에이전트 데이터 (보상 계산용).
        :param personality: (선택 사항) 에이전트의 특성.
        :return: 최종 선택된 Tactic.
        """
        # 1. 전략 AI 의사결정
        strategic_state = self._get_strategic_state(agent_data, market_data)
        strategic_actions = self._get_strategic_actions()
        logger.debug(f"AI_DECISION | Agent {self.agent_id} - Strategic State: {strategic_state}, Strategic Actions: {[action.name for action in strategic_actions]}", extra={'tags': ['ai_decision']})
        
        chosen_intention = self.action_selector.choose_action(
            self.q_table_manager_strategy, strategic_state, strategic_actions, personality=personality
        )
        self.chosen_intention = chosen_intention # Store chosen intention
        logger.debug(f"AI_DECISION | Agent {self.agent_id} - Chosen Intention: {chosen_intention.name if chosen_intention else 'None'}", extra={'tags': ['ai_decision']})
        
        if chosen_intention is None:
            return Tactic.DO_NOTHING # 또는 기본 전술

        # 2. 전술 AI 의사결정
        tactical_state = self._get_tactical_state(chosen_intention, agent_data, market_data)
        tactical_actions = self._get_tactical_actions(chosen_intention)
        logger.debug(f"AI_DECISION | Agent {self.agent_id} - Tactical State for {chosen_intention.name}: {tactical_state}, Tactical Actions: {[action.name for action in tactical_actions]}", extra={'tags': ['ai_decision']})

        # 전술 선택에는 personality를 사용하지 않음
        chosen_tactic = self.action_selector.choose_action(
            self.q_table_manager_tactic, tactical_state, tactical_actions
        )
        self.last_chosen_tactic = chosen_tactic # Store chosen tactic
        logger.debug(f"AI_DECISION | Agent {self.agent_id} - Chosen Tactic for {chosen_intention.name}: {chosen_tactic.name if chosen_tactic else 'None'}", extra={'tags': ['ai_decision']})

        if chosen_tactic is None:
            return Tactic.DO_NOTHING # 또는 기본 전술

        # 3. 학습 (보상 계산 및 Q-테이블 업데이트)
        # 이 부분은 틱 종료 시점에 호출될 수도 있음. 여기서는 의사결정 후 바로 학습하는 것으로 가정.
        # 실제 시뮬레이션에서는 틱 종료 후 모든 에이전트의 행동 결과가 반영된 후 보상 계산 및 학습이 일어남.
        # 여기서는 API 설계이므로, 학습 로직이 호출될 수 있음을 보여줌.

        # 임시 보상 계산 (실제로는 틱 종료 후 호출)
        # reward = self._calculate_reward(pre_state_data, agent_data) 

        # Q-테이블 업데이트 로직은 별도의 update_learning 메서드에서 처리하는 것이 더 적합.
        # decide_and_learn은 의사결정만 하고, 학습은 외부에서 호출하는 방식으로 분리.
        
        return chosen_tactic

    def update_learning(self, 
                        strategic_state: Tuple, chosen_intention: Intention, 
                        tactical_state: Tuple, chosen_tactic: Tactic, 
                        reward: float, 
                        next_strategic_state: Tuple, next_tactical_state: Tuple,
                        is_strategic_failure: bool = False, is_tactical_failure: bool = False):
        """
        계층적 Q-러닝의 학습을 수행한다.
        :param strategic_state: 행동 이전의 전략 상태.
        :param chosen_intention: 선택된 Intention.
        :param tactical_state: 행동 이전의 전술 상태.
        :param chosen_tactic: 선택된 Tactic.
        :param reward: 통합 보상.
        :param next_strategic_state: 행동 이후의 전략 상태.
        :param next_tactical_state: 행동 이후의 전술 상태.
        :param is_strategic_failure: 전략적 실패 여부 (큰 손실).
        :param is_tactical_failure: 전술적 실패 여부 (작은 손실).
        """
        # 동적 학습 초점 (Dynamic Learning Focus)
        alpha_strategy = self.base_alpha * self.learning_focus
        alpha_tactic = self.base_alpha * (1.0 - self.learning_focus)

        # 고급 학습 메커니즘: 손실 크기 기반 학습 (Dynamic Learning Focus)
        if is_strategic_failure: # 큰 손실
            alpha_strategy *= 2.0 # 예시
        elif is_tactical_failure: # 작은 손실
            alpha_tactic *= 2.0 # 예시

        # 학습 강도 조절 (Learning Intensity Adjustment) - 연속 실패 횟수 기반
        alpha_strategy_adjusted = self.learning_tracker.get_learning_alpha(alpha_strategy, chosen_intention)
        alpha_tactic_adjusted = self.learning_tracker.get_learning_alpha(alpha_tactic, chosen_tactic)

        # 1. 전술 Q-테이블 업데이트
        self.q_table_manager_tactic.update_q_table(
            tactical_state, chosen_tactic, reward, next_tactical_state, 
            self._get_tactical_actions(chosen_intention), alpha_tactic_adjusted, self.gamma
        )
        # 전술 성공 시 연속 실패 카운트 리셋
        if reward > 0: # 성공의 기준은 보상이 0보다 큰 경우로 가정
            self.learning_tracker.reset_consecutive_failure(chosen_tactic)
        else: # 실패 시 연속 실패 카운트 기록
            self.learning_tracker.record_failure(chosen_tactic, is_strategic_failure=is_strategic_failure, state_at_failure=tactical_state, reward_at_failure=reward)


        # 2. 전략 Q-테이블 업데이트
        self.q_table_manager_strategy.update_q_table(
            strategic_state, chosen_intention, reward, next_strategic_state, 
            self._get_strategic_actions(), alpha_strategy_adjusted, self.gamma
        )
        # 전략 성공 시 연속 실패 카운트 리셋
        if reward > 0: # 성공의 기준은 보상이 0보다 큰 경우로 가정
            self.learning_tracker.reset_consecutive_failure(chosen_intention)
        else: # 실패 시 연속 실패 카운트 기록
            self.learning_tracker.record_failure(chosen_intention, is_strategic_failure=is_strategic_failure, state_at_failure=strategic_state, reward_at_failure=reward)

    def save_models(self, db_path: str):
        """모든 Q-테이블을 데이터베이스에 저장한다."""
        self.q_table_manager_strategy.save_to_db(db_path, self.agent_id, 'strategy')
        self.q_table_manager_tactic.save_to_db(db_path, self.agent_id, 'tactic')

    def load_models(self, db_path: str):
        """데이터베이스에서 모든 Q-테이블을 로드한다."""
        self.q_table_manager_strategy.load_from_db(db_path, self.agent_id, 'strategy', Intention)
        self.q_table_manager_tactic.load_from_db(db_path, self.agent_id, 'tactic', Tactic)

    def set_ai_decision_engine(self, ai_decision_engine: 'AIDecisionEngine'):
        """
        AIDecisionEngine 인스턴스를 설정한다.
        """
        self.ai_decision_engine = ai_decision_engine