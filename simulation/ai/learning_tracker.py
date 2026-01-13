import logging
from typing import Dict, Any, Tuple, Union
from collections import defaultdict

from .enums import Intention, Tactic, Aggressiveness

logger = logging.getLogger(__name__)


class LearningTracker:
    """
    AI 에이전트의 학습 진행 상황, 특히 연속 실패를 추적하고 이에 따라 학습률을 동적으로 조정하는 클래스.
    """

    def __init__(self, failure_threshold: int = 3, alpha_multiplier: float = 1.5):
        """
        LearningTracker를 초기화합니다.

        Args:
            failure_threshold (int): 학습률을 높이기 시작하는 연속 실패 횟수 임계값.
            alpha_multiplier (float): 연속 실패 시 기본 학습률에 곱할 값.
        """
        self.history: Dict[int, Dict[str, Any]] = {}
        self.consecutive_failures: Dict[
            Union[Intention, Tuple[Tactic, Aggressiveness]], int
        ] = defaultdict(int)
        self.failure_threshold = failure_threshold
        self.alpha_multiplier = alpha_multiplier

    def track_learning_progress(
        self, tick: int, agent_id: str, q_table_change: float, reward: float
    ):
        """
        특정 틱에서 에이전트의 학습 관련 지표를 기록합니다.
        """
        if tick not in self.history:
            self.history[tick] = {}

        if agent_id not in self.history[tick]:
            self.history[tick][agent_id] = []

        self.history[tick][agent_id].append(
            {
                "q_table_change": q_table_change,
                "reward": reward,
            }
        )
        logger.debug(
            f"TICK {tick} | Agent {agent_id} learning tracked: Q-change={q_table_change:.4f}, Reward={reward:.4f}"
        )

    def record_failure(
        self, action: Union[Intention, Tuple[Tactic, Aggressiveness]], **kwargs
    ):
        """특정 행동의 연속 실패 횟수를 1 증가시킵니다."""
        self.consecutive_failures[action] += 1
        logger.debug(
            f"Failure recorded for action {action}. Consecutive failures: {self.consecutive_failures[action]}"
        )

    def reset_consecutive_failure(
        self, action: Union[Intention, Tuple[Tactic, Aggressiveness]]
    ):
        """특정 행동의 연속 실패 횟수를 0으로 리셋합니다."""
        if self.consecutive_failures[action] > 0:
            logger.debug(
                f"Failures reset for action {action}. Was {self.consecutive_failures[action]}"
            )
            self.consecutive_failures[action] = 0

    def get_learning_alpha(
        self, base_alpha: float, action: Union[Intention, Tuple[Tactic, Aggressiveness]]
    ) -> float:
        """
        연속 실패 횟수에 따라 동적으로 학습률(alpha)을 조정하여 반환합니다.
        실패가 임계값을 초과하면 학습률을 높여 빠른 수정을 유도합니다.
        """
        failures = self.consecutive_failures.get(action, 0)
        if failures >= self.failure_threshold:
            adjusted_alpha = base_alpha * (
                self.alpha_multiplier ** (failures - self.failure_threshold + 1)
            )
            logger.debug(
                f"Adjusting alpha for action {action}. Failures: {failures}, Base alpha: {base_alpha}, Adjusted alpha: {adjusted_alpha}"
            )
            return min(1.0, adjusted_alpha)  # alpha는 1.0을 넘지 않도록 함
        return base_alpha

    def get_summary(self) -> Dict[str, Any]:
        """
        전체 시뮬레이션 동안의 학습 진행 상황에 대한 요약 통계를 반환합니다.
        """
        if not self.history:
            return {"total_ticks_tracked": 0, "message": "No learning data tracked."}

        overall_q_change = 0.0
        overall_reward = 0.0
        total_records = 0

        per_agent_stats = defaultdict(lambda: {"total_q_change": 0.0, "total_reward": 0.0, "record_count": 0})

        for tick, tick_data in self.history.items():
            for agent_id, records in tick_data.items():
                for record in records:
                    q_change = record.get("q_table_change", 0.0)
                    reward = record.get("reward", 0.0)

                    # Aggregate overall stats
                    overall_q_change += q_change
                    overall_reward += reward
                    total_records += 1

                    # Aggregate per-agent stats
                    agent_summary = per_agent_stats[agent_id]
                    agent_summary["total_q_change"] += q_change
                    agent_summary["total_reward"] += reward
                    agent_summary["record_count"] += 1

        # Calculate averages
        avg_q_change = overall_q_change / total_records if total_records > 0 else 0.0
        avg_reward = overall_reward / total_records if total_records > 0 else 0.0

        # Finalize per-agent stats with averages
        for agent_id, stats in per_agent_stats.items():
            count = stats["record_count"]
            stats["avg_q_change"] = stats["total_q_change"] / count if count > 0 else 0.0
            stats["avg_reward"] = stats["total_reward"] / count if count > 0 else 0.0

        summary = {
            "total_ticks_tracked": len(self.history),
            "overall": {
                "record_count": total_records,
                "total_q_table_change": overall_q_change,
                "average_q_table_change": avg_q_change,
                "total_reward": overall_reward,
                "average_reward": avg_reward,
            },
            "per_agent": dict(per_agent_stats),
        }
        return summary
