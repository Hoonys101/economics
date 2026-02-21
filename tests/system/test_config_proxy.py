import pytest
from unittest.mock import MagicMock
from modules.system.config_api import ConfigProxy, ConfigKeyMeta, OriginType
from types import ModuleType

# Dummy defaults module
class DummyDefaults:
    TAX_RATE = 0.1
    MAX_TICKS = 100
    lower_case_key = "ignore me"

def test_bootstrap():
    proxy = ConfigProxy()
    proxy.bootstrap_from_module(DummyDefaults)

    assert proxy.TAX_RATE == 0.1
    assert proxy.MAX_TICKS == 100

    with pytest.raises(AttributeError):
        _ = proxy.MISSING_KEY

def test_override():
    proxy = ConfigProxy()
    proxy.bootstrap_from_module(DummyDefaults)

    # User override
    proxy.set("TAX_RATE", 0.2, OriginType.USER)
    assert proxy.TAX_RATE == 0.2

    # Check if internal registry updated
    # GlobalRegistry access via get_registry() and get_entry()
    entry = proxy.get_registry().get_entry("TAX_RATE")
    assert entry.value == 0.2
    assert entry.origin == OriginType.USER

def test_reset_to_defaults():
    proxy = ConfigProxy()
    proxy.bootstrap_from_module(DummyDefaults)

    proxy.set("TAX_RATE", 0.2, OriginType.USER)
    assert proxy.TAX_RATE == 0.2

    proxy.reset_to_defaults()
    assert proxy.TAX_RATE == 0.1

    # Ensure registry entry is back to SYSTEM origin
    entry = proxy.get_registry().get_entry("TAX_RATE")
    assert entry.value == 0.1
    assert entry.origin == OriginType.SYSTEM

def test_observer():
    proxy = ConfigProxy()
    observer = MagicMock()
    proxy.register_observer(observer)

    proxy.set("NEW_KEY", 123, OriginType.USER)
    observer.on_registry_update.assert_called_with("NEW_KEY", 123, OriginType.USER)

def test_snapshot():
    proxy = ConfigProxy()
    proxy.bootstrap_from_module(DummyDefaults)
    proxy.set("NEW_KEY", 999, OriginType.USER)

    snap = proxy.snapshot()
    assert snap["TAX_RATE"] == 0.1
    assert snap["MAX_TICKS"] == 100
    assert snap["NEW_KEY"] == 999
    # GlobalRegistry snapshot only includes active entries.
    # lower_case_key was NOT added to registry in bootstrap_from_module because of isupper() check.
    assert "lower_case_key" not in snap

def test_get_method():
    proxy = ConfigProxy()
    proxy.bootstrap_from_module(DummyDefaults)

    assert proxy.get("TAX_RATE") == 0.1
    assert proxy.get("MISSING", default=999) == 999

    proxy.set("TAX_RATE", 0.5)
    assert proxy.get("TAX_RATE") == 0.5

def test_lock_mechanism():
    proxy = ConfigProxy()
    # Lock a key
    proxy.set("LOCKED_KEY", 100, OriginType.CONFIG)
    # Use GlobalRegistry lock mechanism
    proxy.get_registry().lock("LOCKED_KEY")

    # Try to overwrite with lower/same priority
    with pytest.raises(PermissionError):
        proxy.set("LOCKED_KEY", 200, OriginType.USER)

    # Overwrite with GOD_MODE
    proxy.set("LOCKED_KEY", 300, OriginType.GOD_MODE)
    assert proxy.LOCKED_KEY == 300
