"""
DTOs and Protocols for the Labor Market Domain.
Phase 4.1: Transition to Major-Based Matching.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Protocol, runtime_checkable
from modules.simulation.api import AgentID

@dataclass(frozen=True)
class JobOfferDTO:
    """
    Firm's labor demand signaling.
    Updated for Phase 4.1: Major-Matching.
    """
    firm_id: AgentID
    offer_wage: float # Currently float for compatibility, will migrate to int pennies in Phase 4.2
    required_education: int = 0
    quantity: float = 1.0
    
    # Phase 4.1: Major-Matching Extensions
    major: str = "GENERAL" # Domain specificity (e.g., "STEM", "ARTS", "MANUFACTURING")
    
    # Matching Constraints (Optional)
    min_match_score: float = 0.0 # Minimum match multiplier to accept (0.0 - 1.0)

@dataclass(frozen=True)
class JobSeekerDTO:
    """
    Household's labor supply signaling.
    Updated for Phase 4.1: Major-Matching.
    """
    household_id: AgentID
    reservation_wage: float
    education_level: int
    quantity: float = 1.0
    
    # Phase 4.1: Major-Matching Extensions
    major: str = "GENERAL" # Domain specificity (e.g., "STEM", "ARTS")
    secondary_majors: List[str] = None # Optional

@dataclass(frozen=True)
class LaborMarketMatchResultDTO:
    """
    Result of a match between a JobOffer and a JobSeeker.
    """
    employer_id: AgentID
    employee_id: AgentID
    base_wage: float
    matched_wage: float # Adjusted for match quality
    match_score: float # 0.0 to 1.0
    major_compatibility: str # "PERFECT", "PARTIAL", "MISMATCH"
    
@runtime_checkable
class ILaborMarket(Protocol):
    """
    Protocol for the Labor Market.
    """
    def post_job_offer(self, offer: JobOfferDTO) -> None:
        """Registers a job offer."""
        ...
        
    def post_job_seeker(self, seeker: JobSeekerDTO) -> None:
        """Registers a job seeker."""
        ...
        
    def match_market(self, current_tick: int) -> List[LaborMarketMatchResultDTO]:
        """Executes matching for the current tick."""
        ...
