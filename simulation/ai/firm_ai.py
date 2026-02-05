import logging
from typing import Any, Dict, List, Tuple, TYPE_CHECKING, Optional

from .api import BaseAIEngine, Intention, Tactic, Aggressiveness
from .enums import Personality
from .q_table_manager import QTableManager
from simulation.schemas import FirmActionVector
from modules.system.api import DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.ai_model import AIDecisionEngine
    from simulation.firms import Firm

logger = logging.getLogger(__name__)


class FirmAI(BaseAIEngine):
    """
    기업 에이전트를 위한 AI 엔진.
    Architecture V2: Multi-Channel Aggressiveness Output
    Refined for Phase 16-B: 6-Channel Vector + Personality Based Rewards.
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
        
        # 6-Channel Q-Tables (WO-027)
        self.q_sales = QTableManager()
        self.q_hiring = QTableManager()
        self.q_rd = QTableManager()     # Innovation
        self.q_capital = QTableManager() # CAPEX
        self.q_dividend = QTableManager()
        self.q_debt = QTableManager()    # Leverage
        
        # State Tracking
        self.last_state: Optional[Tuple] = None
        self.last_actions_idx: Dict[str, int] = {}

    def set_ai_decision_engine(self, engine: "AIDecisionEngine"):
        self.ai_decision_engine = engine

    def _get_common_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        Common state features shared across channels.
        Includes: Profitability, Inventory Level, Cash Level, Debt Metrics
        """
        # 1. Inventory Level (0=Empty, 1=Target, 2=Over)
        target = agent_data.get("production_target", 100)
        curr = agent_data.get("inventory", {}).get(agent_data.get("specialization", "food"), 0)
        inv_ratio = curr / target if target > 0 else 0
        inv_idx = self._discretize(inv_ratio, [0.2, 0.5, 0.8, 1.0, 1.2, 1.5])

        # 2. Cash Level (Relative to costs/standard)
        # Simplified: Just log scale or relative
        assets_raw = agent_data.get("assets", 0)
        cash = assets_raw
        if isinstance(assets_raw, dict):
            if "balances" in assets_raw:
                cash = assets_raw["balances"].get(DEFAULT_CURRENCY, 0.0)
            else:
                cash = assets_raw.get(DEFAULT_CURRENCY, 0.0)

        cash_idx = self._discretize(cash, [100, 500, 1000, 5000, 10000])

        # 3. Debt Ratio
        debt_info = market_data.get("debt_data", {}).get(self.agent_id, {"total_principal": 0.0, "daily_interest_burden": 0.0})
        total_debt = debt_info.get("total_principal", 0.0)
        interest_burden = debt_info.get("daily_interest_burden", 0.0)

        debt_ratio = total_debt / cash if cash > 0 else 0.0
        debt_idx = self._discretize(debt_ratio, [0.1, 0.3, 0.5, 0.8])

        # 4. Interest Burden
        burden_ratio = interest_burden / (cash * 0.01 + 1e-9)
        burden_idx = self._discretize(burden_ratio, [0.1, 0.2, 0.5])

        return (inv_idx, cash_idx, debt_idx, burden_idx)

    def decide_action_vector(
        self,
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> FirmActionVector:
        """
        Decide aggressiveness for each channel independently.
        """
        state = self._get_common_state(agent_data, market_data)
        self.last_state = state

        actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))

        # 1. Sales Channel (Pricing)
        sales_idx = self.action_selector.choose_action(self.q_sales, state, actions)
        self.last_actions_idx['sales'] = sales_idx

        # 2. Hiring Channel (Employment)
        hiring_idx = self.action_selector.choose_action(self.q_hiring, state, actions)
        self.last_actions_idx['hiring'] = hiring_idx

        # 3. R&D Channel (Innovation)
        rd_idx = self.action_selector.choose_action(self.q_rd, state, actions)
        self.last_actions_idx['rd'] = rd_idx

        # 4. Capital Channel (CAPEX)
        cap_idx = self.action_selector.choose_action(self.q_capital, state, actions)
        self.last_actions_idx['capital'] = cap_idx

        # 5. Dividend Channel
        div_idx = self.action_selector.choose_action(self.q_dividend, state, actions)
        self.last_actions_idx['dividend'] = div_idx

        # 6. Debt Channel (Leverage)
        debt_idx = self.action_selector.choose_action(self.q_debt, state, actions)
        self.last_actions_idx['debt'] = debt_idx

        vector = FirmActionVector(
            sales_aggressiveness=self.AGGRESSIVENESS_LEVELS[sales_idx],
            hiring_aggressiveness=self.AGGRESSIVENESS_LEVELS[hiring_idx],
            rd_aggressiveness=self.AGGRESSIVENESS_LEVELS[rd_idx],
            capital_aggressiveness=self.AGGRESSIVENESS_LEVELS[cap_idx],
            dividend_aggressiveness=self.AGGRESSIVENESS_LEVELS[div_idx],
            debt_aggressiveness=self.AGGRESSIVENESS_LEVELS[debt_idx]
        )

        logger.debug(
            f"FIRM_AI_V2 | Firm {self.agent_id} | Vector: {vector}",
            extra={"tags": ["ai_v2"]}
        )

        return vector

    def update_learning_v2(
        self,
        reward: float,
        next_agent_data: Dict[str, Any],
        next_market_data: Dict[str, Any],
    ) -> None:
        """
        Update Q-tables for V2 architecture using the same global reward for all channels.
        """
        if self.last_state is None:
            return

        next_state = self._get_common_state(next_agent_data, next_market_data)
        all_actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
        
        # Update All Channels
        managers = [
            (self.q_sales, 'sales'),
            (self.q_hiring, 'hiring'),
            (self.q_rd, 'rd'),
            (self.q_capital, 'capital'),
            (self.q_dividend, 'dividend'),
            (self.q_debt, 'debt'),
        ]

        for q_mgr, key in managers:
            if key in self.last_actions_idx:
                action_idx = self.last_actions_idx[key]
                q_mgr.update_q_table(
                    self.last_state,
                    action_idx,
                    reward,
                    next_state,
                    all_actions,
                    self.base_alpha,
                    self.gamma
                )

    def calculate_reward(self, firm_agent: "Firm", prev_state: Dict, current_state: Dict) -> float:
        """
        Calculate reward based on Firm Personality (WO-027).
        """
        personality = firm_agent.personality

        # Common Metrics
        current_assets_raw = current_state.get("assets", 0.0)
        current_assets = current_assets_raw
        if isinstance(current_assets_raw, dict):
            if "balances" in current_assets_raw:
                current_assets = current_assets_raw["balances"].get(DEFAULT_CURRENCY, 0.0)
            else:
                current_assets = current_assets_raw.get(DEFAULT_CURRENCY, 0.0)

        prev_assets_raw = prev_state.get("assets", 0.0)
        prev_assets = prev_assets_raw
        if isinstance(prev_assets_raw, dict):
            if "balances" in prev_assets_raw:
                prev_assets = prev_assets_raw["balances"].get(DEFAULT_CURRENCY, 0.0)
            else:
                prev_assets = prev_assets_raw.get(DEFAULT_CURRENCY, 0.0)

        delta_assets = current_assets - prev_assets

        # Net Profit approximation (Asset Change is best proxy for realized profit + cash flow)
        net_profit = delta_assets

        # Brand Awareness Delta
        current_awareness = firm_agent.brand_manager.brand_awareness
        prev_awareness = firm_agent.prev_awareness
        delta_awareness = current_awareness - prev_awareness
        firm_agent.prev_awareness = current_awareness # Update state

        reward = 0.0

        if personality == Personality.BALANCED:
            # Reward = Net_Profit + Brand_Value_Change
            brand_value_change = delta_awareness * current_assets * 0.05
            reward = net_profit + brand_value_change

        elif personality == Personality.GROWTH_HACKER:
            # Reward = (Delta_Market_Share * 100) + (Delta_Avg_Quality * 200) + (Delta_Assets * 0.1)
            # Market Share is tricky to get directly here without context, so we approximate or skip if not passed.
            # However, firm_agent doesn't track market share directly.
            # We will use "Sales Volume" as proxy for market share growth or rely on passed state?
            # WO asks for Delta Market Share. Let's assume we can get it or fallback to Revenue Growth.

            # Using Revenue Growth as proxy for Market Share Delta
            current_revenue = current_state.get("revenue_this_turn", 0.0)
            prev_revenue = firm_agent.last_revenue # This might be from 2 ticks ago if not careful
            # Better: firm_agent.prev_market_share tracked in Firm class?
            # Let's use simple proxy: Delta Revenue * 0.5

            # Quality Delta
            current_quality = current_state.get("base_quality", 1.0)
            prev_quality = firm_agent.prev_avg_quality
            delta_quality = current_quality - prev_quality
            firm_agent.prev_avg_quality = current_quality

            reward = (delta_assets * 0.1) + (delta_quality * 200.0) + (net_profit * 0.01) # Profit matters less

        elif personality == Personality.CASH_COW:
            # Reward = (Dividends_Paid * 2.0) + (Net_Profit * 1.0) + (Free_Cash_Flow * 0.5)
            # Dividends Paid is needed. It's not in agent_data directly unless we track it.
            # We can track it on the firm agent during the tick.
            dividends_paid = getattr(firm_agent, 'dividends_paid_last_tick', 0.0) # Need to add this tracking

            reward = (dividends_paid * 2.0) + (net_profit * 1.0)

        else:
            # Default fallback
            reward = net_profit

        logger.debug(
            f"FIRM_REWARD | Firm {firm_agent.id} ({personality.name}) | Reward={reward:.2f}",
            extra={"agent_id": firm_agent.id}
        )
        return reward

    # Legacy Methods (Required by BaseAIEngine ABC but unused/deprecated)
    def _get_strategic_state(self, a, m): pass
    def _get_tactical_state(self, i, a, m): pass
    def _get_strategic_actions(self): pass
    def _get_tactical_actions(self, i): pass

    def _calculate_reward(self, *args):
        return 0.0 # Deprecated
