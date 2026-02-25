from dataclasses import dataclass, field as field
from modules.government.dtos import GovernmentPolicyDTO as GovernmentPolicyDTO, GovernmentStateDTO as GovernmentStateDTO
from typing import Protocol

@dataclass(frozen=True)
class AIConfigDTO:
    """
    Hyperparameters for the Government AI.
    """
    alpha: float = ...
    gamma: float = ...
    epsilon: float = ...
    q_table_filename: str = ...
    state_version: str = ...
    w_approval: float = ...
    w_stability: float = ...
    w_lobbying: float = ...
    enable_reflex_override: bool = ...
    lobbying_threshold_high_tax: float = ...
    lobbying_threshold_high_unemployment: float = ...

@dataclass(frozen=True)
class AIStateSnapshotDTO:
    """
    Represents the discrete state used for Q-Learning.
    """
    tick: int
    inflation_state: int
    unemployment_state: int
    gdp_state: int
    debt_state: int
    approval_state: int
    lobbying_state: int

class IGovernmentAI(Protocol):
    """
    Interface for the Intelligent Government Brain.
    """
    config: AIConfigDTO
    def decide_policy(self, current_tick: int, state_dto: GovernmentStateDTO) -> int:
        """
        Determines the next policy action index based on the current state.
        """
    def update_learning(self, current_tick: int, state_dto: GovernmentStateDTO) -> None:
        """
        Performs the Q-Learning update step:
        Q(S, A) <- Q(S, A) + alpha * [R + gamma * max Q(S', A') - Q(S, A)]
        """
    def save_knowledge(self) -> None:
        """Persists the Q-Table to disk."""
    def load_knowledge(self) -> None:
        """Loads the Q-Table from disk."""

class IRewardCalculator(Protocol):
    """
    Strategy for calculating the scalar reward signal.
    """
    def calculate(self, state: GovernmentStateDTO, config: AIConfigDTO) -> float: ...
