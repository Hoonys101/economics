from dataclasses import dataclass, field as field
from enum import Enum, auto as auto
from pathlib import Path
from typing import Protocol

class ContextTier(Enum):
    """
    Priority tier for context injection.
    Lower values are more critical (Tier 1 > Tier 3).
    """
    UNIVERSAL = 1
    STRUCTURAL = 2
    TESTING = 3
    DOCUMENTATION = 4
    FALLBACK = 99

@dataclass(frozen=True)
class ContextNodeDTO:
    """
    Represents a single file injected into the context.
    """
    file_path: str
    tier: ContextTier
    description: str = ...
    source_node: str | None = ...
    is_stub: bool = ...
    original_path: str | None = ...

@dataclass
class FormattedContextNodeDTO:
    """
    Represents a context node that has been formatted with metadata guidelines.
    """
    original_node: ContextNodeDTO
    formatted_content: str

class IContextFormatter(Protocol):
    """
    Protocol for formatting context nodes with tier-specific guidelines.
    """
    def format_node(self, node: ContextNodeDTO, raw_content: str) -> FormattedContextNodeDTO: ...
    def build_context_block(self, nodes: list[ContextNodeDTO], base_dir: Path) -> str: ...

@dataclass
class InjectionRequestDTO:
    """
    Request payload for the Context Injector.
    """
    target_files: list[str]
    worker_type: str = ...
    task_description: str = ...
    include_tests: bool = ...
    include_docs: bool = ...
    max_dependency_depth: int = ...
    token_budget: int | None = ...

@dataclass
class InjectionResultDTO:
    """
    The final set of files to be injected.
    """
    nodes: list[ContextNodeDTO]
    total_files: int
    missing_files: list[str]
    strategy_used: str

class IContextStrategy(Protocol):
    """
    Strategy interface for resolving context files.
    """
    def resolve(self, request: InjectionRequestDTO, current_nodes: set[str]) -> list[ContextNodeDTO]:
        """
        Resolves context nodes based on the strategy logic.
        """

class IContextInjectorService(Protocol):
    """
    Primary service for Dynamic Context Injection.
    """
    def analyze_context(self, request: InjectionRequestDTO) -> InjectionResultDTO:
        """
        Analyzes the request and returns a prioritized list of context files.
        """
