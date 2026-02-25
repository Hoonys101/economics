from _typeshed import Incomplete
from modules.government.ai.api import AIConfigDTO as AIConfigDTO, IGovernmentAI as IGovernmentAI
from modules.government.dtos import GovernmentStateDTO as GovernmentStateDTO
from simulation.ai.action_selector import ActionSelector as ActionSelector
from simulation.ai.q_table_manager import QTableManager as QTableManager
from typing import Any

logger: Incomplete

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
    agent: Incomplete
    config: Incomplete
    q_table: Incomplete
    action_selector: Incomplete
    last_state: tuple | None
    last_action_idx: int | None
    last_reward: float
    gamma: Incomplete
    alpha: Incomplete
    actions: Incomplete
    ACTION_DOVISH: int
    ACTION_NEUTRAL: int
    ACTION_HAWKISH: int
    ACTION_FISCAL_EASE: int
    ACTION_FISCAL_TIGHT: int
    def __init__(self, government_agent: Any, config: AIConfigDTO) -> None: ...
    def save_knowledge(self) -> None:
        """Persists the Q-Table to disk using pickle as per V5 spec."""
    def load_knowledge(self) -> None:
        """Loads the Q-Table from disk using pickle as per V5 spec."""
    def calculate_reward(self, state_dto: GovernmentStateDTO) -> float:
        """
        Calculate Reward based on Populist Spec.
        R = w_app * R_app + w_stab * R_stab + w_lob * R_lob
        """
    def decide_policy(self, current_tick: int, state_dto: GovernmentStateDTO) -> int:
        """
        Determines the next policy action index based on the current state.
        """
    def update_learning(self, current_tick: int, state_dto: GovernmentStateDTO) -> None:
        """
        Update Q-Table using the reward from the PREVIOUS action and the CURRENT state.
        Transition: (last_state, last_action, reward, current_state)
        """
    def update_learning_with_state(self, reward: float, current_tick: int): ...
