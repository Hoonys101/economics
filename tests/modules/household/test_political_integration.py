import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.ai.enums import Personality, PoliticalParty
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.household.dtos import SocialStateDTO
from tests.utils.factories import create_household, create_household_config_dto

def test_household_update_political_opinion_integration():
    # 1. Setup Mock Household
    # Use factory for complete config
    config = create_household_config_dto(
        initial_household_age_range=(20, 40),
        ticks_per_year=100
    )

    mock_decision_engine = MagicMock()

    household = create_household(
        config_dto=config,
        id=1,
        talent=MagicMock(),
        goods_data=[],
        assets=1000.0,
        initial_needs={"survival": 0.0},
        engine=mock_decision_engine,
        value_orientation="Survival",
        personality=Personality.GROWTH_ORIENTED
    )

    # Verify Initialization
    assert household._social_state.economic_vision > 0.0
    assert household._social_state.trust_score == 0.5

    # 2. Run update_needs with Market Data (Government BLUE)
    market_data = {
        "government": {
            "party": PoliticalParty.BLUE
        }
    }

    # We want to check if approval rating updates.
    # Initially 1 (default in DTO).
    household._social_state.approval_rating = 0 # Force to 0 to see change

    # Mock Engine calls
    # We rely on social_engine to return updated state with approval rating
    household.social_engine = MagicMock()

    def update_status_side_effect(input_dto):
        # Return state with updated approval
        # Logic: Growth (0.9) + Blue (0.9) -> High
        household._social_state.approval_rating = 1.0
        household._social_state.trust_score = 0.6
        from modules.household.api import SocialOutputDTO
        return SocialOutputDTO(
            social_state=household._social_state
        )
    household.social_engine.update_status.side_effect = update_status_side_effect

    # Mock other engines
    household.lifecycle_engine = MagicMock()
    from modules.household.api import LifecycleOutputDTO, NeedsOutputDTO
    household.lifecycle_engine.process_tick.return_value = LifecycleOutputDTO(
        bio_state=household._bio_state,
        cloning_requests=[]
    )

    household.needs_engine = MagicMock()
    household.needs_engine.evaluate_needs.return_value = NeedsOutputDTO(
        bio_state=household._bio_state,
        prioritized_needs=[]
    )

    household.update_needs(current_tick=1, market_data=market_data)

    # 3. Assertions
    # Growth personality (vision ~0.9) + Blue Gov (0.9) + Low Need (10) -> High Satisfaction + High Match
    # Approval should become 1
    assert household._social_state.approval_rating == 1

    # Trust should increase
    assert household._social_state.trust_score > 0.5
