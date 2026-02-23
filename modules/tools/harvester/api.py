from __future__ import annotations
from typing import List, Dict, Optional, Protocol, runtime_checkable, TypedDict
from dataclasses import dataclass

@dataclass(frozen=True)
class HarvestCandidateDTO:
    """
    Represents a file candidate for harvesting.
    """
    path: str
    branch: str
    score: int
    timestamp: int = 0
    content: Optional[str] = None

@dataclass(frozen=True)
class HarvestResultDTO:
    """
    Final result of a harvest operation.
    """
    success: bool
    harvested_files: List[str]
    errors: List[str]
    total_score: int

class HarvestConfigDTO(TypedDict):
    """
    Configuration for the harvest run.
    """
    max_branches: int
    max_files_per_branch: int
    target_patterns: List[str]
    cleanup_remote: bool
    harvest_dir: str

@runtime_checkable
class IGitDriver(Protocol):
    """
    Protocol for Git operations, enforcing batch processing.
    """
    def fetch_origin(self) -> None:
        """Executes git fetch origin --prune."""
        ...

    def list_remote_branches(self) -> List[str]:
        """Returns list of remote branches (origin/*)."""
        ...

    def list_files_in_branch(self, branch: str) -> List[str]:
        """
        Returns all file paths in a branch using ls-tree -r.
        """
        ...

    def get_commit_dates_batch(self, branch: str, file_paths: List[str]) -> Dict[str, int]:
        """
        Retrieves last commit timestamps for a LIST of files.
        """
        ...

    def read_files_batch(self, branch: str, file_paths: List[str]) -> Dict[str, Optional[str]]:
        """
        Reads content of multiple files using optimized batch methods.
        """
        ...

    def delete_remote_branch(self, branch: str) -> bool:
        """Deletes a remote branch."""
        ...

@runtime_checkable
class IScoringEngine(Protocol):
    def calculate_static_score(self, file_path: str) -> int:
        ...

@runtime_checkable
class IHarvesterService(Protocol):
    def execute_harvest(self, config: HarvestConfigDTO) -> HarvestResultDTO:
        ...
