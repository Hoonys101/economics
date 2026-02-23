from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, List, Dict, Any, runtime_checkable, Optional, Tuple
from modules.system.api import CurrencyCode
from modules.common.enums import IndustryDomain

# We import PaymentRequestDTO to ensure Lobbying is a financial transaction
from modules.government.dtos import PaymentRequestDTO

# region: DTOs

@dataclass(frozen=True)
class VoteRecordDTO:
    """
    A single vote cast by an agent (Household) reflecting their satisfaction
    and policy preferences.
    """
    agent_id: int
    tick: int
    approval_value: float  # 0.0 (Strong Disapprove) to 1.0 (Strong Approve)

    # The policy the agent wants to see changed
    primary_grievance: str  # e.g., "HIGH_TAX", "LOW_WELFARE", "INFLATION"

    # Derived from social status/influence.
    # Default is 1.0. High status agents may have 10.0+.
    political_weight: float = 1.0

@dataclass(frozen=True)
class LobbyingEffortDTO:
    """
    Represents a firm's financial investment to influence specific policies.
    This DTO acts as a 'Receipt' for a successful financial transfer.
    """
    firm_id: int
    tick: int
    target_policy: str  # e.g., "CORPORATE_TAX", "SUBSIDY_AGRI"

    # The direction of influence.
    # e.g. -1.0 (Lower Tax), +1.0 (Increase Subsidy)
    desired_shift: float

    # Amount spent on lobbying (Revenue for Gov/Politicians).
    # This MUST match the amount in the associated PaymentRequest.
    investment_pennies: int

@dataclass(frozen=True)
class PoliticalClimateDTO:
    """
    Aggregated state of the political environment.
    This is the input for the Government's Decision Engine.
    """
    tick: int

    # Weighted average of all VoteRecordDTO.approval_value
    overall_approval_rating: float

    # Breakdown of support by party (if applicable)
    party_support_breakdown: Dict[str, float]

    # The most common grievances, sorted by weighted frequency
    top_grievances: List[str]

    # Aggregated financial pressure per policy.
    # Key: Policy Name, Value: Total Pennies Invested * Desired Shift
    # e.g. "CORPORATE_TAX": -500000 (Strong pressure to lower tax)
    lobbying_pressure: Dict[str, float]

# endregion

# region: Protocols

@runtime_checkable
class IVoter(Protocol):
    """Protocol for agents that can vote."""
    id: int
    def cast_vote(self, current_tick: int, government_state: Any) -> VoteRecordDTO:
        ...

@runtime_checkable
class ILobbyist(Protocol):
    """Protocol for entities that can lobby."""
    id: int
    def formulate_lobbying_effort(self, current_tick: int, government_state: Any) -> Optional[Tuple[LobbyingEffortDTO, PaymentRequestDTO]]:
        """
        Returns a LobbyingDTO and the PaymentRequest to fund it.
        Returns None if no lobbying is desired or affordable.
        """
        ...

@runtime_checkable
class IPoliticalOrchestrator(Protocol):
    """
    Manages the political lifecycle: Voting, Lobbying, and Mandate calculation.
    State is reset every election cycle or tick depending on granularity.
    """

    def register_vote(self, vote: VoteRecordDTO) -> None:
        """
        Ingests a single vote from a household.
        Should be called during the 'Political Phase' of the tick.
        """
        ...

    def register_lobbying(self, effort: LobbyingEffortDTO) -> None:
        """
        Ingests a verified lobbying effort.
        CRITICAL: This should only be called AFTER the SettlementSystem
        has confirmed the transfer of 'investment_pennies'.
        """
        ...

    def calculate_political_climate(self, current_tick: int) -> PoliticalClimateDTO:
        """
        Aggregates all registered votes and lobbying efforts to produce a
        snapshot of the political climate (Approval, Pressures).
        """
        ...

    def reset_cycle(self) -> None:
        """Clears votes and lobbying efforts for the next accumulation cycle."""
        ...

# endregion
