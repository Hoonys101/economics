import pytest
import config
from simulation.dtos.api import HouseholdConfigDTO, FirmConfigDTO
from simulation.utils.config_factory import create_config_dto

def test_household_config_parity():
    """Ensure all fields in HouseholdConfigDTO exist in config.py."""
    try:
        create_config_dto(config, HouseholdConfigDTO)
    except AttributeError as e:
        pytest.fail(f"HouseholdConfigDTO parity check failed: {e}")

def test_firm_config_parity():
    """Ensure all fields in FirmConfigDTO exist in config.py."""
    try:
        create_config_dto(config, FirmConfigDTO)
    except AttributeError as e:
        pytest.fail(f"FirmConfigDTO parity check failed: {e}")
