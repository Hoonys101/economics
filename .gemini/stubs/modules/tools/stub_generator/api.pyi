from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class StubGenerationRequestDTO:
    """
    Request to generate a stub for a specific source file.
    """
    source_path: str
    output_dir: str
    include_docstrings: bool = ...
    preserve_defaults: bool = ...

@dataclass(frozen=True)
class StubGenerationResultDTO:
    """
    Result of a stub generation attempt.
    """
    source_path: str
    stub_path: str | None
    success: bool
    error_message: str | None = ...
    generation_time_ms: float = ...
    is_cached: bool = ...

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
    def batch_generate(self, requests: list[StubGenerationRequestDTO]) -> list[StubGenerationResultDTO]:
        """
        Generates stubs for multiple files in parallel or sequence.
        """

class IStubPostProcessor(Protocol):
    """
    Interface for post-processing generated stubs.
    Used to fix common stubgen issues or enforce strict formatting.
    """
    def process(self, stub_content: str) -> str:
        """
        Refines the raw stub content (e.g., re-inserting missing docstrings).
        """
