"""
Crystallizer API: Knowledge Recirculation Engine
Defines the protocols and DTOs for extracting insights and proposing manual updates.
"""
from typing import List, Optional, Protocol, runtime_checkable, TypedDict
from datetime import datetime
from dataclasses import dataclass


class InsightMetadata(TypedDict):
    """Metadata extracted from Insight Report Frontmatter."""
    mission_key: str
    date: str  # YYYY-MM-DD
    type: str  # e.g., "Architectural Decision"
    target_manual: Optional[str]  # e.g., "_internal/manuals/spec_writer.md"
    actionable: bool


@dataclass
class InsightEntry:
    """Represents a single parsed insight ready for synthesis."""
    file_path: str
    metadata: InsightMetadata
    content_block: str  # The raw markdown content of the insight
    relevance_score: float = 1.0


@dataclass
class ManualContext:
    """Represents the current state of a manual to be updated."""
    file_path: str
    current_content: str
    last_updated: datetime


@dataclass
class ProposalDiff:
    """A specific suggested change to a manual."""
    section_header: str  # e.g., "## 3. Protocol Compliance"
    original_text: Optional[str]
    proposed_text: str
    reasoning: str
    source_insights: List[str]  # List of Insight file paths driving this change


class ManualUpdateProposalDTO(TypedDict):
    """The final artifact produced by the Crystallizer."""
    target_manual: str
    generated_at: str
    proposals: List[ProposalDiff]
    risk_assessment: str


@runtime_checkable
class IInsightLoader(Protocol):
    """Protocol for loading and parsing insight files."""
    def load_insights(self, insights_dir: str) -> List[InsightEntry]: ...
    def filter_actionable(self, insights: List[InsightEntry]) -> List[InsightEntry]: ...


@runtime_checkable
class IManualSynthesizer(Protocol):
    """Protocol for generating update proposals from insights."""
    def synthesize_proposal(
        self, 
        manual: ManualContext, 
        insights: List[InsightEntry]
    ) -> ManualUpdateProposalDTO: ...


@runtime_checkable
class ICrystallizerEngine(Protocol):
    """Main Orchestrator Interface for the Knowledge Loop."""
    def run_crystallization(
        self, 
        insights_dir: str, 
        manuals_dir: str, 
        dry_run: bool = True
    ) -> List[ManualUpdateProposalDTO]: ...
