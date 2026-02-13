import pytest
from unittest.mock import Mock
from types import SimpleNamespace
from modules.system.telemetry import TelemetryCollector

class MockRegistry:
    def __init__(self, data):
        self._data = data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value, origin=None):
        self._data[key] = value

    def lock(self, key): pass
    def unlock(self, key): pass
    def subscribe(self, observer, keys=None): pass
    def snapshot(self): return {}

@pytest.fixture
def registry():
    data = {
        "economy": SimpleNamespace(m2=1000, gdp=5000),
        "agents": {
            "1": SimpleNamespace(balance=100),
            "2": SimpleNamespace(balance=200)
        },
        "config": {
            "tax": {
                "rate": 0.15
            }
        }
    }
    return MockRegistry(data)

@pytest.fixture
def collector(registry):
    return TelemetryCollector(registry)

def test_subscribe_and_harvest_valid_path(collector):
    # Subscribe to object attribute
    collector.subscribe(["economy.m2"])

    # Subscribe to dict item
    collector.subscribe(["config.tax.rate"])

    # Harvest at tick 1
    snapshot = collector.harvest(1)

    assert snapshot["tick"] == 1
    assert snapshot["data"]["economy.m2"] == 1000
    assert snapshot["data"]["config.tax.rate"] == 0.15
    assert not snapshot["errors"]

def test_subscribe_invalid_path(collector):
    # Invalid root
    collector.subscribe(["missing.value"])

    # Invalid attribute
    collector.subscribe(["economy.inflation"])

    snapshot = collector.harvest(1)

    assert "missing.value" in snapshot["errors"]
    assert "economy.inflation" in snapshot["errors"]
    assert "economy.m2" not in snapshot["data"]

def test_multi_frequency(collector):
    # Macro: freq 1, Micro: freq 10
    collector.subscribe(["economy.m2"], frequency_interval=1)
    collector.subscribe(["agents.1.balance"], frequency_interval=10)

    # Tick 1: Only macro
    snapshot1 = collector.harvest(1)
    assert "economy.m2" in snapshot1["data"]
    assert "agents.1.balance" not in snapshot1["data"]

    # Tick 5: Only macro
    snapshot5 = collector.harvest(5)
    assert "economy.m2" in snapshot5["data"]
    assert "agents.1.balance" not in snapshot5["data"]

    # Tick 10: Both
    snapshot10 = collector.harvest(10)
    assert "economy.m2" in snapshot10["data"]
    assert "agents.1.balance" in snapshot10["data"]
    assert snapshot10["data"]["agents.1.balance"] == 100

def test_unsubscribe(collector):
    collector.subscribe(["economy.m2"])
    snapshot = collector.harvest(1)
    assert "economy.m2" in snapshot["data"]

    collector.unsubscribe(["economy.m2"])
    snapshot = collector.harvest(2)
    assert "economy.m2" not in snapshot["data"]

def test_runtime_error_handling(registry, collector):
    # Setup valid path
    registry._data["dynamic"] = SimpleNamespace(value=10)
    collector.subscribe(["dynamic.value"])

    snapshot1 = collector.harvest(1)
    assert snapshot1["data"]["dynamic.value"] == 10

    # Break the path at runtime (e.g., dynamic becomes None or attribute removed)
    # Here we change the object to not have 'value'
    registry._data["dynamic"] = SimpleNamespace() # Empty

    snapshot2 = collector.harvest(2)
    # Should be in errors now
    assert "dynamic.value" in snapshot2["errors"]
    assert "dynamic.value" not in snapshot2["data"]

def test_deep_nested_path(collector):
    collector.subscribe(["agents.1.balance"])
    snapshot = collector.harvest(1)
    assert snapshot["data"]["agents.1.balance"] == 100

def test_root_object_path(collector, registry):
    # Subscribe to root object directly
    collector.subscribe(["economy"])
    snapshot = collector.harvest(1)
    assert snapshot["data"]["economy"] == registry._data["economy"]

def test_subscribe_pre_validation(collector, registry):
    # Valid path
    collector.subscribe(["economy.m2"])
    assert "economy.m2" in collector._accessors
    assert "economy.m2" not in collector._invalid_paths

    # Invalid path
    collector.subscribe(["economy.missing"])
    assert "economy.missing" not in collector._accessors
    assert "economy.missing" in collector._invalid_paths
