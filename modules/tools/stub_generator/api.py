from __future__ import annotations
from typing import List, Optional, Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass(frozen=True)
class StubGenerationRequestDTO:
    """
    Request to generate a stub for a specific source file.
    """
    source_path: str
    output_dir: str
    include_docstrings: bool = True
    preserve_defaults: bool = True

@dataclass(frozen=True)
class StubGenerationResultDTO:
    """
    Result of a stub generation attempt.
    """
    source_path: str
    stub_path: Optional[str]
    success: bool
    error_message: Optional[str] = None
    generation_time_ms: float = 0.0
    is_cached: bool = False

@runtime_checkable
class IStubGenerator(Protocol):
    """
    Interface for the Stub Generation Service.
    Responsible for creating lightweight .pyi files from .py sources.
    """
    def generate_stub(self, request: StubGenerationRequestDTO) -> StubGenerationResultDTO:
        """
        Generates a .pyi stub for the given source file.
        Should handle caching based on file modification times.
        """
        ...

    def batch_generate(self, requests: List[StubGenerationRequestDTO]) -> List[StubGenerationResultDTO]:
        """
        Generates stubs for multiple files in parallel or sequence.
        """
        ...

@runtime_checkable
class IStubPostProcessor(Protocol):
    """
    Interface for post-processing generated stubs.
    Used to fix common stubgen issues or enforce strict formatting.
    """
    def process(self, stub_content: str) -> str:
        """
        Refines the raw stub content (e.g., re-inserting missing docstrings).
        """
        ...
