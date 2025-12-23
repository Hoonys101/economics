import logging
from typing import Any, Dict, List, Tuple, Optional, TYPE_CHECKING

from .api import BaseAIEngine, Intention, Tactic, Aggressiveness
from .q_table_manager import QTableManager
from simulation.schemas import HouseholdActionVector

if TYPE_CHECKING:
    from simulation.ai_model import AIDecisionEngine

logger = logging.getLogger(__name__)


class HouseholdAI(BaseAIEngine):
    """
    가계 에이전트를 위한 AI 엔진.
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
        
        # New Q-Table Managers
        # One Q-Table per Consumption Category (e.g., 'basic_food', 'luxury')
        self.q_consumption: Dict[str, QTableManager] = {} 
        self.q_work = QTableManager()

        # State Tracking
        self.last_consumption_states: Dict[str, Tuple] = {}
        self.last_consumption_action_idxs: Dict[str, int] = {}
        self.last_work_state: Optional[Tuple] = None
        self.last_work_action_idx: Optional[int] = None

    def set_ai_decision_engine(self, engine: "AIDecisionEngine"):
        self.ai_decision_engine = engine

    def _get_common_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        Common state: Assets, General Needs
        """
        # 1. Asset Level
        assets = agent_data.get("assets", 0)
        asset_bins = [100.0, 500.0, 2000.0, 10000.0]
        asset_idx = self._discretize(assets, asset_bins)
        
        # 2. Avg Need Level
        needs = agent_data.get("needs", {})
        avg_need = sum(needs.values()) / max(len(needs), 1)
        need_idx = self._discretize(avg_need, [20, 50, 80])
        
        return (asset_idx, need_idx)

    def decide_action_vector(
        self,
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
        goods_list: List[str] # List of item_ids to decide consumption for
    ) -> HouseholdActionVector:
        """
        Decide aggressiveness for consumption (per item) and work.
        """
        state = self._get_common_state(agent_data, market_data)
        
        # 1. Consumption Aggressiveness
        consumption_aggressiveness = {}
        self.last_consumption_states = {}
        self.last_consumption_action_idxs = {}

        for item_id in goods_list:
            if item_id not in self.q_consumption:
                self.q_consumption[item_id] = QTableManager()
            
            # Create specific state for this item (e.g., specific need inventory?)
            # For now, use common state + item inventory level?
            # Keeping it simple: Use common state
            item_state = state 
            self.last_consumption_states[item_id] = item_state
            
            actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
            action_idx = self.action_selector.choose_action(
                self.q_consumption[item_id], item_state, actions
            )
            self.last_consumption_action_idxs[item_id] = action_idx
            consumption_aggressiveness[item_id] = self.AGGRESSIVENESS_LEVELS[action_idx]

        # 2. Work Aggressiveness
        self.last_work_state = state
        work_actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
        work_action_idx = self.action_selector.choose_action(
            self.q_work, state, work_actions
        )
        self.last_work_action_idx = work_action_idx
        work_agg = self.AGGRESSIVENESS_LEVELS[work_action_idx]

        return HouseholdActionVector(
            consumption_aggressiveness=consumption_aggressiveness,
            work_aggressiveness=work_agg,
            learning_aggressiveness=0.0,
            investment_aggressiveness=0.0
        )

    def update_learning_v2(
        self,
        reward: float,
        next_agent_data: Dict[str, Any],
        next_market_data: Dict[str, Any],
    ) -> None:
        """
        Update Household Q-Tables.
        """
        next_state = self._get_common_state(next_agent_data, next_market_data)
        actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))

        # Update Consumption Q-Tables
        for item_id, q_manager in self.q_consumption.items():
            last_state = self.last_consumption_states.get(item_id)
            last_action = self.last_consumption_action_idxs.get(item_id)
            
            if last_state is not None and last_action is not None:
                q_manager.update_q_table(
                    last_state,
                    last_action,
                    reward,
                    next_state,
                    actions,
                    self.base_alpha,
                    self.gamma
                )

        # Update Work Q-Table
        if self.last_work_state is not None and self.last_work_action_idx is not None:
            self.q_work.update_q_table(
                self.last_work_state,
                self.last_work_action_idx,
                reward,
                next_state,
                actions,
                self.base_alpha,
                self.gamma
            )

    # Legacy Methods
    def _get_strategic_state(self, a, m): pass
    def _get_tactical_state(self, i, a, m): pass
    def _get_strategic_actions(self): pass
    def _get_tactical_actions(self, i): pass
    def _calculate_reward(self, pre_state_data, post_state_data, agent_data, market_data):
        """
        가계 보상: Wealth 증분 + 욕구 해소 만족도.
        """
        # 1. Wealth Delta
        wealth_reward = super()._calculate_reward(pre_state_data, post_state_data, agent_data, market_data)
        
        # 2. Need Satisfaction (욕구 감소량)
        pre_needs = pre_state_data.get("needs", {})
        post_needs = post_state_data.get("needs", {})
        
        need_reduction = sum(pre_needs.values()) - sum(post_needs.values())
        
        # 가중치 적용 (config에서 가져오거나 기본값 사용)
        # 팁: 가계의 경우 욕구 해소가 자산 증식보다 더 강력한 동기일 수 있음.
        asset_weight = 1.0
        growth_weight = 5.0 # 욕구 해소에 더 높은 가중치
        
        total_reward = (wealth_reward * asset_weight) + (need_reduction * growth_weight)
        
        return total_reward
