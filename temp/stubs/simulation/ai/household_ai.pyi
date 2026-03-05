from .api import Aggressiveness as Aggressiveness, BaseAIEngine as BaseAIEngine, Intention as Intention, Tactic as Tactic
from .q_table_manager import QTableManager as QTableManager
from _typeshed import Incomplete
from simulation.ai_model import AIDecisionEngine as AIDecisionEngine
from simulation.schemas import HouseholdActionVector as HouseholdActionVector
from typing import Any

logger: Incomplete

class HouseholdAI(BaseAIEngine):
    """
    가계 에이전트를 위한 AI 엔진.
    Architecture V2: Multi-Channel Aggressiveness Output
    """
    AGGRESSIVENESS_LEVELS: Incomplete
    ai_decision_engine: AIDecisionEngine | None
    q_consumption: dict[str, QTableManager]
    q_work: Incomplete
    q_investment: Incomplete
    last_consumption_states: dict[str, tuple]
    last_consumption_action_idxs: dict[str, int]
    last_work_state: tuple | None
    last_work_action_idx: int | None
    last_investment_state: tuple | None
    last_investment_action_idx: int | None
    def __init__(self, agent_id: str, ai_decision_engine: AIDecisionEngine, gamma: float = 0.9, epsilon: float = 0.1, base_alpha: float = 0.1, learning_focus: float = 0.5) -> None: ...
    def set_ai_decision_engine(self, engine: AIDecisionEngine): ...
    def decide_action_vector(self, agent_data: dict[str, Any], market_data: dict[str, Any], goods_list: list[str]) -> HouseholdActionVector:
        """
        Decide aggressiveness for consumption (per item) and work.
        Includes Phase 4.1 Perceptual Filters and Panic Reaction.
        """
    def decide_reproduction(self, agent_data: dict[str, Any], market_data: dict[str, Any], current_time: int) -> bool:
        """
        Phase 19: Evolutionary Reproduction Decision
        Revised by WO-048 (Adaptive Breeding)
        """
    def update_learning_v2(self, reward: float, next_agent_data: dict[str, Any], next_market_data: dict[str, Any]) -> float:
        """
        Update Household Q-Tables.
        Returns the total accumulated TD-Error (as a proxy for insight gain).
        """
    def decide_time_allocation(self, agent_data: dict[str, Any], spouse_data: dict[str, Any] | None = None, children_data: list[dict[str, Any]] = [], config_module: Any = None) -> dict[str, float]:
        """
        Phase 20 Step 2: Socio-Tech Time Demand Model

        Calculates required hours for Housework and Childcare, applying constraints.
        Returns 'time_budget' dictionary.
        """
