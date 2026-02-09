import pytest
from unittest.mock import MagicMock, patch
from modules.household.engines.lifecycle import LifecycleEngine
from modules.household.api import LifecycleInputDTO
from modules.household.dtos import BioStateDTO, EconStateDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO

def test_lifecycle_aging():
    engine = LifecycleEngine()

    bio_state = BioStateDTO(
        id=1, age=20.0, gender="M", generation=0, is_active=True, needs={}
    )
    econ_state = MagicMock(spec=EconStateDTO)
    config = MagicMock(spec=HouseholdConfigDTO)
    config.ticks_per_year = 100.0

    input_dto = LifecycleInputDTO(
        bio_state=bio_state,
        econ_state=econ_state,
        config=config,
        current_tick=1
    )

    output = engine.process_tick(input_dto)

    assert output.bio_state.age == pytest.approx(20.0 + 0.01)
    assert output.bio_state.is_active is True

@patch('modules.household.engines.lifecycle.random.random')
def test_lifecycle_death_check(mock_random):
    engine = LifecycleEngine()

    # Age 100 -> High death probability (0.50 per year)
    # ticks_per_year = 100 -> 0.005 per tick
    mock_random.return_value = 0.001 # Force death

    bio_state = BioStateDTO(
        id=1, age=100.0, gender="M", generation=0, is_active=True, needs={}
    )
    econ_state = MagicMock(spec=EconStateDTO)
    config = MagicMock(spec=HouseholdConfigDTO)
    config.ticks_per_year = 100.0

    input_dto = LifecycleInputDTO(
        bio_state=bio_state,
        econ_state=econ_state,
        config=config,
        current_tick=1
    )

    output = engine.process_tick(input_dto)

    assert output.bio_state.is_active is False
