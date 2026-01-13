import logging
import random
from typing import List, Dict, Any, Tuple
from simulation.ai.q_table_manager import QTableManager
from simulation.ai.action_selector import ActionSelector

logger = logging.getLogger(__name__)

class GovernmentAI:
    """
    Intelligent Government AI (Brain Module).
    Learns to maximize public opinion (Approval Rating) and macro stability
    by adjusting fiscal (tax) and monetary (interest rate) policy.

    Implements WO-057-A Spec:
    - 81 States (Inflation, Unemployment, GDP, Debt)
    - 5 Discrete Actions (Dovish, Neutral, Hawkish, Fiscal Ease, Fiscal Tight)
    - Q-Learning Engine
    """

    def __init__(self, government_agent: Any, config_module: Any):
        self.agent = government_agent
        self.config_module = config_module

        # RL Components
        self.q_table = QTableManager()  # State -> Action -> Q-Value
        self.action_selector = ActionSelector(
            epsilon=getattr(config_module, "AI_EPSILON", 0.1)
        )

        # State Tracking
        self.last_state: Tuple = None
        self.last_action_idx: int = None
        self.last_reward: float = 0.0

        # Hyperparameters
        self.gamma = getattr(config_module, "RL_DISCOUNT_FACTOR", 0.95)
        self.alpha = getattr(config_module, "RL_LEARNING_RATE", 0.1)

        # Action Space: 5 Discrete Actions
        # 0: Dovish Pivot (Rate -0.25%)
        # 1: Neutral (Hold)
        # 2: Hawkish Shift (Rate +0.25%)
        # 3: Fiscal Ease (Tax -1.0%)
        # 4: Fiscal Tight (Tax +1.0%)
        self.actions = [0, 1, 2, 3, 4]
        self.ACTION_DOVISH = 0
        self.ACTION_NEUTRAL = 1
        self.ACTION_HAWKISH = 2
        self.ACTION_FISCAL_EASE = 3
        self.ACTION_FISCAL_TIGHT = 4

    def _get_state(self, market_data: Dict[str, Any]) -> Tuple[int, int, int, int]:
        """
        Discretize Macro Indicators into 81 States (3^4).
        Variables: Inflation Gap, Unemployment Gap, GDP Gap, Debt Gap.
        Levels: 0 (Low), 1 (Ideal), 2 (High).
        """
        # 1. Retrieve Targets from Config
        target_inflation = getattr(self.config_module, "TARGET_INFLATION_RATE", 0.02)
        target_unemployment = getattr(self.config_module, "TARGET_UNEMPLOYMENT_RATE", 0.04)

        # 2. Retrieve Current Metrics
        # Inflation: Using Government's shadow tracking or market avg price change
        # Assuming Government has updated price history.
        # If not, we calculate from market_data if available, or rely on agent attributes.
        inflation = 0.0
        if hasattr(self.agent, "price_history_shadow") and len(self.agent.price_history_shadow) >= 2:
            current_p = self.agent.price_history_shadow[-1]
            past_p = self.agent.price_history_shadow[0]  # Oldest in window (1 year)
            if past_p > 0:
                inflation = (current_p - past_p) / past_p

        # Unemployment
        unemployment = 0.0
        # market_data usually contains 'unemployment_rate'
        if "unemployment_rate" in market_data:
            unemployment = market_data["unemployment_rate"]

        # GDP Gap
        current_gdp = market_data.get("total_production", 0.0) # Using production as GDP proxy
        potential_gdp = getattr(self.agent, "potential_gdp", 100.0)
        gdp_gap_val = 0.0
        if potential_gdp > 0:
            gdp_gap_val = (current_gdp - potential_gdp) / potential_gdp

        # Debt Gap
        # Debt Ratio = max(0, -assets) / GDP
        assets = getattr(self.agent, "assets", 0.0)
        debt = max(0.0, -assets)
        debt_ratio = 0.0
        if current_gdp > 0:
            debt_ratio = debt / current_gdp
        debt_gap_val = debt_ratio - 0.60 # Target Debt Ratio 60%

        # 3. Discretize
        # Inflation Gap: I - I*
        inf_gap_val = inflation - target_inflation
        # Thresholds: +/- 1% deviation?
        # Let's use 0.01 (1%) as tolerance
        if inf_gap_val < -0.01:
            s_inf = 0 # Low
        elif inf_gap_val > 0.01:
            s_inf = 2 # High
        else:
            s_inf = 1 # Ideal

        # Unemployment Gap: U - U*
        unemp_gap_val = unemployment - target_unemployment
        # Tolerance: +/- 1%
        if unemp_gap_val < -0.01:
            s_unemp = 0 # Low (Too hot? Good?) -> Usually Low Unemp is Good, but 'Gap' implies deviation.
            # Context: Phillips curve tradeoff. Low unemp might drive inflation.
            # Let's keep it simply descriptive: Low, Ideal, High.
        elif unemp_gap_val > 0.01:
            s_unemp = 2 # High
        else:
            s_unemp = 1 # Ideal

        # GDP Gap: (Y-Y*)/Y*
        # Tolerance: +/- 1%
        if gdp_gap_val < -0.01:
            s_gdp = 0 # Low (Recession)
        elif gdp_gap_val > 0.01:
            s_gdp = 2 # High (Overheating)
        else:
            s_gdp = 1 # Ideal

        # Debt Gap: Ratio - 0.6
        # Tolerance: +/- 5%?
        if debt_gap_val < -0.05:
            s_debt = 0 # Low
        elif debt_gap_val > 0.05:
            s_debt = 2 # High
        else:
            s_debt = 1 # Ideal

        return (s_inf, s_unemp, s_gdp, s_debt)

    def calculate_reward(self, market_data: Dict[str, Any]) -> float:
        """
        Calculate Reward based on Macro Stability.
        R = - ( 0.5*Inf_Gap^2 + 0.4*Unemp_Gap^2 + 0.1*Debt_Gap^2 )
        """
        target_inflation = getattr(self.config_module, "TARGET_INFLATION_RATE", 0.02)
        target_unemployment = getattr(self.config_module, "TARGET_UNEMPLOYMENT_RATE", 0.04)

        # Re-calculate metrics (identical logic to _get_state, but continuous values)
        inflation = 0.0
        if hasattr(self.agent, "price_history_shadow") and len(self.agent.price_history_shadow) >= 2:
            current_p = self.agent.price_history_shadow[-1]
            past_p = self.agent.price_history_shadow[0]
            if past_p > 0:
                inflation = (current_p - past_p) / past_p

        unemployment = market_data.get("unemployment_rate", 0.0)

        current_gdp = market_data.get("total_production", 0.0)
        assets = getattr(self.agent, "assets", 0.0)
        debt = max(0.0, -assets)
        debt_ratio = 0.0
        if current_gdp > 0:
            debt_ratio = debt / current_gdp

        inf_gap = inflation - target_inflation
        unemp_gap = unemployment - target_unemployment
        debt_gap = debt_ratio - 0.60

        # Calculate Reward
        # Minimizing loss -> Maximizing negative weighted sum of squares
        loss = (0.5 * (inf_gap ** 2)) + (0.4 * (unemp_gap ** 2)) + (0.1 * (debt_gap ** 2))
        reward = -loss

        return reward

    def decide_policy(self, market_data: Dict[str, Any], current_tick: int) -> int:
        """
        Main decision method.
        1. Observe Current State (S_t).
        2. Select Action (A_t) using Epsilon-Greedy.
        3. Store context for future learning.
        """
        state = self._get_state(market_data)

        # Action Selection
        action_idx = self.action_selector.choose_action(self.q_table, state, self.actions)

        # Learning happens in update_learning, called separately (or before next decision)
        # We just return the decision here.
        # But to support (S, A, R, S') tuple, we need to track:
        # self.last_state = S_{t-1}
        # self.last_action = A_{t-1}
        # In this method, we are at time T.
        # We store S_t and A_t as 'last' AFTER the caller has processed the learning step.
        # Wait, if update_learning is called externally, it needs access to 'last' values.
        # We update them here, assuming learning has already happened for the PREVIOUS step.

        self.last_state = state
        self.last_action_idx = action_idx

        return action_idx

    def update_learning(self, reward: float, market_data: Dict[str, Any]):
        """
        Update Q-Table using the reward from the PREVIOUS action and the CURRENT state.
        Transition: (last_state, last_action, reward, current_state)

        NOTE: 'reward' argument passed by legacy/policy wrapper might be 'approval_rating'.
        We explicitly recalculate the reward using the WO-057-A Macro Stability Formula.
        """
        if self.last_state is None or self.last_action_idx is None:
            return

        # Enforce WO-057-A Reward Logic (Ignoring the passed argument if it's from legacy policy)
        # We recalculate strictly based on current macro indicators.
        real_reward = self.calculate_reward(market_data)

        current_state = self._get_state(market_data)

        # Update Q-Table
        self.q_table.update_q_table(
            state=self.last_state,
            action=self.last_action_idx,
            reward=real_reward,
            next_state=current_state,
            next_actions=self.actions,
            alpha=self.alpha,
            gamma=self.gamma
        )

        logger.debug(
            f"GOV_AI_LEARN | Reward: {real_reward:.5f} (Ignored Input: {reward}) | State: {self.last_state} -> {current_state} | Action: {self.last_action_idx}",
            extra={"tick": self.agent.id} # Using agent ID as proxy if tick not passed
        )

    # Alias for SmartLeviathanPolicy compatibility
    update_learning_with_state = update_learning
