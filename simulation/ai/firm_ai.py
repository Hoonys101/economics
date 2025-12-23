import logging
from typing import Any, Dict, List, Tuple, TYPE_CHECKING, Optional

from .api import BaseAIEngine, Intention, Tactic, Aggressiveness
from .q_table_manager import QTableManager
from simulation.schemas import FirmActionVector

if TYPE_CHECKING:
    from simulation.ai_model import AIDecisionEngine

logger = logging.getLogger(__name__)


class FirmAI(BaseAIEngine):
    """
    기업 에이전트를 위한 AI 엔진.
    Architecture V2: Multi-Channel Aggressiveness Output
    """

    # Discrete Aggressiveness Levels for Q-Learning
    AGGRESSIVENESS_LEVELS = [0.0, 0.25, 0.5, 0.75, 1.0]

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
        
        # New Q-Table Managers for specific channels
        self.q_sales = QTableManager()
        self.q_hiring = QTableManager()
        
        # State Tracking
        self.last_sales_state: Optional[Tuple] = None
        self.last_hiring_state: Optional[Tuple] = None
        self.last_sales_action_idx: Optional[int] = None
        self.last_hiring_action_idx: Optional[int] = None

    def set_ai_decision_engine(self, engine: "AIDecisionEngine"):
        self.ai_decision_engine = engine

    def _get_common_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        Common state features shared across channels.
        Includes: Profitability, Inventory Level, Cash Level
        """
        # 1. Inventory Level (0=Empty, 1=Target, 2=Over)
        target = agent_data.get("production_target", 100)
        curr = agent_data.get("inventory", {}).get(agent_data.get("specialization", "food"), 0)
        inv_ratio = curr / target if target > 0 else 0
        inv_idx = self._discretize(inv_ratio, [0.2, 0.5, 0.8, 1.0, 1.2, 1.5])

        # 2. Cash Level (Relative to costs/standard)
        # Simplified: Just log scale or relative
        cash = agent_data.get("assets", 0)
        cash_idx = self._discretize(cash, [100, 500, 1000, 5000, 10000])

        return (inv_idx, cash_idx)

    def decide_action_vector(
        self,
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> FirmActionVector:
        """
        Decide aggressiveness for each channel independently.
        """
        state = self._get_common_state(agent_data, market_data)
        self.last_sales_state = state
        self.last_hiring_state = state

        # 1. Sales Channel
        sales_actions = list(range(len(self.AGGRESSIVENESS_LEVELS))) # Indices
        sales_action_idx = self.action_selector.choose_action(
            self.q_sales, state, sales_actions
        )
        self.last_sales_action_idx = sales_action_idx
        sales_agg = self.AGGRESSIVENESS_LEVELS[sales_action_idx]

        # 2. Hiring Channel
        hiring_actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
        hiring_action_idx = self.action_selector.choose_action(
            self.q_hiring, state, hiring_actions
        )
        self.last_hiring_action_idx = hiring_action_idx
        hiring_agg = self.AGGRESSIVENESS_LEVELS[hiring_action_idx]

        logger.debug(
            f"FIRM_AI_V2 | Firm {self.agent_id} | SalesAgg: {sales_agg} | HireAgg: {hiring_agg}",
            extra={"tags": ["ai_v2"]}
        )

        return FirmActionVector(
            sales_aggressiveness=sales_agg,
            hiring_aggressiveness=hiring_agg,
            production_aggressiveness=0.5 # Default for now
        )

    def update_learning_v2(
        self,
        reward: float,
        next_agent_data: Dict[str, Any],
        next_market_data: Dict[str, Any],
    ) -> None:
        """
        Update Q-tables for V2 architecture.
        Assuming global reward for now (Profit).
        Future improvement: Channel-specific rewards.
        """
        next_state = self._get_common_state(next_agent_data, next_market_data)
        
        # Update Sales Q-Table
        if self.last_sales_state is not None and self.last_sales_action_idx is not None:
             self.q_sales.update_q_table(
                self.last_sales_state,
                self.last_sales_action_idx,
                reward,
                next_state,
                list(range(len(self.AGGRESSIVENESS_LEVELS))),
                self.base_alpha,
                self.gamma
            )

        # Update Hiring Q-Table
        if self.last_hiring_state is not None and self.last_hiring_action_idx is not None:
            self.q_hiring.update_q_table(
                self.last_hiring_state,
                self.last_hiring_action_idx,
                reward,
                next_state,
                list(range(len(self.AGGRESSIVENESS_LEVELS))),
                self.base_alpha,
                self.gamma
            )

    # Legacy Methods (Required by BaseAIEngine ABC but unused/deprecated)
    def _get_strategic_state(self, a, m): pass
    def _get_tactical_state(self, i, a, m): pass
    def _get_strategic_actions(self): pass
    def _get_tactical_actions(self, i): pass
    def _calculate_reward(self, p, post, a, m): 
        # BaseAIEngine의 Wealth 기반 보상을 우선 사용
        return super()._calculate_reward(p, post, a, m)

