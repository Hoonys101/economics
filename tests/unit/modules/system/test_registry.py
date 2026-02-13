import pytest
from unittest.mock import Mock, MagicMock
from modules.system.api import OriginType, RegistryEntry, RegistryObserver
from modules.system.registry import GlobalRegistry

class TestGlobalRegistry:
    @pytest.fixture
    def registry(self):
        return GlobalRegistry()

    def test_set_and_get_basic(self, registry):
        # 1. Happy Path
        assert registry.set("TEST_KEY", 100, OriginType.CONFIG) is True
        assert registry.get("TEST_KEY") == 100

        # 2. Update with same origin
        assert registry.set("TEST_KEY", 200, OriginType.CONFIG) is True
        assert registry.get("TEST_KEY") == 200

    def test_origin_priority(self, registry):
        # 1. Set with SYSTEM
        assert registry.set("PRIORITY_TEST", 1, OriginType.SYSTEM) is True

        # 2. Overwrite with CONFIG (Higher)
        assert registry.set("PRIORITY_TEST", 2, OriginType.CONFIG) is True
        assert registry.get("PRIORITY_TEST") == 2

        # 3. Fail to overwrite with SYSTEM (Lower)
        assert registry.set("PRIORITY_TEST", 3, OriginType.SYSTEM) is False
        assert registry.get("PRIORITY_TEST") == 2

        # 4. Overwrite with GOD_MODE (Highest)
        assert registry.set("PRIORITY_TEST", 4, OriginType.GOD_MODE) is True
        assert registry.get("PRIORITY_TEST") == 4

        # 5. Fail to overwrite with CONFIG (Lower than GOD_MODE)
        # Note: GOD_MODE implies lock=True in implementation
        with pytest.raises(PermissionError):
            registry.set("PRIORITY_TEST", 5, OriginType.CONFIG)

    def test_locking_mechanism(self, registry):
        # 1. Set CONFIG value
        registry.set("LOCK_TEST", 10, OriginType.CONFIG)

        # 2. Lock it (GOD_MODE authority)
        registry.lock("LOCK_TEST")
        entry = registry.snapshot()["LOCK_TEST"]
        assert entry.is_locked is True
        assert entry.origin == OriginType.GOD_MODE

        # 3. Attempt update with CONFIG (Should fail due to lock)
        with pytest.raises(PermissionError):
            registry.set("LOCK_TEST", 20, OriginType.CONFIG)

        # 4. Update with GOD_MODE (Should succeed)
        assert registry.set("LOCK_TEST", 30, OriginType.GOD_MODE) is True
        assert registry.get("LOCK_TEST") == 30

        # 5. Unlock
        registry.unlock("LOCK_TEST")
        entry = registry.snapshot()["LOCK_TEST"]
        assert entry.is_locked is False
        # Origin remains GOD_MODE

        # 6. Attempt update with SYSTEM (Should fail due to priority, not lock)
        assert registry.set("LOCK_TEST", 40, OriginType.SYSTEM) is False

        # 7. Attempt update with GOD_MODE (Succeed)
        assert registry.set("LOCK_TEST", 50, OriginType.GOD_MODE) is True

    def test_observer_notification(self, registry):
        observer = MagicMock(spec=RegistryObserver)
        registry.subscribe(observer)

        registry.set("OBSERVE_ME", 123, OriginType.CONFIG)

        observer.on_registry_update.assert_called_with("OBSERVE_ME", 123, OriginType.CONFIG)

    def test_key_specific_observer(self, registry):
        general_observer = MagicMock(spec=RegistryObserver)
        specific_observer = MagicMock(spec=RegistryObserver)

        registry.subscribe(general_observer)
        registry.subscribe(specific_observer, keys=["TARGET"])

        # Update unrelated key
        registry.set("OTHER", 1, OriginType.SYSTEM)
        general_observer.on_registry_update.assert_called_with("OTHER", 1, OriginType.SYSTEM)
        specific_observer.on_registry_update.assert_not_called()

        general_observer.reset_mock()

        # Update target key
        registry.set("TARGET", 99, OriginType.CONFIG)
        general_observer.on_registry_update.assert_called_with("TARGET", 99, OriginType.CONFIG)
        specific_observer.on_registry_update.assert_called_with("TARGET", 99, OriginType.CONFIG)
