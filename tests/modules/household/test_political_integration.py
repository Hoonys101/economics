import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.ai.enums import Personality, PoliticalParty
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.household.dtos import SocialStateDTO

def test_household_update_political_opinion_integration():
    # 1. Setup Mock Household
    # Minimal config
    config = MagicMock(spec=HouseholdConfigDTO)
    config.initial_household_age_range = (20, 40)
    config.value_orientation_mapping = {}
    config.ticks_per_year = 100
    config.wage_memory_length = 10
    config.price_memory_length = 10
    config.adaptation_rate_normal = 0.1
    config.adaptation_rate_impulsive = 0.2
    config.adaptation_rate_conservative = 0.05
    config.initial_aptitude_distribution = (0.5, 0.1)
    config.conformity_ranges = {}
    config.initial_household_assets_mean = 1000
    config.quality_pref_snob_min = 0.8
    config.quality_pref_miser_max = 0.2
    config.base_desire_growth = 1.0
    config.max_desire_value = 100.0
    config.survival_need_death_threshold = 200.0
    config.social_status_asset_weight = 0.5
    config.social_status_luxury_weight = 0.5
    config.leisure_coeffs = {}
    config.distress_grace_period_ticks = 10
    config.elasticity_mapping = {}

    mock_decision_engine = MagicMock()

    household = Household(
        id=1,
        talent=MagicMock(),
        goods_data=[],
        initial_assets=1000.0,
        initial_needs={"survival": 0.0},
        decision_engine=mock_decision_engine,
        value_orientation="Survival",
        personality=Personality.GROWTH_ORIENTED,
        config_dto=config
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

    # Mock bio/econ component calls to avoid complex logic and side effects
    household.econ_component.work = MagicMock(return_value=(household._econ_state, None))
    household.social_component.update_psychology = MagicMock(
        return_value=(
            household._social_state,
            {"survival": 10.0}, # New needs
            [], # Durable assets
            True # Is Active
        )
    )
    household.bio_component.age_one_tick = MagicMock(return_value=household._bio_state)
    household.econ_component.update_skills = MagicMock(return_value=household._econ_state)

    household.update_needs(current_tick=1, market_data=market_data)

    # 3. Assertions
    # Growth personality (vision ~0.9) + Blue Gov (0.9) + Low Need (10) -> High Satisfaction + High Match
    # Approval should become 1
    assert household._social_state.approval_rating == 1

    # Trust should increase
    assert household._social_state.trust_score > 0.5
