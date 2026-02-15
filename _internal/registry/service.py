import json
import time
import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import asdict

from .api import IMissionRegistryService, MissionDTO, MissionType
from .mission_protocol import construct_mission_prompt

DB_PATH = Path("_internal/registry/mission_db.json")
LOCK_PATH = Path("_internal/registry/mission.lock")

class MissionLock:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.lock_file = LOCK_PATH

    def __enter__(self):
        start_time = time.time()
        while True:
            try:
                # Atomic creation (exclusive creation)
                self.lock_file.touch(exist_ok=False)
                break
            except FileExistsError:
                if time.time() - start_time > self.timeout:
                    # Check if lock is stale (e.g. > 30 seconds old)
                    try:
                        stat = self.lock_file.stat()
                        if time.time() - stat.st_mtime > 30:
                            print(f"Breaking stale lock: {self.lock_file}")
                            self.lock_file.unlink(missing_ok=True)
                            continue # Retry immediately
                    except FileNotFoundError:
                        pass # Lock gone, retry

                    raise TimeoutError(f"Could not acquire lock after {self.timeout} seconds")
                time.sleep(0.1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file.exists():
            self.lock_file.unlink()

class MissionRegistryService:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        # Ensure directory exists
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_db(self) -> Dict[str, Any]:
        if not self.db_path.exists():
            return {"_meta": {"version": "1.0"}, "missions": {}}

        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"_meta": {"version": "1.0"}, "missions": {}}

    def _save_db(self, data: Dict[str, Any]):
        # Atomic write
        temp_path = self.db_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
        shutil.move(str(temp_path), str(self.db_path))

    def load_missions(self) -> Dict[str, MissionDTO]:
        data = self._load_db()
        missions = {}
        for key, m_data in data.get("missions", {}).items():
            # Convert string type back to Enum
            if isinstance(m_data.get("type"), str):
                try:
                    m_data["type"] = MissionType(m_data["type"])
                except ValueError:
                    # Fallback to GEMINI if unknown, or log warning
                    m_data["type"] = MissionType.GEMINI

            missions[key] = MissionDTO(**m_data)
        return missions

    def get_mission(self, key: str) -> Optional[MissionDTO]:
        missions = self.load_missions()
        return missions.get(key)

    def register_mission(self, mission: MissionDTO) -> None:
        with MissionLock():
            data = self._load_db()

            # Serialize DTO
            mission_dict = asdict(mission)
            mission_dict["type"] = mission.type.value # Enum to string

            if "missions" not in data:
                data["missions"] = {}

            data["missions"][mission.key] = mission_dict
            self._save_db(data)

    def delete_mission(self, key: str) -> bool:
        with MissionLock():
            data = self._load_db()
            if "missions" in data and key in data["missions"]:
                del data["missions"][key]
                self._save_db(data)
                return True
            return False

    def get_mission_prompt(self, key: str) -> str:
        mission = self.get_mission(key)
        if not mission:
            raise ValueError(f"Mission {key} not found")

        return construct_mission_prompt(
            key=mission.key,
            title=mission.title,
            instruction_raw=mission.instruction_raw
        )

    def sync_to_legacy_json(self, target_path: Optional[Path] = None):
        """
        Exports current missions to command_registry.json for legacy tool compatibility.
        """
        target = target_path or Path("_internal/registry/command_registry.json")
        missions = self.load_missions()
        
        # Format for command_registry.json
        output_data = {
            "_meta": {
                "updated": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
        }
        
        # Merge missions into root for legacy compatibility if needed, 
        # or keep them under 'missions' key. 
        # Based on launcher.py, it seems it expects missions in the registry.
        for key, m in missions.items():
            m_dict = asdict(m)
            m_dict["type"] = m.type.value
            output_data[key] = m_dict
            
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)

    def migrate_from_registry_dir(self) -> int:
        """
        Scans _internal/registry/ for any *_manifest.py files and migrates missions.
        """
        registry_dir = Path("_internal/registry")
        manifest_files = list(registry_dir.glob("*_manifest.py"))
        
        count = 0
        import importlib.util
        import sys
        
        # Ensure we can import from the directory
        if str(registry_dir) not in sys.path:
            sys.path.append(str(registry_dir))

        for manifest_path in manifest_files:
            spec = importlib.util.spec_from_file_location(manifest_path.stem, manifest_path)
            if spec is None or spec.loader is None:
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # JULES
            if hasattr(module, "JULES_MISSIONS"):
                for key, m_data in module.JULES_MISSIONS.items():
                    dto = MissionDTO(
                        key=key,
                        title=m_data.get("title", key),
                        type=MissionType.JULES,
                        instruction_raw=m_data.get("instruction", ""),
                        command=m_data.get("command"),
                        file_path=m_data.get("file"),
                        wait=m_data.get("wait", False),
                        session_id=m_data.get("session_id")
                    )
                    self.register_mission(dto)
                    count += 1

            # GEMINI
            if hasattr(module, "GEMINI_MISSIONS"):
                for key, m_data in module.GEMINI_MISSIONS.items():
                    dto = MissionDTO(
                        key=key,
                        title=m_data.get("title", key),
                        type=MissionType.GEMINI,
                        instruction_raw=m_data.get("instruction", ""),
                        worker=m_data.get("worker"),
                        context_files=m_data.get("context_files", []),
                        output_path=m_data.get("output_path"),
                        model=m_data.get("model"),
                        audit_requirements=m_data.get("audit_requirements")
                    )
                    self.register_mission(dto)
                    count += 1

            # Move to .bak to avoid re-migration
            shutil.move(str(manifest_path), str(manifest_path.with_suffix('.py.bak')))

        return count
