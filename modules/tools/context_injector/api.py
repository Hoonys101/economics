from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Protocol, Dict, runtime_checkable, Set

class ContextTier(Enum):
    """
    Priority tier for context injection.
    Lower values are more critical (Tier 1 > Tier 3).
    """
    UNIVERSAL = 1       # Tier 1: Mandatory Core Contracts (e.g., system/api.py)
    STRUCTURAL = 2      # Tier 2: Direct Dependencies (AST-discovered imports)
    TESTING = 3         # Tier 2.5: Test Fixtures & Related Tests
    DOCUMENTATION = 4   # Tier 3: Relevant Manuals & Design Docs
    FALLBACK = 99       # Legacy Heuristics

@dataclass(frozen=True)
class ContextNodeDTO:
    """
    Represents a single file injected into the context.
    """
    file_path: str
    tier: ContextTier
    description: str = ""
    source_node: Optional[str] = None # The file that triggered this inclusion (e.g., importer)

@dataclass
class InjectionRequestDTO:
    """
    Request payload for the Context Injector.
    """
    target_files: List[str]
    task_description: str = ""
    include_tests: bool = True
    include_docs: bool = True
    max_dependency_depth: int = 1 # How deep to traverse the import graph
    token_budget: Optional[int] = None # Optional limit

@dataclass
class InjectionResultDTO:
    """
    The final set of files to be injected.
    """
    nodes: List[ContextNodeDTO]
    total_files: int
    missing_files: List[str] # Imports found but file missing
    strategy_used: str

@runtime_checkable
class IContextStrategy(Protocol):
    """
    Strategy interface for resolving context files.
    """
    def resolve(self, request: InjectionRequestDTO, current_nodes: Set[str]) -> List[ContextNodeDTO]:
        """
        Resolves context nodes based on the strategy logic.
        """
        ...

@runtime_checkable
class IContextInjectorService(Protocol):
    """
    Primary service for Dynamic Context Injection.
    """
    def analyze_context(self, request: InjectionRequestDTO) -> InjectionResultDTO:
        """
        Analyzes the request and returns a prioritized list of context files.
        """
        ...
