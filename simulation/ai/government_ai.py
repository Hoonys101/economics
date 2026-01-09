import logging
import random
from typing import List, Dict, Any, Tuple
from collections import deque
from simulation.ai.enums import PoliticalParty
from simulation.ai.q_table_manager import QTableManager
from simulation.ai.action_selector import ActionSelector

logger = logging.getLogger(__name__)

class GovernmentAI:
    """
    Intelligent Government AI (Policy Actuator).
    Learns to maximize public opinion (Approval Rating) by adjusting fiscal policy.
    Operates under the constraints of the ruling party.
    """

    def __init__(self, government_agent, config_module):
        self.agent = government_agent
        self.config_module = config_module

        # RL Components
        self.q_table = QTableManager() # State -> Action -> Q-Value
        self.action_selector = ActionSelector(epsilon=0.1) # Default epsilon, maybe decay?

        # State Tracking
        self.last_state: Tuple = None
        self.last_action_idx: int = None
        self.last_approval: float = 0.5

        # Hyperparameters
        self.gamma = 0.9
        self.alpha = 0.1

        # Action Space: [FISCAL_EXPANSION, FISCAL_CONTRACTION, DO_NOTHING]
        self.actions = [0, 1, 2]
        self.ACTION_EXPAND = 0
        self.ACTION_CONTRACT = 1
        self.ACTION_HOLD = 2

    def _get_state(self, perceived_opinion: float, gdp_growth: float, ruling_party: PoliticalParty) -> Tuple:
        """
        State Space:
        1. Public Opinion: [LOW (<0.4), MEDIUM (0.4-0.6), HIGH (>0.6)]
        2. GDP Growth: [NEGATIVE, NEUTRAL, POSITIVE]
        3. Ruling Party: [BLUE, RED]
        """
        # 1. Opinion
        if perceived_opinion < 0.4:
            opinion_state = 0
        elif perceived_opinion < 0.6:
            opinion_state = 1
        else:
            opinion_state = 2

        # 2. GDP Growth (Simple trend check, assuming agent knows it or we pass it)
        # We'll use a threshold of +/- 1%
        if gdp_growth < -0.01:
            gdp_state = 0 # Recession
        elif gdp_growth > 0.01:
            gdp_state = 2 # Boom
        else:
            gdp_state = 1 # Stagnation

        # 3. Party
        party_state = 0 if ruling_party == PoliticalParty.BLUE else 1

        return (opinion_state, gdp_state, party_state)

    def decide_policy(self, market_data: Dict[str, Any], current_tick: int) -> int:
        """
        Decide policy action based on state.
        """
        # 1. Get Inputs
        perceived_opinion = self.agent.perceived_public_opinion

        # Calculate GDP Growth
        current_gdp = market_data.get("total_production", 0.0)
        # We need historical GDP to calc growth. Government tracks gdp_history.
        # Use gdp_history[-2] if available
        gdp_growth = 0.0
        if len(self.agent.gdp_history) >= 2:
            prev_gdp = self.agent.gdp_history[-2] # -1 is current (appended in run_welfare_check)
            # Actually run_welfare_check appends current before calling this? No.
            # We need to ensure logic flow.
            # Assuming agent updates gdp_history separately or we use it here.
            # Let's rely on agent.gdp_history.
            if prev_gdp > 0:
                gdp_growth = (current_gdp - prev_gdp) / prev_gdp

        ruling_party = self.agent.ruling_party

        state = self._get_state(perceived_opinion, gdp_growth, ruling_party)
        self.last_state = state

        # 2. Select Action
        action_idx = self.action_selector.choose_action(self.q_table, state, self.actions)
        self.last_action_idx = action_idx

        return action_idx

    def update_learning(self, current_approval: float):
        """
        Update Q-Table based on reward (Change in Approval).
        """
        if self.last_state is None or self.last_action_idx is None:
            return

        # Reward: Change in approval + Absolute level bonus
        # If approval increased, good.
        # If approval is high, good.
        delta = current_approval - self.last_approval

        # Reward Function:
        # Survival is key. High approval is good.
        # R = (Current - 0.5) + (Delta * 5.0)
        # If current is 0.6, reward is 0.1. If dropped from 0.7, Delta is -0.1 -> -0.5. Total -0.4.
        reward = (current_approval - 0.4) * 2.0 + (delta * 10.0)

        # New State (Approximation for Q-Learning update, effectively "next state" is just current reading)
        # We don't have next_state computed yet for the next tick, but Q-learning needs (s, a, r, s').
        # We can treat the *current* situation as s'.
        # However, decide_policy hasn't run for the new tick yet.
        # So we update the PREVIOUS step's transition using CURRENT state.

        # We need to reconstruct the "current" state to use as s'.
        # Since we are inside update_learning, we assume this is called at the end of tick or start of next.
        # Let's assume we can get the current state params.
        # For simplicity, we skip full S' reconstruction and just do Q(S,A) += alpha * (R - Q(S,A))
        # (Bandit style or simplified Q).
        # But let's try to be proper. We need `next_state`.
        # We can pass `next_state` to this method?
        # Or just use the last stored state as S and action A, and assume S' is the state *now*?
        # Yes, we need current inputs to form S'.
        pass

    def update_learning_with_state(self, current_approval: float, market_data: Dict[str, Any]):
        """
        Proper Q-Learning Update.
        """
        if self.last_state is None or self.last_action_idx is None:
            return

        # Calculate Reward
        delta = current_approval - self.last_approval
        reward = (current_approval - 0.5) + (delta * 5.0)

        # Get Next State
        perceived_opinion = self.agent.perceived_public_opinion # Updated
        current_gdp = market_data.get("total_production", 0.0)
        gdp_growth = 0.0
        if len(self.agent.gdp_history) >= 2:
            prev_gdp = self.agent.gdp_history[-2]
            if prev_gdp > 0:
                gdp_growth = (current_gdp - prev_gdp) / prev_gdp

        next_state = self._get_state(perceived_opinion, gdp_growth, self.agent.ruling_party)

        # Update Q-Table
        self.q_table.update_q_table(
            self.last_state,
            self.last_action_idx,
            reward,
            next_state,
            self.actions,
            self.alpha,
            self.gamma
        )

        self.last_approval = current_approval
