import pytest
import config
from config import registry
from modules.system.api import OriginType

def test_config_hot_swap():
    """
    Verifies that changing a value in GlobalRegistry is immediately reflected
    when accessing config.CONSTANT.
    """
    # 1. Read initial value
    initial_supply = config.INITIAL_MONEY_SUPPLY

    # 2. Update Registry via API
    new_supply = initial_supply + 5000
    registry.set("INITIAL_MONEY_SUPPLY", new_supply, origin=OriginType.USER)

    # 3. Verify Proxy Access
    assert config.INITIAL_MONEY_SUPPLY == new_supply

    # 4. Verify Reset
    registry.reset_to_defaults()
    # Note: reset_to_defaults should revert to SYSTEM/CONFIG level.
    # Assuming initial_supply came from SYSTEM/CONFIG.
    assert config.INITIAL_MONEY_SUPPLY == initial_supply

def test_config_engine_type_access():
    """
    Verifies that EngineType enum is accessible via config proxy.
    """
    from config.defaults import EngineType
    assert config.EngineType == EngineType
    assert config.EngineType.AI_DRIVEN == EngineType.AI_DRIVEN

def test_defaults_loaded():
    """
    Verifies that a value present in config/defaults.py but not in simulation.yaml
    is correctly loaded.
    """
    # FORMULA_TECH_LEVEL is 0.0 in defaults.py and not in simulation.yaml
    assert hasattr(config, "FORMULA_TECH_LEVEL")
    assert config.FORMULA_TECH_LEVEL == 0.0

def test_none_handling():
    """
    Verifies that None values are handled correctly and don't trigger AttributeError.
    """
    registry.set("TEST_NONE_KEY", None, OriginType.CONFIG)
    assert config.TEST_NONE_KEY is None

    with pytest.raises(AttributeError):
        _ = config.REALLY_MISSING_KEY
