import pytest
from simulation.dtos.api import JobMatchContextDTO, LaborMatchingResultDTO, FirmPricingStrategyDTO, ZombieFirmPreventionDTO
from modules.labor.api import JobOfferDTO, JobSeekerDTO
from modules.labor.system import execute_labor_matching
from modules.simulation.api import AgentID

def test_zombie_firm_pricing():
    # Placeholder
    pass

def test_labor_matching_efficiency():
    context = JobMatchContextDTO(
        tick=1,
        available_seekers=[
            JobSeekerDTO(household_id=AgentID(1), reservation_wage_pennies=1000, education_level=0, talent_score=1.5),
            JobSeekerDTO(household_id=AgentID(2), reservation_wage_pennies=1200, education_level=0, talent_score=1.0)
        ],
        available_offers=[
            JobOfferDTO(firm_id=AgentID(3), offer_wage_pennies=1100, min_match_score=1.2),
            JobOfferDTO(firm_id=AgentID(4), offer_wage_pennies=1300, min_match_score=1.0)
        ],
        market_panic_index=0.0
    )
    result = execute_labor_matching(context)

    # Seeker 1 has talent 1.5, seeks >= 1000.
    # Seeker 2 has talent 1.0, seeks >= 1200.
    # Offer 1 offers 1100, needs talent >= 1.2
    # Offer 2 offers 1300, needs talent >= 1.0

    # Seeker 1 can take Offer 2 (1300) -> wait, seeker 1 is sorted first because of highest talent!
    # Seeker 1 will match with Offer 2 (highest wage offer)
    # Seeker 2 will match with... nothing, because Offer 1 needs talent >= 1.2 and seeker 2 has 1.0.
    assert AgentID(1) in result.matched_pairs
    assert result.matched_pairs[AgentID(1)] == AgentID(4)
    assert AgentID(2) in result.unmatched_seekers
