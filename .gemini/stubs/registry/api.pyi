from _typeshed import Incomplete
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Protocol, TypedDict

class MissionType(str, Enum):
    JULES = 'jules'
    GEMINI = 'gemini'

@dataclass
class MissionDTO:
    key: str
    title: str
    type: MissionType
    instruction_raw: str = ...
    command: str | None = ...
    file_path: str | None = ...
    wait: bool = ...
    session_id: str | None = ...
    worker: str | None = ...
    context_files: list[str] = field(default_factory=list)
    output_path: str | None = ...
    model: str | None = ...
    audit_requirements: Any | None = ...
    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for legacy compatibility."""

class IMissionRegistryService(Protocol):
    def register_mission(self, mission: MissionDTO) -> None: ...
    def get_mission(self, key: str) -> MissionDTO | None: ...
    def delete_mission(self, key: str) -> bool: ...
    def get_mission_prompt(self, key: str) -> str: ...

class MissionContext(TypedDict):
    """Defines the context files required for a mission."""
    files: list[str]

class GeminiMissionDefinition(TypedDict):
    """
    Schema for a registered mission.
    Matches the structure required by gemini_manifest.py.
    """
    title: str
    worker: str
    instruction: str
    context_files: list[str]
    output_path: str | None
    model: str | None

class MissionMetadata(TypedDict, total=False):
    """Optional metadata for missions."""
    priority: str
    owner: str
    tags: list[str]

@dataclass
class RegisteredMission:
    """Internal representation of a registered mission."""
    key: str
    definition: GeminiMissionDefinition
    metadata: MissionMetadata | None = ...
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""

class IMissionRegistry(Protocol):
    """Interface for the Mission Registry."""
    def register(self, key: str, definition: GeminiMissionDefinition, metadata: MissionMetadata | None = None) -> None: ...
    def get_mission(self, key: str) -> GeminiMissionDefinition | None: ...
    def to_manifest(self) -> dict[str, dict[str, Any]]:
        """Exports to the format required by GEMINI_MISSIONS."""
    def scan_packages(self, package_path: str) -> None:
        """Recursively scans a package for @gemini_mission decorated functions."""

class GeminiMissionRegistry:
    def __init__(self) -> None: ...
    def register(self, key: str, definition: GeminiMissionDefinition, metadata: MissionMetadata | None = None) -> None: ...
    def get_mission(self, key: str) -> GeminiMissionDefinition | None: ...
    def to_manifest(self) -> dict[str, dict[str, Any]]: ...
    def scan_packages(self, package_path: str) -> None:
        """
        Scans the given package path for modules and imports them.
        The @gemini_mission decorator will register the missions as a side effect of import.
        """

mission_registry: Incomplete

def gemini_mission(key: str, title: str, worker: str, context_files: list[str], output_path: str | None = None, instruction: str = '', model: str | None = 'gemini-3-pro-preview', **kwargs) -> Callable:
    '''
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
    '''

@dataclass
class CommandContext:
    """
    Context object passed to every command execution.
    Encapsulates environment configuration and lazy service access.
    """
    base_dir: Path
    gemini_manifest_path: Path
    jules_manifest_path: Path
    gemini_registry_json: Path
    jules_registry_json: Path
    raw_args: list[str] = field(default_factory=list)
    is_interactive: bool = ...
    service_provider: Any = ...

@dataclass
class CommandResult:
    """
    Standardized return object for command execution.
    """
    success: bool
    message: str
    exit_code: int = ...
    data: dict[str, Any] | None = ...

class ICommand(Protocol):
    """
    Interface for all executable commands (Fixed or Dynamic Dispatchers).
    """
    @property
    def name(self) -> str:
        """The primary invocation name of the command (e.g., 'git-review')."""
    @property
    def description(self) -> str:
        """Short description for help text."""
    def execute(self, ctx: CommandContext) -> CommandResult:
        """
        Executes the command logic.
        
        Args:
            ctx: The execution context containing paths and services.
            
        Returns:
            CommandResult indicating success/failure.
        """

class IFixedCommandRegistry(Protocol):
    """
    Interface for the immutable registry of system commands.
    """
    def register(self, command: ICommand) -> None:
        """Registers a command implementation."""
    def get_command(self, name: str) -> ICommand | None:
        """Retrieves a command by name."""
    def list_commands(self) -> list[str]:
        """Lists all registered command names."""
    def has_command(self, name: str) -> bool:
        """Checks if a command exists."""

class IServiceProvider(Protocol):
    """
    Interface for providing services lazily.
    """
    def get_gemini_service(self) -> Any:
        """Returns the Gemini MissionRegistryService, initializing it if necessary."""
    def get_jules_service(self) -> Any:
        """Returns the Jules MissionRegistryService, initializing it if necessary."""
