"""
Mission Protocol Definitions.
Contains the safety protocols and prompt construction logic for missions.
"""

META = """
MISSION: {title}
Mission Key: {key}
============================================================
"""

GUARDRAILS = """
[PROJECT MANDATE]
============================================================

🛡️ [ARCHITECTURAL GUARDRAILS]
1. Zero-Sum Integrity: No magic money creation/leaks. All transfers must be balanced.
2. Protocol Purity: Use `@runtime_checkable` Protocols and `isinstance()`. Avoid `hasattr()`.
3. DTO Purity: Use typed DTOs/Dataclasses for cross-boundary data. Avoid raw dicts.
4. Logic Separation: Keep business logic in Systems/Services, data in State/Repository.

🚨 [MANDATORY REPORTING]
Before completing this task, you MUST create a NEW insight report file at:
`communications/insights/{key}.md`

DO NOT append to `manual.md` or any other shared file. This is CRITICAL to prevent merge conflicts.

The report MUST include:
1. [Architectural Insights]: Technical debt identified or architectural decisions made.
2. [Test Evidence]: Copy-paste the literal output of `pytest` demonstrating that your changes pass.
(No verified test logs = Submission Rejected)

🧪 [TESTING DISCIPLINE]
1. Protocol Fidelity: When mocking Protocols, explicitly implement required methods or use specs. Enforce `isinstance(mock, Protocol)`.
2. No Mock Drift: Do not invent attributes on mocks. Use `MagicMock(spec=RealClass)`.
3. Hygiene: NEVER patch `sys.modules` globally in a test file. Use `conftest.py` or `patch.dict`.
4. Async: Use `pytest-asyncio` with proper loop scope. Avoid mixing thread/process loops.
"""

OUTPUT_DISCIPLINE = """
🚨 [OUTPUT DISCIPLINE]
1. Output ONLY the file content or the specific Markdown block requested.
2. DO NOT include conversational preamble (e.g., 'Sure!', 'I have updated...').
3. Respect code fences and file-level termination rules.

============================================================
"""

WORKER_MODEL_MAP = {
    # Reasoning Tier: gemini-3-pro-preview
    "spec": "gemini-3-pro-preview",
    "scribe": "gemini-3-pro-preview",
    "writer": "gemini-3-pro-preview",
    "reviewer": "gemini-3-pro-preview",
    "git-review": "gemini-3-pro-preview",
    
    # High-Volume Tier: gemini-3-flash-preview
    "audit": "gemini-3-flash-preview",
    "analyze": "gemini-3-flash-preview",
    "risk": "gemini-3-flash-preview",
    "report": "gemini-3-flash-preview",
    "crystallizer": "gemini-3-pro-preview",
}

def construct_mission_prompt(key: str, title: str, instruction_raw: str) -> str:
    """
    Constructs the full mission prompt by injecting protocols.
    """
    prompt = META.format(title=title, key=key)
    prompt += instruction_raw + "\n\n"
    prompt += GUARDRAILS.format(key=key)
    prompt += OUTPUT_DISCIPLINE
    return prompt

from pathlib import Path
from enum import Enum

class ArtifactType(Enum):
    SPEC = "spec"
    AUDIT = "audit"
    REVIEW = "review"
    REPORT = "report"

def get_artifact_path(mission_key: str, artifact_type: ArtifactType) -> Path:
    """
    Centralized resolver for mission artifacts.
    Enforces UPS-4.2 Directory Structure.
    """
    # Base is relative to where this script is imported, usually project root
    # But safer to use relative paths from CWD if running from root
    
    if artifact_type == ArtifactType.SPEC:
        return Path(f"design/3_work_artifacts/specs/MISSION_{mission_key}_SPEC.md")
    elif artifact_type == ArtifactType.AUDIT:
        return Path(f"design/3_work_artifacts/audits/MISSION_{mission_key}_AUDIT.md")
    elif artifact_type == ArtifactType.REVIEW:
        return Path(f"design/_archive/reviews/MISSION_{mission_key}_REVIEW.md")
    elif artifact_type == ArtifactType.REPORT:
        return Path(f"design/3_work_artifacts/reports/active/REPORT_{mission_key}.md")
    
    raise ValueError(f"Unknown artifact type: {artifact_type}")
