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
        self.q_dividend = QTableManager()
        self.q_equity = QTableManager()
        self.q_capital = QTableManager()
        
        # State Tracking
        self.last_sales_state: Optional[Tuple] = None
        self.last_hiring_state: Optional[Tuple] = None
        self.last_dividend_state: Optional[Tuple] = None
        self.last_equity_state: Optional[Tuple] = None
        self.last_capital_state: Optional[Tuple] = None
        self.last_sales_action_idx: Optional[int] = None
        self.last_hiring_action_idx: Optional[int] = None
        self.last_dividend_action_idx: Optional[int] = None
        self.last_equity_action_idx: Optional[int] = None
        self.last_capital_action_idx: Optional[int] = None

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
        self.last_dividend_state = state
        self.last_equity_state = state
        self.last_capital_state = state

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

        # 3. Dividend Channel
        dividend_actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
        dividend_action_idx = self.action_selector.choose_action(
            self.q_dividend, state, dividend_actions
        )
        self.last_dividend_action_idx = dividend_action_idx
        dividend_agg = self.AGGRESSIVENESS_LEVELS[dividend_action_idx]

        # 4. Equity Channel (Buyback/Issuance)
        equity_actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
        equity_action_idx = self.action_selector.choose_action(
            self.q_equity, state, equity_actions
        )
        self.last_equity_action_idx = equity_action_idx
        equity_agg = self.AGGRESSIVENESS_LEVELS[equity_action_idx]

        # 5. Capital Channel (Investment)
        capital_actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
        capital_action_idx = self.action_selector.choose_action(
            self.q_capital, state, capital_actions
        )
        self.last_capital_action_idx = capital_action_idx
        capital_agg = self.AGGRESSIVENESS_LEVELS[capital_action_idx]

        logger.debug(
            f"FIRM_AI_V2 | Firm {self.agent_id} | Sales: {sales_agg} | Hire: {hiring_agg} | Div: {dividend_agg} | Eq: {equity_agg} | Cap: {capital_agg}",
            extra={"tags": ["ai_v2"]}
        )

        return FirmActionVector(
            sales_aggressiveness=sales_agg,
            hiring_aggressiveness=hiring_agg,
            production_aggressiveness=0.5, # Default for now
            dividend_aggressiveness=dividend_agg,
            equity_aggressiveness=equity_agg,
            capital_aggressiveness=capital_agg
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

        # Update Dividend Q-Table
        if self.last_dividend_state is not None and self.last_dividend_action_idx is not None:
            self.q_dividend.update_q_table(
                self.last_dividend_state,
                self.last_dividend_action_idx,
                reward,
                next_state,
                list(range(len(self.AGGRESSIVENESS_LEVELS))),
                self.base_alpha,
                self.gamma
            )

        # Update Equity Q-Table
        if self.last_equity_state is not None and self.last_equity_action_idx is not None:
            self.q_equity.update_q_table(
                self.last_equity_state,
                self.last_equity_action_idx,
                reward,
                next_state,
                list(range(len(self.AGGRESSIVENESS_LEVELS))),
                self.base_alpha,
                self.gamma
            )

        # Update Capital Q-Table
        if self.last_capital_state is not None and self.last_capital_action_idx is not None:
            self.q_capital.update_q_table(
                self.last_capital_state,
                self.last_capital_action_idx,
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
    def _calculate_reward(
        self,
        pre_state_data: Dict[str, Any],
        post_state_data: Dict[str, Any],
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> float:
        """
        기업 보상 함수:
        1. Wealth Delta (현금 + 재고 가치 증분)
        2. Market Price Incentive (주가 부양 유인 - 경영권 방어 대리)
        """
        # 1. 자산 증분 (기본: 수익성)
        wealth_delta = super()._calculate_reward(
            pre_state_data, post_state_data, agent_data, market_data
        )

        # 2. 주가 기반 보상 (시가총액 대리 지표)
        stock_market_data = market_data.get("stock_market", {})
        firm_item_id = f"stock_{self.agent_id}"
        
        market_price: float = 0.0
        if firm_item_id in stock_market_data:
            market_price = stock_market_data[firm_item_id].get("avg_price", 0.0)
        
        if market_price <= 0:
            # 주가가 없는 경우 장부가(BPS) 기준
            total_shares = post_state_data.get("total_shares", 1)
            market_price = post_state_data.get("assets", 0) / total_shares if total_shares > 0 else 10.0

        # 주가 자체의 수준에 가중치를 두어 "높은 기업 가치 유지"에 보상
        # wealth_delta에 비해 너무 크지 않도록 스케일링 (예: 자산 1000일 때 주가 10이면 1 정도)
        price_reward_val = float(market_price) * 0.5

        # 최종 보상 = 자산 증분 + 가치 유지 보상
        # 가계가 주식을 선호하도록 배당을 주는 행위가 주가를 올린다면, 
        # 자산 감소(wealth_delta 음수)를 주가 상승(price_reward 양수)이 상쇄하도록 유도
        return wealth_delta + price_reward_val

