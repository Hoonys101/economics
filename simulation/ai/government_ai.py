import logging
import pickle
import os
from typing import List, Dict, Any, Tuple, Optional
from simulation.ai.q_table_manager import QTableManager
from simulation.ai.action_selector import ActionSelector
from modules.government.ai.api import IGovernmentAI, AIConfigDTO
from modules.government.dtos import GovernmentStateDTO

logger = logging.getLogger(__name__)

class GovernmentAI:
    """
    Intelligent Government AI (Brain Module).
    Learns to maximize public opinion (Approval Rating) and macro stability
    by adjusting fiscal (tax) and monetary (interest rate) policy.

    Implements WO-057-A Spec & Wave 5 Populist Spec:
    - 6-Tuple State (Inflation, Unemployment, GDP, Debt, Approval, Lobbying)
    - 5 Discrete Actions (Dovish, Neutral, Hawkish, Fiscal Ease, Fiscal Tight)
    - Q-Learning Engine with Versioned Persistence
    """

    def __init__(self, government_agent: Any, config: AIConfigDTO):
        self.agent = government_agent
        self.config = config

        # RL Components
        self.q_table = QTableManager()  # State -> Action -> Q-Value
        self.action_selector = ActionSelector(
            epsilon=config.epsilon
        )

        # State Tracking
        self.last_state: Optional[Tuple] = None
        self.last_action_idx: Optional[int] = None
        self.last_reward: float = 0.0

        # Hyperparameters
        self.gamma = config.gamma
        self.alpha = config.alpha

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

        # Load Knowledge (V5 Spec)
        self.load_knowledge()

    def save_knowledge(self) -> None:
        """Persists the Q-Table to disk using pickle as per V5 spec."""
        filename = self.config.q_table_filename
        try:
            # Ensure directory exists if needed, but usually running from root
            with open(filename, 'wb') as f:
                pickle.dump(self.q_table.q_table, f)
            logger.info(f"Saved Q-Table to {filename}")
        except Exception as e:
            logger.error(f"Failed to save Q-Table {filename}: {e}")

    def load_knowledge(self) -> None:
        """Loads the Q-Table from disk using pickle as per V5 spec."""
        filename = self.config.q_table_filename
        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as f:
                    data = pickle.load(f)
                    self.q_table.q_table = data
                logger.info(f"Loaded Q-Table from {filename}")
            except Exception as e:
                logger.warning(f"Failed to load Q-Table {filename}: {e}. Starting fresh.")
                self.q_table.q_table = {}
        else:
            logger.info(f"No existing Q-Table {filename}. Starting fresh.")
            self.q_table.q_table = {}

    def _determine_lobbying_state(self, state_dto: GovernmentStateDTO) -> int:
        """
        Determines Lobbying Pressure based on economic conditions.
        0=Neutral, 1=Corp(Cut Tax), 2=Labor(Raise Spend/Cut Tax)
        """
        # Thresholds
        high_tax = self.config.lobbying_threshold_high_tax
        high_unemp = self.config.lobbying_threshold_high_unemployment

        # Check Sensory Data
        if not state_dto.sensory_data:
            return 0

        unemp = state_dto.sensory_data.unemployment_sma
        corp_tax = state_dto.corporate_tax_rate

        # Priority Logic: Crisis (Unemployment) > Profit (Tax)
        if unemp > high_unemp:
            return 2 # Labor Pressure
        if corp_tax > high_tax:
            return 1 # Corp Pressure

        return 0

    def _get_state(self, state_dto: GovernmentStateDTO) -> Tuple[int, int, int, int, int, int]:
        """
        Discretize Macro Indicators into 729 States (3^6).
        Variables: Inflation, Unemployment, GDP Growth, Debt Ratio, Approval, Lobbying.
        """
        if not state_dto.sensory_data:
             # Fallback neutral state if no sensory data
            return (1, 1, 1, 1, 1, 0)

        # 1. Retrieve Targets (Hardcoded or Config? Default to standard)
        target_inflation = 0.02
        target_unemployment = 0.04

        # 2. Retrieve Metrics
        inflation = state_dto.sensory_data.inflation_sma
        unemployment = state_dto.sensory_data.unemployment_sma
        gdp_growth = state_dto.sensory_data.gdp_growth_sma
        approval = state_dto.sensory_data.approval_sma

        # Debt Gap
        current_gdp = state_dto.sensory_data.current_gdp

        # Calculate Debt Ratio
        # Total Debt is in pennies (int), GDP is in dollars (float, usually).
        # We must confirm units. Assuming total_debt is pennies, and GDP is dollars.
        total_debt_dollars = state_dto.total_debt / 100.0

        debt_ratio = (total_debt_dollars / current_gdp) if current_gdp > 0 else 0.0

        # 3. Discretize

        # Inflation (Target +/- 1%)
        if inflation < target_inflation - 0.01: s_inf = 0
        elif inflation > target_inflation + 0.01: s_inf = 2
        else: s_inf = 1

        # Unemployment (Target +/- 1%)
        if unemployment < target_unemployment - 0.01: s_unemp = 0
        elif unemployment > target_unemployment + 0.01: s_unemp = 2
        else: s_unemp = 1

        # GDP Growth
        if gdp_growth < -0.005: s_gdp = 0 # Recession
        elif gdp_growth > 0.02: s_gdp = 2 # Boom
        else: s_gdp = 1

        # Debt Ratio
        # Spec: < 40% (0), 40-80% (1), > 80% (2)
        if debt_ratio < 0.40: s_debt = 0
        elif debt_ratio > 0.80: s_debt = 2
        else: s_debt = 1

        # Approval
        # Spec: < 40% (0), 40-60% (1), > 60% (2)
        if approval < 0.40: s_app = 0
        elif approval > 0.60: s_app = 2
        else: s_app = 1

        # Lobbying
        s_lob = self._determine_lobbying_state(state_dto)

        return (s_inf, s_unemp, s_gdp, s_debt, s_app, s_lob)

    def calculate_reward(self, state_dto: GovernmentStateDTO) -> float:
        """
        Calculate Reward based on Populist Spec.
        R = w_app * R_app + w_stab * R_stab + w_lob * R_lob
        """
        if not state_dto.sensory_data:
            return 0.0

        # Weights
        w_app = self.config.w_approval
        w_stab = self.config.w_stability
        w_lob = self.config.w_lobbying

        # 1. Approval Reward
        approval = state_dto.sensory_data.approval_sma
        r_approval = (approval - 0.5) * 100.0

        # 2. Stability Reward (Penalty)
        target_inf = 0.02
        target_unemp = 0.04
        inf = state_dto.sensory_data.inflation_sma
        unemp = state_dto.sensory_data.unemployment_sma

        # Spec Formula: - (InflationGap^2 + UnemploymentGap^2) * 50
        r_stability = - (((inf - target_inf)**2 + (unemp - target_unemp)**2) * 50.0)

        # 3. Lobbying Reward
        r_lobbying = 0.0
        if self.last_state:
            # last_state tuple: (inf, unemp, gdp, debt, app, lob)
            # lob is index 5
            lob_state = self.last_state[5]
            last_action = self.last_action_idx

            # 0=Neutral, 1=Corp, 2=Labor
            # Action 3 = FISCAL_EASE
            # We assume FISCAL_EASE satisfies both Corp (Tax Cut) and Labor (Spend/Cut)
            if lob_state == 1 and last_action == self.ACTION_FISCAL_EASE:
                r_lobbying = 10.0
            elif lob_state == 2 and last_action == self.ACTION_FISCAL_EASE:
                r_lobbying = 10.0

        total_reward = (w_app * r_approval) + (w_stab * r_stability) + (w_lob * r_lobbying)
        return total_reward

    def decide_policy(self, current_tick: int, state_dto: GovernmentStateDTO) -> int:
        """
        Determines the next policy action index based on the current state.
        """
        state = self._get_state(state_dto)

        action_idx = self.action_selector.choose_action(
            self.q_table, state, self.actions, current_tick=current_tick
        )

        # Store context for learning
        self.last_state = state
        self.last_action_idx = action_idx

        return action_idx

    def update_learning(self, current_tick: int, state_dto: GovernmentStateDTO) -> None:
        """
        Update Q-Table using the reward from the PREVIOUS action and the CURRENT state.
        Transition: (last_state, last_action, reward, current_state)
        """
        if self.last_state is None or self.last_action_idx is None:
            return

        reward = self.calculate_reward(state_dto)
        current_state = self._get_state(state_dto)

        self.q_table.update_q_table(
            state=self.last_state,
            action=self.last_action_idx,
            reward=reward,
            next_state=current_state,
            next_actions=self.actions,
            alpha=self.alpha,
            gamma=self.gamma
        )

        logger.debug(
            f"GOV_AI_LEARN | Tick: {current_tick} | Reward: {reward:.2f} "
            f"(App: {state_dto.sensory_data.approval_sma:.2f})"
        )

    # Legacy method wrapper for backward compatibility if needed,
    # but callers should be updated to use update_learning(tick, state_dto)
    def update_learning_with_state(self, reward: float, current_tick: int):
        # This method is now DEPRECATED and should not be used if possible.
        # It lacks state_dto, so it cannot calculate reward or get current state correctly
        # unless we fetch it from self.agent (which is what the old code did).
        # We will try to reconstruct state_dto from self.agent if possible.
        pass
