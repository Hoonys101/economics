# simulation/ai/learning_tracker.py

from typing import Any, Dict, Tuple, Deque
from collections import deque

class LearningTracker:
    """
    고급 학습 메커니즘(연속 실패 카운트, 전략 실패 이력)을 관리하고
    동적 학습률을 계산하는 클래스.
    """
    def __init__(self):
        self.consecutive_failures: Dict[Any, int] = {} # 행동별 연속 실패 횟수
        self.major_strategic_failure_history: Deque[Dict[str, Any]] = deque(maxlen=5) # 주요 전략 실패 이력 스택 (최대 5개)

    def record_failure(self, action: Any, is_strategic_failure: bool = False, state_at_failure: Tuple = None, reward_at_failure: float = 0.0, current_turn: int = 0):
        """
        실패를 기록하고 연속 실패 카운트를 업데이트한다.
        :param action: 실패한 행동.
        :param is_strategic_failure: 전략적 실패인지 여부.
        :param state_at_failure: 실패 시점의 상태.
        :param reward_at_failure: 실패 시점의 보상.
        :param current_turn: 현재 턴.
        """
        self.consecutive_failures[action] = self.consecutive_failures.get(action, 0) + 1
        
        if is_strategic_failure:
            self.major_strategic_failure_history.append({
                "state": state_at_failure,
                "action": action,
                "reward": reward_at_failure,
                "turn": current_turn
            })

    def reset_consecutive_failure(self, action: Any):
        """특정 행동의 연속 실패 카운트를 리셋한다."""
        self.consecutive_failures[action] = 0

    def get_learning_alpha(self, base_alpha: float, action: Any, learning_focus: float = 0.5) -> float:
        """
        고급 학습 메커니즘에 따라 동적으로 학습률을 반환한다.
        :param base_alpha: 기본 학습률.
        :param action: 현재 행동.
        :param learning_focus: 학습 초점 (0.0 ~ 1.0, 1.0에 가까울수록 전략 학습에 집중).
        :return: 동적으로 조절된 학습률.
        """
        # 학습 강도 조절 (Learning Intensity Adjustment)
        failure_count = self.consecutive_failures.get(action, 0)
        intensity_factor = (1 + 0.5 * failure_count) # 예시: 실패 횟수에 따라 학습률 증폭

        # 동적 학습 초점 (Dynamic Learning Focus) - 이 부분은 BaseAIEngine에서 전략/전술에 따라 다르게 적용될 것임
        # 여기서는 일단 강도 조절만 반환
        return base_alpha * intensity_factor

