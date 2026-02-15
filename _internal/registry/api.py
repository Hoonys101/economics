"""
Mission Registry API Definition.
Defines the Data Transfer Objects and Service Interface for the Mission Registry System.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Protocol, Union, Any, runtime_checkable
from enum import Enum

class MissionType(Enum):
    JULES = "jules"
    GEMINI = "gemini"

@dataclass
class MissionDTO:
    """
    Data Transfer Object representing a single mission (task).
    Unified structure for both Jules and Gemini missions.
    """
    key: str
    title: str
    type: MissionType
    instruction_raw: str  # The raw instruction without protocol injections

    # Common Optional
    status: str = "pending"
    created_at: str = ""

    # Jules Specific
    command: Optional[str] = None  # 'create', 'send-message'
    file_path: Optional[str] = None
    wait: bool = False
    session_id: Optional[str] = None

    # Gemini Specific
    worker: Optional[str] = None  # 'spec', 'reporter', etc.
    context_files: List[str] = field(default_factory=list)
    output_path: Optional[str] = None
    model: Optional[str] = None
    audit_requirements: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts DTO to dictionary for legacy compatibility."""
        from dataclasses import asdict
        d = asdict(self)
        d["type"] = self.type.value
        return d

@runtime_checkable
class IMissionRegistryService(Protocol):
    """
    Interface for the Mission Registry Service.
    Handles CRUD operations for missions and protocol injection.
    """

    def load_missions(self) -> Dict[str, MissionDTO]:
        """
        Loads all missions from the persistence layer (mission_db.json).
        """
        ...

    def get_mission(self, key: str) -> Optional[MissionDTO]:
        """
        Retrieves a specific mission by key.
        """
        ...

    def register_mission(self, mission: MissionDTO) -> None:
        """
        Saves or updates a mission atomically.
        """
        ...

    def delete_mission(self, key: str) -> bool:
        """
        Removes a mission by key. Returns True if found and deleted.
        """
        ...

    def get_mission_prompt(self, key: str) -> str:
        """
        Constructs the full, protocol-compliant prompt for a mission.
        Injects META, GUARDRAILS, and OUTPUT_DISCIPLINE dynamically.
        """
        ...

    def migrate_from_legacy(self, legacy_file_path: str = "_internal/registry/command_manifest.py") -> int:
        """
        One-time migration from legacy command_manifest.py to mission_db.json.
        Returns the number of missions migrated.
        """
        ...
