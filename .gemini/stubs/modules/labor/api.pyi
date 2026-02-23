from dataclasses import dataclass, field
from modules.common.enums import IndustryDomain as IndustryDomain
from modules.simulation.api import AgentID as AgentID
from typing import Any, Protocol

@dataclass(frozen=True)
class LaborConfigDTO:
    """
    Configuration DTO for the Labor Domain.
    """
    majors: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class LaborMatchDTO:
    """
    Standardized payload for Labor Market Order Metadata.
    """
    major: IndustryDomain = ...
    education_level: int = ...
    secondary_majors: list[IndustryDomain] = field(default_factory=list)
    years_experience: float = ...
    min_match_score: float = ...
    def to_metadata(self) -> dict[str, Any]: ...
    @classmethod
    def from_metadata(cls, metadata: dict[str, Any]) -> LaborMatchDTO: ...

@dataclass(frozen=True)
class JobOfferDTO:
    """
    Firm's labor demand signaling.
    Updated for Phase 4.1: Major-Matching.
    """
    firm_id: AgentID
    offer_wage_pennies: int
    required_education: int = ...
    quantity: float = ...
    major: IndustryDomain = ...
    min_match_score: float = ...
    min_experience: float = ...

@dataclass(frozen=True)
class JobSeekerDTO:
    """
    Household's labor supply signaling.
    Updated for Phase 4.1: Major-Matching.
    """
    household_id: AgentID
    reservation_wage_pennies: int
    education_level: int
    quantity: float = ...
    major: IndustryDomain = ...
    secondary_majors: list[IndustryDomain] = field(default_factory=list)
    experience: float = ...

@dataclass(frozen=True)
class LaborMarketMatchResultDTO:
    """
    Result of a match between a JobOffer and a JobSeeker.
    """
    employer_id: AgentID
    employee_id: AgentID
    base_wage_pennies: int
    matched_wage_pennies: int
    match_score: float
    major_compatibility: str
    surplus_pennies: int = ...
    bargaining_power: float = ...

class ILaborMarket(Protocol):
    """
    Protocol for the Labor Market.
    """
    def configure(self, config: LaborConfigDTO) -> None:
        """
        Injects configuration into the Labor Market.
        """
    def post_job_offer(self, offer: JobOfferDTO) -> None:
        """Registers a job offer."""
    def post_job_seeker(self, seeker: JobSeekerDTO) -> None:
        """Registers a job seeker."""
    def match_market(self, current_tick: int) -> list[LaborMarketMatchResultDTO]:
        """Executes matching for the current tick."""
