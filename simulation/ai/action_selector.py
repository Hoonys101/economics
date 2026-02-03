# simulation/ai/action_selector.py

import random
from typing import Any, List, Optional, Tuple
from .q_table_manager import QTableManager  # QTableManager에 의존
from .enums import Personality, Intention  # Personality와 Intention 임포트


class ActionSelector:
    """
    Q-테이블을 기반으로 행동을 선택하는 정책(예: 입실론-그리디)을 관리하는 클래스.
    에이전트의 특성(Personality)을 고려하여 행동 선택에 편향을 줄 수 있다.
    """

    def __init__(self, epsilon: float = 0.1, decay_params: Tuple[float, float, int] = (0.5, 0.05, 700)):
        self.epsilon = epsilon
        self.initial_epsilon = decay_params[0]
        self.final_epsilon = decay_params[1]
        self.decay_steps = decay_params[2]

    def get_epsilon(self, current_tick: int) -> float:
        """Linear Decay based on configured parameters."""
        initial = self.initial_epsilon
        final = self.final_epsilon
        decay_steps = self.decay_steps

        if current_tick >= decay_steps:
            return final

        return initial - (initial - final) * (current_tick / decay_steps)

    def choose_action(
        self,
        q_table_manager: QTableManager,
        state: Tuple,
        actions: List[Any],
        personality: Optional[Personality] = None,
        current_tick: Optional[int] = None
    ) -> Any:
        """
        현재 상태에서 Q-테이블을 보고 최적의 행동을 선택하거나, 탐험을 위해 무작위 행동을 선택한다.
        동일한 Q-값을 가진 여러 최적 행동이 있을 경우, 에이전트의 특성(Personality)에 맞는 행동을 우선적으로 선택한다.

        :param q_table_manager: QTableManager 인스턴스.
        :param state: 현재 상태.
        :param actions: 선택 가능한 행동 목록.
        :param personality: (선택 사항) 에이전트의 특성(Personality).
        :param current_tick: (선택 사항) 동적 엡실론 계산을 위한 현재 틱.
        :return: 선택된 행동.
        """
        if not actions:
            return None  # 선택 가능한 행동이 없으면 None 반환

        epsilon_to_use = self.epsilon
        if current_tick is not None:
            epsilon_to_use = self.get_epsilon(current_tick)

        # 입실론-그리디 정책
        if random.uniform(0, 1) < epsilon_to_use:
            return random.choice(actions)  # 탐험: 무작위 행동 선택
        else:
            # 활용: Q-값이 가장 높은 행동 선택
            q_values = q_table_manager.get_state_q_values(state)

            # 현재 선택 가능한 행동들 중에서만 Q-값 비교
            valid_q_values = {action: q_values.get(action, 0.0) for action in actions}

            if not valid_q_values:  # 유효한 행동이 없으면 무작위 선택
                return random.choice(actions)

            max_q = max(valid_q_values.values())
            best_actions = [
                action for action, q in valid_q_values.items() if q == max_q
            ]

            # --- Personality-based tie-breaking ---
            if personality and best_actions and isinstance(best_actions[0], Intention):
                preferred_intentions = {
                    Personality.MISER: Intention.INCREASE_ASSETS,
                    Personality.STATUS_SEEKER: Intention.SATISFY_SOCIAL_NEED,
                    Personality.GROWTH_ORIENTED: Intention.IMPROVE_SKILLS,
                }
                preferred_action = preferred_intentions.get(personality)
                if preferred_action in best_actions:
                    return preferred_action
            # --- End of personality-based tie-breaking ---

            return random.choice(best_actions)  # 동점일 경우 무작위 선택
