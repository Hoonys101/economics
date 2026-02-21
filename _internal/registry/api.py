"""
_internal/registry/api.py

Defines the Gemini Mission Registry API and Decorators.
Resolves TD-DX-AUTO-CRYSTAL by enabling auto-discovery of missions.
"""
from __future__ import annotations
from typing import Callable, Dict, List, Optional, TypedDict, Any, Protocol
from dataclasses import dataclass, field
import pkgutil
import importlib
import inspect
import sys
from enum import Enum

# --- Legacy / Service API Support ---

class MissionType(str, Enum):
    JULES = "jules"
    GEMINI = "gemini"

@dataclass
class MissionDTO:
    key: str
    title: str
    type: MissionType
    instruction_raw: str = ""
    command: Optional[str] = None
    file_path: Optional[str] = None
    wait: bool = False
    session_id: Optional[str] = None
    worker: Optional[str] = None
    context_files: List[str] = field(default_factory=list)
    output_path: Optional[str] = None
    model: Optional[str] = None
    audit_requirements: Optional[Any] = None

class IMissionRegistryService(Protocol):
    def register_mission(self, mission: MissionDTO) -> None: ...
    def get_mission(self, key: str) -> Optional[MissionDTO]: ...
    def delete_mission(self, key: str) -> bool: ...
    def get_mission_prompt(self, key: str) -> str: ...

# --- New Gemini Registry API ---

class MissionContext(TypedDict):
    """Defines the context files required for a mission."""
    files: List[str]

class GeminiMissionDefinition(TypedDict):
    """
    Schema for a registered mission.
    Matches the structure required by gemini_manifest.py.
    """
    title: str
    worker: str # 'spec', 'reporter', 'verify', etc.
    instruction: str
    context_files: List[str]
    output_path: Optional[str]
    model: Optional[str]

class MissionMetadata(TypedDict, total=False):
    """Optional metadata for missions."""
    priority: str
    owner: str
    tags: List[str]

@dataclass
class RegisteredMission:
    """Internal representation of a registered mission."""
    key: str
    definition: GeminiMissionDefinition
    metadata: Optional[MissionMetadata] = None

class IMissionRegistry(Protocol):
    """Interface for the Mission Registry."""

    def register(self, key: str, definition: GeminiMissionDefinition, metadata: Optional[MissionMetadata] = None) -> None:
        ...

    def get_mission(self, key: str) -> Optional[GeminiMissionDefinition]:
        ...

    def to_manifest(self) -> Dict[str, Dict[str, Any]]:
        """Exports to the format required by GEMINI_MISSIONS."""
        ...

    def scan_packages(self, package_path: str) -> None:
        """Recursively scans a package for @gemini_mission decorated functions."""
        ...

class GeminiMissionRegistry:
    def __init__(self):
        self._missions: Dict[str, RegisteredMission] = {}

    def register(self, key: str, definition: GeminiMissionDefinition, metadata: Optional[MissionMetadata] = None) -> None:
        self._missions[key] = RegisteredMission(key=key, definition=definition, metadata=metadata)

    def get_mission(self, key: str) -> Optional[GeminiMissionDefinition]:
        if key in self._missions:
            return self._missions[key].definition
        return None

    def to_manifest(self) -> Dict[str, Dict[str, Any]]:
        manifest = {}
        for key, mission in self._missions.items():
            manifest[key] = mission.definition # TypedDict is compatible with Dict
        return manifest

    def scan_packages(self, package_path: str) -> None:
        """
        Scans the given package path for modules and imports them.
        The @gemini_mission decorator will register the missions as a side effect of import.
        """
        try:
            package = importlib.import_module(package_path)
        except ImportError:
            return

        if not hasattr(package, "__path__"):
            return

        for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            try:
                importlib.import_module(name)
            except ImportError:
                pass

# Singleton Access
mission_registry = GeminiMissionRegistry()

# Decorator API
def gemini_mission(
    key: str,
    title: str,
    worker: str,
    context_files: List[str],
    output_path: Optional[str] = None,
    instruction: str = "",
    model: Optional[str] = "gemini-3-pro-preview",
    **kwargs
) -> Callable:
    """
    Decorator to register a function or class as a Gemini Mission.

    Usage:
        @gemini_mission(
            key="wave3-refactor",
            title="Wave 3 Refactor",
            worker="spec",
            context_files=["..."],
            output_path="..."
        )
        def mission_definition():
            return "Specific instructions if dynamic..."
    """
    def decorator(func: Callable) -> Callable:
        final_instruction = instruction

        # If the function is simple enough (returns string, no args), let's call it to get the instruction.
        try:
            sig = inspect.signature(func)
            if not sig.parameters:
                res = func()
                if isinstance(res, str) and res:
                    final_instruction = res
        except Exception:
            pass

        definition: GeminiMissionDefinition = {
            "title": title,
            "worker": worker,
            "instruction": final_instruction,
            "context_files": context_files,
            "output_path": output_path,
            "model": model
        }

        metadata: MissionMetadata = {}
        for k in ["priority", "owner", "tags"]:
            if k in kwargs:
                metadata[k] = kwargs[k] # type: ignore

        mission_registry.register(key, definition, metadata)
        return func
    return decorator
