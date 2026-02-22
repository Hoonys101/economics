import pytest
from unittest.mock import MagicMock
from modules.household.engines.needs import NeedsEngine
from modules.household.dtos import BioStateDTO, EconStateDTO, SocialStateDTO
from modules.household.api import NeedsInputDTO
from modules.simulation.dtos.api import HouseholdConfigDTO

@pytest.fixture
def needs_engine():
    return NeedsEngine()

@pytest.fixture
def base_config():
    config = MagicMock(spec=HouseholdConfigDTO)
    config.base_desire_growth = 1.0
    config.max_desire_value = 100.0
    config.survival_need_death_threshold = 100.0
    config.survival_need_death_ticks_threshold = 10
    return config

@pytest.fixture
def mock_states():
    bio_state = MagicMock(spec=BioStateDTO)
    bio_state.needs = {"survival": 0.0}
    bio_state.spouse_id = None
    bio_state.children_ids = []
    bio_state.copy.return_value = bio_state # Simple copy mock

    econ_state = MagicMock(spec=EconStateDTO)
    econ_state.durable_assets = []

    social_state = MagicMock(spec=SocialStateDTO)
    social_state.desire_weights = {"survival": 1.0}

    return bio_state, econ_state, social_state

def test_needs_growth_single(needs_engine, base_config, mock_states):
    bio_state, econ_state, social_state = mock_states

    input_dto = NeedsInputDTO(
        bio_state=bio_state,
        econ_state=econ_state,
        social_state=social_state,
        config=base_config,
        current_tick=0,
        goods_data={}
    )

    output = needs_engine.evaluate_needs(input_dto)

    # Base growth is 1.0, single person -> survival need should increase by 1.0
    assert output.bio_state.needs["survival"] == 1.0

def test_needs_growth_married(needs_engine, base_config, mock_states):
    bio_state, econ_state, social_state = mock_states
    bio_state.spouse_id = 123  # Married

    input_dto = NeedsInputDTO(
        bio_state=bio_state,
        econ_state=econ_state,
        social_state=social_state,
        config=base_config,
        current_tick=0,
        goods_data={}
    )

    output = needs_engine.evaluate_needs(input_dto)

    # Expected scaling: 1 + 1 = 2 members. Growth should be scaled.
    # Assuming scaling factor is simple sum for now or similar logic.
    # Let's assume the implementation will use household_size * base_growth
    # So 2 * 1.0 = 2.0
    assert output.bio_state.needs["survival"] > 1.0
    # Ideally assert specific value if we know the formula.
    # If formula is linear: 2.0
    # If formula is economies of scale (size^0.7): 2^0.7 * 1.0 = 1.62

    # We will accept any value > 1.0 for now, but strict check later.
    assert output.bio_state.needs["survival"] >= 1.5

def test_needs_growth_married_with_kids(needs_engine, base_config, mock_states):
    bio_state, econ_state, social_state = mock_states
    bio_state.spouse_id = 123
    bio_state.children_ids = [101, 102] # 2 kids

    input_dto = NeedsInputDTO(
        bio_state=bio_state,
        econ_state=econ_state,
        social_state=social_state,
        config=base_config,
        current_tick=0,
        goods_data={}
    )

    output = needs_engine.evaluate_needs(input_dto)

    # Size = 1 + 1 + 2 = 4
    # Expect significantly higher growth
    assert output.bio_state.needs["survival"] > 2.0
