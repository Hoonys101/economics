import pytest
from unittest.mock import MagicMock, patch
from _internal.registry.api import GeminiMissionRegistry, gemini_mission, mission_registry

def test_manual_registration():
    registry = GeminiMissionRegistry()

    definition = {
        "title": "Test Mission",
        "worker": "spec",
        "instruction": "Do something",
        "context_files": ["foo.py"],
        "output_path": "out.md",
        "model": "gemini-3-pro-preview"
    }

    registry.register("test-key", definition)

    retrieved = registry.get_mission("test-key")
    assert retrieved == definition
    assert registry.get_mission("missing") is None

def test_decorator_registration():
    # Clear registry for test
    mission_registry._missions.clear()

    @gemini_mission(
        key="decorator-test",
        title="Decorator Test",
        worker="spec",
        context_files=["bar.py"],
        instruction="Static Instruction"
    )
    def my_mission():
        return "Dynamic Instruction Override"

    # Check if registered
    mission = mission_registry.get_mission("decorator-test")
    assert mission is not None
    assert mission["title"] == "Decorator Test"
    # Implementation runs the function and overrides instruction if returns string
    assert mission["instruction"] == "Dynamic Instruction Override"

def test_decorator_static_instruction():
    mission_registry._missions.clear()

    @gemini_mission(
        key="static-test",
        title="Static Test",
        worker="spec",
        context_files=[],
        instruction="Static Only"
    )
    def my_static_mission():
        pass # Returns None

    mission = mission_registry.get_mission("static-test")
    assert mission["instruction"] == "Static Only"

def test_scan_packages():
    registry = GeminiMissionRegistry()

    # Mock pkgutil and importlib
    with patch("pkgutil.walk_packages") as mock_walk, \
         patch("importlib.import_module") as mock_import:

        # Setup mock package
        mock_package = MagicMock()
        mock_package.__path__ = ["/path/to/pkg"]
        mock_package.__name__ = "dummy_pkg"

        # importlib.import_module("dummy_pkg") returns mock_package
        # We need side_effect to return different things
        def import_side_effect(name):
            if name == "dummy_pkg":
                return mock_package
            return MagicMock()

        mock_import.side_effect = import_side_effect

        # walk_packages returns one module
        mock_walk.return_value = [
            (None, "dummy_pkg.mission_module", False)
        ]

        registry.scan_packages("dummy_pkg")

        # verify import_module was called for the submodule
        mock_import.assert_any_call("dummy_pkg.mission_module")

def test_to_manifest():
    registry = GeminiMissionRegistry()
    definition = {
        "title": "Test",
        "worker": "spec",
        "instruction": "Instr",
        "context_files": [],
        "output_path": None,
        "model": None
    }
    registry.register("key1", definition)

    manifest = registry.to_manifest()
    assert "key1" in manifest
    assert manifest["key1"] == definition
