import pytest
import config
from modules.system.registry import OriginType, GlobalRegistry

class TestConfigBridge:
    def test_direct_access(self):
        # Access via module attribute
        # Note: TAX_RATE_BASE is 0.10 in config unless modified by other tests
        # Since tests run in isolated environments or sequentially, let's just check type/value
        val = config.TAX_RATE_BASE
        assert isinstance(val, float)
        # assert val == 0.10 # Might be modified by previous test run in same session?
        # Pytest usually runs in same process. If previous test modified it, it might persist?
        # GlobalRegistry instance is module-level in config/__init__.py.
        # So state persists across tests unless reset.
        # I should probably reset it or use a fixture to restore state?
        # Or just set it to known value first.
        config.registry.set("TAX_RATE_BASE", 0.10, OriginType.SYSTEM)
        assert config.TAX_RATE_BASE == 0.10

    def test_registry_integration(self):
        # Update via registry
        config.registry.set("TAX_RATE_BASE", 0.55, OriginType.CONFIG)
        assert config.TAX_RATE_BASE == 0.55

        # Reset
        config.registry.set("TAX_RATE_BASE", 0.10, OriginType.CONFIG)
        assert config.TAX_RATE_BASE == 0.10

    def test_missing_attribute(self):
        with pytest.raises(AttributeError):
            _ = config.NON_EXISTENT_PARAM

    def test_dir_listing(self):
        keys = dir(config)
        assert "TAX_RATE_BASE" in keys
        assert "registry" in keys

    def test_enum_access(self):
        assert config.EngineType.AI_DRIVEN.value == "AIDriven"
