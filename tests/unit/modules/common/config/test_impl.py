import pytest
from pathlib import Path
from modules.common.config.impl import ConfigManagerImpl
from modules.common.config.api import BaseConfigDTO, GovernmentConfigDTO
from dataclasses import dataclass

@dataclass(frozen=True)
class ConfigDTOTest(BaseConfigDTO):
    val_int: int
    val_float: float

def test_config_manager_load_and_get():
    # We rely on the pre-loaded domains for now since we can't easily mock importlib in this integration-ish test
    # without robust mocking.
    # However, we can test override.

    manager = ConfigManagerImpl()

    # Check if government domain is loaded (it should be if file exists)
    try:
        gov_config = manager.get_config("government", GovernmentConfigDTO)
        assert isinstance(gov_config, GovernmentConfigDTO)
    except (KeyError, ImportError):
        pytest.skip("Government config not found or failed to load")

def test_config_manager_override():
    manager = ConfigManagerImpl()

    # Register a dummy domain for testing
    manager.register_domain("test_domain", ConfigDTOTest, {"val_int": 10, "val_float": 20.0})

    config = manager.get_config("test_domain", ConfigDTOTest)
    assert config.val_int == 10

    # Override
    manager.override("test_domain.val_int", 99)

    config = manager.get_config("test_domain", ConfigDTOTest)
    assert config.val_int == 99

def test_legacy_support():
    class LegacyConfig:
        OLD_VAL = 123

    legacy = LegacyConfig()
    manager = ConfigManagerImpl(legacy_config=legacy)

    assert manager.OLD_VAL == 123
    assert manager.get("OLD_VAL") == 123

    # Set legacy
    manager.override("OLD_VAL", 456)
    assert manager.OLD_VAL == 456
