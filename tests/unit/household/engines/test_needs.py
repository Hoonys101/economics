import pytest
from unittest.mock import MagicMock
from modules.household.engines.needs import NeedsEngine
from modules.household.api import NeedsInputDTO
from modules.household.dtos import BioStateDTO, EconStateDTO, SocialStateDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO

def test_needs_update():
    engine = NeedsEngine()

    bio_state = BioStateDTO(id=1, age=20.0, gender="M", generation=0, is_active=True, needs={"survival": 10.0})
    econ_state = MagicMock(spec=EconStateDTO)
    econ_state.durable_assets = [] # No assets
    social_state = MagicMock(spec=SocialStateDTO)
    social_state.desire_weights = {"survival": 1.0}

    config = MagicMock(spec=HouseholdConfigDTO)
    config.base_desire_growth = 1.0
    config.max_desire_value = 100.0
    config.survival_need_death_threshold = 100.0
    config.survival_need_death_ticks_threshold = 5

    input_dto = NeedsInputDTO(
        bio_state=bio_state,
        econ_state=econ_state,
        social_state=social_state,
        config=config,
        current_tick=1,
        goods_data={}
    )

    output = engine.evaluate_needs(input_dto)

    # 10 + 1 (growth) = 11
    assert output.bio_state.needs["survival"] == pytest.approx(11.0)
    assert output.bio_state.is_active is True
