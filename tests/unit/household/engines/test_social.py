import pytest
from unittest.mock import MagicMock
from modules.household.engines.social import SocialEngine
from modules.household.api import SocialInputDTO
from modules.household.dtos import SocialStateDTO, EconStateDTO, BioStateDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO
from simulation.ai.enums import Personality, PoliticalParty
from modules.system.api import DEFAULT_CURRENCY

def test_social_status_update():
    engine = SocialEngine()

    social_state = MagicMock(spec=SocialStateDTO)
    # Mocking attributes that are copied
    social_state.copy.return_value = MagicMock(spec=SocialStateDTO)

    econ_state = MagicMock(spec=EconStateDTO)
    econ_state.wallet = MagicMock()
    econ_state.wallet.get_balance.return_value = 1000.0
    bio_state = MagicMock(spec=BioStateDTO)

    config = MagicMock(spec=HouseholdConfigDTO)
    config.social_status_asset_weight = 0.5
    config.social_status_luxury_weight = 0.5

    all_items = {"luxury_car": 1.0}

    input_dto = SocialInputDTO(
        social_state=social_state,
        econ_state=econ_state,
        bio_state=bio_state,
        all_items=all_items,
        config=config,
        current_tick=1
    )

    output = engine.update_status(input_dto)

    # Check the updated state
    # Since we mocked copy(), the output state is the mock returned by copy()
    # We should assert that social_status was set on it.
    assert output.social_state.social_status == 500.5
