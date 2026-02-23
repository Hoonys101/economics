import abc
from .action_selector import ActionSelector as ActionSelector
from .enums import Aggressiveness as Aggressiveness, Intention as Intention, Personality as Personality, Tactic as Tactic
from .learning_tracker import LearningTracker as LearningTracker
from .q_table_manager import QTableManager as QTableManager
from _typeshed import Incomplete
from abc import ABC
from simulation.ai_model import AIDecisionEngine as AIDecisionEngine
from typing import Any

logger: Incomplete

class BaseAIEngine(ABC, metaclass=abc.ABCMeta):
    """
    모든 AI 에이전트(가계, 기업)의 공통적인 학습 메커니즘을 추상화한 기본 클래스.
    Q-러닝 알고리즘의 핵심 기능과 학습 프로세스를 정의한다.
    관심사 분리를 위해 QTableManager, ActionSelector, LearningTracker를 조합한다.
    """
    agent_id: Incomplete
    gamma: Incomplete
    base_alpha: Incomplete
    learning_focus: Incomplete
    ai_decision_engine: Incomplete
    q_table_manager_strategy: QTableManager
    q_table_manager_tactic: QTableManager
    action_selector: ActionSelector
    learning_tracker: LearningTracker
    chosen_intention: Intention | None
    last_chosen_tactic: tuple[Tactic, Aggressiveness] | None
    def __init__(self, agent_id: str, gamma: float = 0.9, epsilon: float = 0.1, base_alpha: float = 0.1, learning_focus: float = 0.5, ai_decision_engine: AIDecisionEngine | None = None) -> None:
        """
        BaseAIEngine의 생성자.
        :param agent_id: 이 AI 엔진이 속한 에이전트의 고유 ID.
        :param gamma: 감가율 (할인율) - 미래 보상의 현재 가치를 얼마나 중요하게 여길지.
        :param epsilon: 탐험율 - 무작위 행동을 선택할 확률.
        :param base_alpha: 기본 학습률.
        :param learning_focus: 학습 초점 (0.0 ~ 1.0, 1.0에 가까울수록 전략 학습에 집중).
        """
    def decide_and_learn(self, agent_data: dict[str, Any], market_data: dict[str, Any], pre_state_data: dict[str, Any], personality: Personality | None = None) -> tuple[Tactic, Aggressiveness]:
        """
        AI의 의사결정 흐름을 관장하고 학습을 수행한다.
        :param agent_data: 현재 턴의 에이전트 데이터.
        :param market_data: 현재 턴의 시장 데이터.
        :param pre_state_data: 이전 턴의 에이전트 데이터 (보상 계산용).
        :param personality: (선택 사항) 에이전트의 특성.
        :return: 최종 선택된 (Tactic, Aggressiveness) 튜플.
        """
    def update_learning(self, tick: int, strategic_state: tuple, chosen_intention: Intention, tactical_state: tuple, chosen_tactic_tuple: tuple[Tactic, Aggressiveness], reward: float, next_strategic_state: tuple, next_tactical_state: tuple, is_strategic_failure: bool = False, is_tactical_failure: bool = False) -> None:
        """
        계층적 Q-러닝의 학습을 수행한다.
        """
    def load_models(self, db_path: str) -> None:
        """데이터베이스에서 모든 Q-테이블을 로드한다."""
    def set_ai_decision_engine(self, ai_decision_engine: AIDecisionEngine) -> None:
        """
        AIDecisionEngine 인스턴스를 설정한다.
        """
