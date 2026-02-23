from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, Tuple, List, Optional, Any, runtime_checkable
from modules.government.dtos import GovernmentStateDTO, GovernmentPolicyDTO

# region: DTOs

@dataclass(frozen=True)
class AIConfigDTO:
    """
    Hyperparameters for the Government AI.
    """
    # Q-Learning Params
    alpha: float = 0.1  # Learning Rate
    gamma: float = 0.95 # Discount Factor
    epsilon: float = 0.1 # Exploration Rate

    # State Space Params
    q_table_filename: str = "q_table_v5_populist.pkl"
    state_version: str = "v5"

    # Reward Function Weights
    w_approval: float = 0.7  # Weight for Approval Rating (Populism)
    w_stability: float = 0.2 # Weight for Macro Stability (Technocracy)
    w_lobbying: float = 0.1  # Weight for Lobbying Compliance (Corruption)

    # Action Constraints
    enable_reflex_override: bool = False # If True, forces Hawkish on high inflation

    # Lobbying Thresholds (Proxy Logic)
    lobbying_threshold_high_tax: float = 0.25 # If > 0.25, Corp pressures for cuts
    lobbying_threshold_high_unemployment: float = 0.05 # If > 0.05, Labor pressures for spending

@dataclass(frozen=True)
class AIStateSnapshotDTO:
    """
    Represents the discrete state used for Q-Learning.
    """
    tick: int
    # 0=Low, 1=Target, 2=High
    inflation_state: int
    unemployment_state: int
    gdp_state: int
    debt_state: int

    # New Political Dimensions
    # 0=Danger(<40%), 1=Safe(40-60%), 2=High(>60%)
    approval_state: int

    # 0=None, 1=CorpPressure(CutTax), 2=LaborPressure(RaiseSpend)
    lobbying_state: int

# endregion

# region: Protocols

@runtime_checkable
class IGovernmentAI(Protocol):
    """
    Interface for the Intelligent Government Brain.
    """
    config: AIConfigDTO

    def decide_policy(self, current_tick: int, state_dto: GovernmentStateDTO) -> int:
        """
        Determines the next policy action index based on the current state.
        """
        ...

    def update_learning(self, current_tick: int, state_dto: GovernmentStateDTO) -> None:
        """
        Performs the Q-Learning update step:
        Q(S, A) <- Q(S, A) + alpha * [R + gamma * max Q(S', A') - Q(S, A)]
        """
        ...

    def save_knowledge(self) -> None:
        """Persists the Q-Table to disk."""
        ...

    def load_knowledge(self) -> None:
        """Loads the Q-Table from disk."""
        ...

@runtime_checkable
class IRewardCalculator(Protocol):
    """
    Strategy for calculating the scalar reward signal.
    """
    def calculate(self, state: GovernmentStateDTO, config: AIConfigDTO) -> float:
        ...

# endregion
