from .api import Aggressiveness as Aggressiveness, BaseAIEngine as BaseAIEngine, Intention as Intention, Tactic as Tactic
from .enums import Personality as Personality
from .q_table_manager import QTableManager as QTableManager
from _typeshed import Incomplete
from simulation.ai_model import AIDecisionEngine as AIDecisionEngine
from simulation.firms import Firm as Firm
from simulation.schemas import FirmActionVector as FirmActionVector
from typing import Any

logger: Incomplete

class FirmAI(BaseAIEngine):
    """
    기업 에이전트를 위한 AI 엔진.
    Architecture V2: Multi-Channel Aggressiveness Output
    Refined for Phase 16-B: 6-Channel Vector + Personality Based Rewards.
    """
    AGGRESSIVENESS_LEVELS: Incomplete
    ai_decision_engine: AIDecisionEngine | None
    q_sales: Incomplete
    q_hiring: Incomplete
    q_rd: Incomplete
    q_capital: Incomplete
    q_dividend: Incomplete
    q_debt: Incomplete
    last_state: tuple | None
    last_actions_idx: dict[str, int]
    def __init__(self, agent_id: str, ai_decision_engine: AIDecisionEngine, gamma: float = 0.9, epsilon: float = 0.1, base_alpha: float = 0.1, learning_focus: float = 0.5) -> None: ...
    def set_ai_decision_engine(self, engine: AIDecisionEngine): ...
    def decide_action_vector(self, agent_data: dict[str, Any], market_data: dict[str, Any]) -> FirmActionVector:
        """
        Decide aggressiveness for each channel independently.
        """
    def update_learning_v2(self, reward: float, next_agent_data: dict[str, Any], next_market_data: dict[str, Any]) -> float:
        """
        Update Q-tables for V2 architecture using the same global reward for all channels.
        Returns the maximum absolute TD-Error encountered (proxy for surprise/learning).
        """
    def calculate_reward(self, firm_agent: Firm, prev_state: dict, current_state: dict) -> float:
        """
        Calculate reward based on Firm Personality (WO-027).
        """
