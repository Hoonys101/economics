import pytest
import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from _internal.registry.api import MissionDTO, MissionType
from _internal.registry.service import MissionRegistryService, MissionLock

@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "mission_db.json"

@pytest.fixture
def service(temp_db_path):
    # Ensure parent dir exists for lock file patching if needed,
    # but service creates parent dir for db_path.
    return MissionRegistryService(db_path=temp_db_path)

def test_load_missions_empty(service):
    missions = service.load_missions()
    assert missions == {}

def test_register_and_get_mission(service):
    dto = MissionDTO(
        key="test-mission",
        title="Test Mission",
        type=MissionType.JULES,
        instruction_raw="Do something"
    )
    service.register_mission(dto)

    loaded = service.get_mission("test-mission")
    assert loaded is not None
    assert loaded.key == "test-mission"
    assert loaded.title == "Test Mission"
    assert loaded.type == MissionType.JULES

def test_delete_mission(service):
    dto = MissionDTO(
        key="delete-me",
        title="Delete Me",
        type=MissionType.GEMINI,
        instruction_raw="Delete instruction"
    )
    service.register_mission(dto)

    assert service.get_mission("delete-me") is not None

    deleted = service.delete_mission("delete-me")
    assert deleted is True
    assert service.get_mission("delete-me") is None

    deleted_again = service.delete_mission("delete-me")
    assert deleted_again is False

def test_get_mission_prompt(service):
    dto = MissionDTO(
        key="prompt-mission",
        title="Prompt Mission",
        type=MissionType.JULES,
        instruction_raw="Execute order 66"
    )
    service.register_mission(dto)

    prompt = service.get_mission_prompt("prompt-mission")
    assert "MISSION: Prompt Mission" in prompt
    assert "Mission Key: prompt-mission" in prompt
    assert "Execute order 66" in prompt
    assert "ARCHITECTURAL GUARDRAILS" in prompt # From GUARDRAILS

def test_migration(service, tmp_path):
    # Create a dummy legacy file
    legacy_file = tmp_path / "command_manifest.py"
    legacy_content = """
JULES_MISSIONS = {
    "legacy-jules": {
        "title": "Legacy Jules",
        "instruction": "Old instruction",
        "command": "create"
    }
}
GEMINI_MISSIONS = {
    "legacy-gemini": {
        "title": "Legacy Gemini",
        "instruction": "Old gemini instruction",
        "worker": "spec"
    }
}
"""
    legacy_file.write_text(legacy_content)

    count = service.migrate_from_legacy(str(legacy_file))
    assert count == 2

    # Check if missions are registered
    jules = service.get_mission("legacy-jules")
    assert jules is not None
    assert jules.type == MissionType.JULES
    assert jules.instruction_raw == "Old instruction"

    gemini = service.get_mission("legacy-gemini")
    assert gemini is not None
    assert gemini.type == MissionType.GEMINI

    # Check if file was renamed
    assert not legacy_file.exists()
    assert legacy_file.with_suffix(".py.bak").exists()

def test_lock_timeout(tmp_path):
    # We need to patch LOCK_PATH to use a temp file
    lock_path = tmp_path / "test.lock"

    with patch("_internal.registry.service.LOCK_PATH", lock_path):
        # Create lock file manually to simulate another process holding it
        lock_path.touch()

        # Set timeout to very small
        start = time.time()
        with pytest.raises(TimeoutError):
            # We use a short timeout
            lock = MissionLock(timeout=0.1)
            with lock:
                pass
        duration = time.time() - start
        assert duration >= 0.1 # Should have waited at least 0.1s

    # Clean up handled by tmp_path but good practice
    if lock_path.exists():
        lock_path.unlink()

def test_lock_success(tmp_path):
    lock_path = tmp_path / "test.lock"
    with patch("_internal.registry.service.LOCK_PATH", lock_path):
        with MissionLock(timeout=1):
            assert lock_path.exists()
        assert not lock_path.exists()
