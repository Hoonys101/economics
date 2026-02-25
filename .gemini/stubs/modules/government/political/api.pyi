from dataclasses import dataclass, field as field
from modules.common.enums import IndustryDomain as IndustryDomain
from modules.government.dtos import PaymentRequestDTO as PaymentRequestDTO
from modules.system.api import CurrencyCode as CurrencyCode
from typing import Any, Protocol

@dataclass(frozen=True)
class VoteRecordDTO:
    """
    A single vote cast by an agent (Household) reflecting their satisfaction
    and policy preferences.
    """
    agent_id: int
    tick: int
    approval_value: float
    primary_grievance: str
    political_weight: float = ...

@dataclass(frozen=True)
class LobbyingEffortDTO:
    """
    Represents a firm's financial investment to influence specific policies.
    This DTO acts as a 'Receipt' for a successful financial transfer.
    """
    firm_id: int
    tick: int
    target_policy: str
    desired_shift: float
    investment_pennies: int

@dataclass(frozen=True)
class PoliticalClimateDTO:
    """
    Aggregated state of the political environment.
    This is the input for the Government's Decision Engine.
    """
    tick: int
    overall_approval_rating: float
    party_support_breakdown: dict[str, float]
    top_grievances: list[str]
    lobbying_pressure: dict[str, float]

class IVoter(Protocol):
    """Protocol for agents that can vote."""
    id: int
    def cast_vote(self, current_tick: int, government_state: Any) -> VoteRecordDTO: ...

class ILobbyist(Protocol):
    """Protocol for entities that can lobby."""
    id: int
    def formulate_lobbying_effort(self, current_tick: int, government_state: Any) -> tuple[LobbyingEffortDTO, PaymentRequestDTO] | None:
        """
        Returns a LobbyingDTO and the PaymentRequest to fund it.
        Returns None if no lobbying is desired or affordable.
        """

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
    def register_lobbying(self, effort: LobbyingEffortDTO) -> None:
        """
        Ingests a verified lobbying effort.
        CRITICAL: This should only be called AFTER the SettlementSystem
        has confirmed the transfer of 'investment_pennies'.
        """
    def calculate_political_climate(self, current_tick: int) -> PoliticalClimateDTO:
        """
        Aggregates all registered votes and lobbying efforts to produce a
        snapshot of the political climate (Approval, Pressures).
        """
    def reset_cycle(self) -> None:
        """Clears votes and lobbying efforts for the next accumulation cycle."""
