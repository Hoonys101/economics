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
        self.q_investment = QTableManager()  # 주식 투자 적극성 Q-테이블

        # State Tracking
        self.last_consumption_states: Dict[str, Tuple] = {}
        self.last_consumption_action_idxs: Dict[str, int] = {}
        self.last_work_state: Optional[Tuple] = None
        self.last_work_action_idx: Optional[int] = None
        self.last_investment_state: Optional[Tuple] = None
        self.last_investment_action_idx: Optional[int] = None

    def set_ai_decision_engine(self, engine: "AIDecisionEngine"):
        self.ai_decision_engine = engine

    def _get_common_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        Common state: Assets, General Needs, Debt Ratio, Interest Burden
        """
        # 1. Asset Level
        assets = agent_data.get("assets", 0)
        asset_bins = [100.0, 500.0, 2000.0, 10000.0]
        asset_idx = self._discretize(assets, asset_bins)
        
        # 2. Avg Need Level
        needs = agent_data.get("needs", {})
        avg_need = sum(needs.values()) / max(len(needs), 1)
        need_idx = self._discretize(avg_need, [20, 50, 80])

        # 3. Debt Metrics (from market_data injection)
        debt_info = market_data.get("debt_data", {}).get(self.agent_id, {"total_principal": 0.0, "daily_interest_burden": 0.0})
        total_debt = debt_info.get("total_principal", 0.0)
        interest_burden = debt_info.get("daily_interest_burden", 0.0)

        debt_ratio = total_debt / assets if assets > 0 else 0.0
        debt_idx = self._discretize(debt_ratio, [0.1, 0.3, 0.5, 0.8])
        
        # 4. Interest Burden Ratio (vs Asset or Income Proxy)
        # Using asset as income proxy since income is volatile
        burden_ratio = interest_burden / (assets * 0.01 + 1e-9) # Assume 1% daily return as baseline
        burden_idx = self._discretize(burden_ratio, [0.1, 0.2, 0.5])

        return (asset_idx, need_idx, debt_idx, burden_idx)

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

        # Task #6: Maslow Gating (Action Masking)
        needs = agent_data.get("needs", {})
        survival_need = needs.get("survival", 0.0)
        # Use config if available via ai_decision_engine, else fallback
        config_module = getattr(self.ai_decision_engine, "config_module", None)
        survival_threshold = getattr(config_module, "MASLOW_SURVIVAL_THRESHOLD", 50.0)
        is_starving = survival_need > survival_threshold

        for item_id in goods_list:
            if item_id not in self.q_consumption:



                self.q_consumption[item_id] = QTableManager()
            
            item_state = state 
            self.last_consumption_states[item_id] = item_state
            
            actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
            action_idx = self.action_selector.choose_action(
                self.q_consumption[item_id], item_state, actions
            )
            self.last_consumption_action_idxs[item_id] = action_idx
            agg = self.AGGRESSIVENESS_LEVELS[action_idx]

            # Apply Gating if Starving
            if is_starving and config_module:
                good_info = config_module.GOODS.get(item_id, {})
                utility_effects = good_info.get("utility_effects", {})
                if utility_effects.get("survival", 0) <= 0:
                    agg = 0.0  # Force passive if no survival benefit

            consumption_aggressiveness[item_id] = agg





        # 2. Work Aggressiveness
        self.last_work_state = state
        work_actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
        work_action_idx = self.action_selector.choose_action(
            self.q_work, state, work_actions
        )
        self.last_work_action_idx = work_action_idx
        work_agg = self.AGGRESSIVENESS_LEVELS[work_action_idx]

        # 3. Investment Aggressiveness
        # 자산이 충분할 때만 투자 고려
        assets = agent_data.get("assets", 0)
        if assets >= 500.0 and not is_starving:  # 최소 투자 자산 및 배고프지 않을 때
            self.last_investment_state = state
            inv_actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
            inv_action_idx = self.action_selector.choose_action(
                self.q_investment, state, inv_actions
            )
            self.last_investment_action_idx = inv_action_idx
            investment_agg = self.AGGRESSIVENESS_LEVELS[inv_action_idx]
        else:
            self.last_investment_state = None
            self.last_investment_action_idx = None
            investment_agg = 0.0

        return HouseholdActionVector(
            consumption_aggressiveness=consumption_aggressiveness,
            work_aggressiveness=work_agg,
            learning_aggressiveness=0.0,
            investment_aggressiveness=investment_agg
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

        # Update Investment Q-Table
        if self.last_investment_state is not None and self.last_investment_action_idx is not None:
            self.q_investment.update_q_table(
                self.last_investment_state,
                self.last_investment_action_idx,
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
        
        # 3. Leisure Utility (Phase 5)
        # agent_data is injected with 'leisure_utility' in engine.py
        leisure_utility = agent_data.get("leisure_utility", 0.0)

        # Use config LEISURE_WEIGHT if available, else default 0.3
        leisure_weight = 0.3
        if self.ai_decision_engine and getattr(self.ai_decision_engine, "config_module", None):
            leisure_weight = getattr(self.ai_decision_engine.config_module, "LEISURE_WEIGHT", 0.3)

        total_reward = (
            (wealth_reward * asset_weight) +
            (need_reduction * growth_weight) +
            (leisure_utility * leisure_weight)
        )
        
        return total_reward
