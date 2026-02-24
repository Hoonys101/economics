"""
DTOs and Protocols for the Labor Market Domain.
Phase 4.1: Transition to Major-Based Matching.
Phase 4.2: Labor Market Thaw (Desperation & Talent Signal)
"""
from __future__ import annotations
from typing import List, Optional, Protocol, runtime_checkable, Dict, Any
from dataclasses import dataclass, field
from modules.simulation.api import AgentID
from modules.common.enums import IndustryDomain

@dataclass(frozen=True)
class LaborConfigDTO:
    """
    Configuration DTO for the Labor Domain.
    """
    majors: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class LaborMatchDTO:
    """
    Standardized payload for Labor Market Order Metadata.
    """
    major: IndustryDomain = IndustryDomain.GENERAL
    education_level: int = 0
    secondary_majors: List[IndustryDomain] = field(default_factory=list)
    years_experience: float = 0.0
    min_match_score: float = 0.0
    talent_score: float = 1.0  # Phase 4.2: Talent Signal

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "major": self.major.value if hasattr(self.major, "value") else self.major,
            "education_level": self.education_level,
            "secondary_majors": self.secondary_majors,
            "years_experience": self.years_experience,
            "min_match_score": self.min_match_score,
            "talent_score": self.talent_score,
            "__type": "LaborMatchDTO"
        }

    @classmethod
    def from_metadata(cls, metadata: Dict[str, Any]) -> LaborMatchDTO:
        edu_level = metadata.get("education_level")
        if edu_level is None:
            edu_level = metadata.get("required_education", 0)

        major_str = metadata.get("major", "GENERAL")
        try:
            major = IndustryDomain(major_str)
        except ValueError:
            major = IndustryDomain.GENERAL

        return cls(
            major=major,
            education_level=int(edu_level),
            secondary_majors=metadata.get("secondary_majors", []),
            years_experience=float(metadata.get("years_experience", 0.0)),
            min_match_score=float(metadata.get("min_match_score", 0.0)),
            talent_score=float(metadata.get("talent_score", 1.0))
        )

@dataclass(frozen=True)
class JobOfferDTO:
    """
    Firm's labor demand signaling.
    Updated for Phase 4.1: Major-Matching.
    """
    firm_id: AgentID
    offer_wage_pennies: int
    required_education: int = 0
    quantity: float = 1.0
    
    # Phase 4.1: Major-Matching Extensions
    major: IndustryDomain = IndustryDomain.GENERAL # Domain specificity (e.g., "STEM", "ARTS", "MANUFACTURING")
    
    # Matching Constraints (Optional)
    min_match_score: float = 0.0 # Minimum match multiplier to accept (0.0 - 1.0)
    
    # Wave 3: Hiring Preferences
    min_experience: float = 0.0

    # Phase 4.2: Pre-flight check flag
    is_liquidity_verified: bool = False

@dataclass(frozen=True)
class JobSeekerDTO:
    """
    Household's labor supply signaling.
    Updated for Phase 4.1: Major-Matching.
    """
    household_id: AgentID
    reservation_wage_pennies: int
    education_level: int
    quantity: float = 1.0
    
    # Phase 4.1: Major-Matching Extensions
    major: IndustryDomain = IndustryDomain.GENERAL # Domain specificity (e.g., "STEM", "ARTS")
    secondary_majors: List[IndustryDomain] = field(default_factory=list) # Optional
    
    # Wave 3: Labor Supply Signals
    experience: float = 0.0 # Years of experience in this major

    # Phase 4.2: Talent Signal
    talent_score: float = 1.0

@dataclass(frozen=True)
class LaborMarketMatchResultDTO:
    """
    Result of a match between a JobOffer and a JobSeeker.
    """
    employer_id: AgentID
    employee_id: AgentID
    base_wage_pennies: int
    matched_wage_pennies: int # Adjusted for match quality
    match_score: float # 0.0 to 1.0
    major_compatibility: str # "PERFECT", "PARTIAL", "MISMATCH"
    
    # Wave 3: Bargaining Context
    surplus_pennies: int = 0          # (WTP - Reservation Wage)
    bargaining_power: float = 0.5 # Worker's share of surplus (0.0 - 1.0)
    
@runtime_checkable
class ILaborMarket(Protocol):
    """
    Protocol for the Labor Market.
    """
    def configure(self, config: LaborConfigDTO) -> None:
        """
        Injects configuration into the Labor Market.
        """
        ...

    def post_job_offer(self, offer: JobOfferDTO) -> None:
        """Registers a job offer."""
        ...
        
    def post_job_seeker(self, seeker: JobSeekerDTO) -> None:
        """Registers a job seeker."""
        ...
        
    def match_market(self, current_tick: int) -> List[LaborMarketMatchResultDTO]:
        """Executes matching for the current tick."""
        ...
