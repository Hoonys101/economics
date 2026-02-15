I will generate the requested files for the "Knowledge Recirculation Loop" (Mission Key: `spec-manual-loop`).

File: communications/insights/spec-manual-loop.md
```markdown
# Insight Report: Knowledge Recirculation Loop (Crystallizer)

> **Mission Key**: `spec-manual-loop`
> **Type**: Architectural Decision & Risk Analysis
> **Date**: 2026-02-15

---

## 🏗️ [Architectural Decisions] The Crystallizer Pattern

### 1. Proposal-Based Workflow (Safety First)
To mitigate the risk of **Recursive Prompt Degradation** (where an agent dilutes its own instructions over time), the "Crystallizer" engine is designed as a **Proposal Generator**, not an executor. It never overwrites manuals directly. Instead, it produces a `MANUAL_UPDATE_PROPOSAL.md` artifact that requires explicit human review and application.

### 2. Structured Insight Parsing
The current free-form nature of insight reports makes automated extraction unreliable. We are introducing a **Strict Metadata Header** (YAML Frontmatter) requirement for all future insight reports to enable machine-readable filtering.
- **Key Field**: `target_manual` (e.g., `_internal/manuals/spec_writer.md`)
- **Key Field**: `actionable_insight` (Boolean)

### 3. The "Librarian" Persona
We identified that the `spec_writer` role is insufficient for this meta-cognitive task. A new logical component, the **Crystallizer Engine**, is defined to handle the aggregation and synthesis of insights. This engine operates offline (post-session) to maintain the purity of the runtime environment.

---

## ⚠️ [Risks & Mitigations]

### 1. Prompt Injection via Insight
- **Risk**: A malicious or hallucinated insight file could contain instructions like "Ignore all safety rules."
- **Mitigation**: The Crystallizer treats all insight content as **Untrusted User Input**. It extracts only the *observations* and *suggestions*, wrapping them in a sanitization layer before presenting them in the proposal.

### 2. Context Window Pollution
- **Risk**: Feeding all historical insights into the context window for synthesis is cost-prohibitive and noisy.
- **Mitigation**: Insights are filtered by `relevance_score` and `date` (Recency Bias), ensuring only the most pertinent lessons are recirculated.

---

## 🧪 [Verification Strategy]

To verify the Crystallizer's logic without corrupting the system:
1. **Mock Data**: Create a temporary `tests/fixtures/insights/mock_insight.md`.
2. **Dry Run**: Execute the Crystallizer in `dry_run=True` mode.
3. **Assertion**: Verify that a `MANUAL_UPDATE_PROPOSAL.md` is generated and contains the expected diff, without modifying any protected files.

```

File: modules/system/crystallizer/api.py
```python
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
```

File: design/3_work_artifacts/specs/manual_recirculation_spec.md
```markdown
# Specification: Knowledge Recirculation Loop (Crystallizer)

## 1. Introduction
The **Crystallizer** is an offline engine designed to close the feedback loop between operational experience (Insights) and systemic instruction (Manuals). It automates the analysis of `communications/insights/` to propose structured updates to `_internal/manuals/`, preventing the recurrence of errors and solidifying architectural decisions.

**Core Principle**: "Knowledge survives, artifacts perish." - The Crystallizer ensures that transient insights are refined into permanent instruction.

## 2. Architecture

### 2.1 Component Diagram
`[InsightLoader]` -> `[InsightFilter]` -> `[ManualSynthesizer]` -> `[ProposalGenerator]`

### 2.2 Data Flow
1.  **Ingest**: Scan `communications/insights/*.md`.
2.  **Parse**: Extract metadata (YAML) and content blocks.
3.  **Filter**: Select insights where `actionable: true` and `target_manual` is defined.
4.  **Load Context**: Read the current version of the target manual (e.g., `spec_writer.md`).
5.  **Synthesize**: Generate a **Proposal Diff** that integrates the new knowledge into the existing manual structure.
6.  **Output**: Write `MANUAL_UPDATE_PROPOSAL.md`.

## 3. Detailed Design

### 3.1 Insight Loader & Parser
- **Responsibility**: Robustly parse Markdown files.
- **Logic**:
    - Iterate through `communications/insights/`.
    - Regex capture for YAML frontmatter.
    - If frontmatter is missing, fallback to heuristic parsing (looking for `> **Target Manual**:`).
    - Return `List[InsightEntry]`.

### 3.2 Manual Synthesizer (The Brain)
- **Responsibility**: Determine *how* the manual should change.
- **Logic**:
    - **Input**: `ManualContext`, `List[InsightEntry]`.
    - **Grouping**: Group insights by `target_manual`.
    - **Conflict Resolution**: If multiple insights contradict, prioritize the most recent (by date).
    - **Diff Generation**:
        - Identify the relevant section in the manual (e.g., "## 3. Protocol Compliance").
        - Construct a new text block that preserves existing rules while adding the new constraint.
        - **Crucial**: Do not simply append. Integrate.

### 3.3 Proposal Generator
- **Responsibility**: Format the output for human review.
- **Output Format**:
    ```markdown
    # Manual Update Proposal: [Manual Name]
    > Generated: 2026-02-15
    
    ## Proposed Change 1: [Section Name]
    **Reasoning**: derived from [Insight-001], [Insight-002]
    
    ### Diff
    - Old Rule: "Do X."
    + New Rule: "Do X, but verify Y first."
    ```

## 4. Safety & Constraints

1.  **Read-Only Operations**: The Crystallizer **NEVER** modifies a manual file directly.
2.  **Sanitization**: All insight text is sanitized to remove imperative commands ("You must...") before synthesis to prevent prompt injection.
3.  **Version Control**: The `MANUAL_UPDATE_PROPOSAL.md` is a build artifact, not a source file. It should be committed or discarded after application.

## 5. Verification Plan

### 5.1 Unit Tests
- `test_parse_insight_metadata`: Verify extraction of YAML frontmatter.
- `test_filter_actionable`: Ensure non-actionable insights are dropped.

### 5.2 Integration Tests
- **Scenario**: "The Conflicting Insight"
    - Input: Manual says "Do A". Insight 1 says "Do B". Insight 2 (newer) says "Do A+".
    - Expected: Proposal suggests "Do A+".
- **Fixture**: `tests/fixtures/crystallizer/mock_manual.md`.

## 6. Mocking Strategy
- Use `tests/conftest.py` to provide `mock_insight_loader` adhering to `IInsightLoader`.
- Do **not** mock the filesystem for the integration test; use a temporary directory pattern.

## 7. Migration Guide
- **Phase 1**: Implement `InsightLoader` and basic `ProposalGenerator`.
- **Phase 2**: Retroactively add YAML headers to existing high-value insights in `design/2_operations/ledgers/`.
- **Phase 3**: Run the Crystallizer to generate the first batch of proposals.

```