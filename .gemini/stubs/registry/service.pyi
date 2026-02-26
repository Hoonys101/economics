import types
from .api import IMissionRegistryService as IMissionRegistryService, MissionDTO as MissionDTO, MissionType as MissionType
from .mission_protocol import construct_mission_prompt as construct_mission_prompt
from _typeshed import Incomplete
from pathlib import Path

DB_PATH: Incomplete
LOCK_PATH: Incomplete

class MissionLock:
    lock_file: Incomplete
    timeout: Incomplete
    def __init__(self, lock_file: Path | None = None, timeout: int = 10) -> None: ...
    def __enter__(self) -> None: ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None: ...

class MissionRegistryService:
    db_path: Incomplete
    lock_path: Incomplete
    def __init__(self, db_path: Path = ...) -> None: ...
    def load_missions(self) -> dict[str, MissionDTO]: ...
    def get_mission(self, key: str) -> MissionDTO | None: ...
    def register_mission(self, mission: MissionDTO) -> None: ...
    def delete_mission(self, key: str) -> bool: ...
    def get_mission_prompt(self, key: str) -> str: ...
    def sync_to_legacy_json(self, target_path: Path | None = None):
        """DEPRECATED: Legacy command_registry.json is no longer used."""
    def migrate_from_registry_dir(self) -> int:
        """
        Scans _internal/registry/ for any *_manifest.py files and migrates missions.
        After migration, standard manifests (gemini/jules) are auto-reset to their
        manual-only template state to prevent re-migration of completed missions.
        
        ROUTING: Only processes the manifest section matching this service's db_path.
        - Jules service (jules_command_registry.json) -> only JULES_MISSIONS
        - Gemini service (gemini_command_registry.json) -> only GEMINI_MISSIONS
        """
    def migrate_from_legacy(self, legacy_file_path: str, archive: bool = True) -> int:
        """
        Migrates missions from a legacy manifest file.
        If archive is True, moves the file to .bak.
        """
