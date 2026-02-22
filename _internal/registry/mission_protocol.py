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
5. DTO/API Audit: "DTO나 API"가 변경되는 구현업무인 경우 구현체를 전수조사하여 변동을 반영하시오.

🚨 [MANDATORY REPORTING]
Before completing this task, you MUST create a NEW insight report file at:
`communications/insights/{key}.md`

DO NOT append to `manual.md` or any other shared file. This is CRITICAL to prevent merge conflicts.

The report MUST include:
1. [Architectural Insights]: Technical debt identified or architectural decisions made.
2. [Regression Analysis]: If existing tests were broken, explain why and how you fixed them to align with the new architecture.
3. [Test Evidence]: Copy-paste the FULL literal output of `pytest` demonstrating that ALL affected tests (new and legacy) pass. 
(No verified test logs or failure analysis = Submission Rejected)

🧪 [TESTING DISCIPLINE]
1. Protocol Fidelity: When mocking Protocols, explicitly implement required methods or use specs. Enforce `isinstance(mock, Protocol)`.
2. No Mock Drift: Do not invent attributes on mocks. Use `MagicMock(spec=RealClass)`.
3. Legacy Compatibility: Ensure that refactors do not break existing unit, system, or integration tests. If a signature changes, you MUST update all call sites.
4. Total Test Pass Mandate: Your submission MUST NOT introduce ANY new failures. The ENTIRE existing test suite (pytest tests/) must pass 100% before submission. 
(Any regression in existing functionality = Submission Rejected)
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
    "git": "gemini-3-pro-preview",
    "git-review": "gemini-3-pro-preview",
    "context": "gemini-3-pro-preview",
    "crystallizer": "gemini-3-pro-preview",
    
    # High-Volume Tier: gemini-3-flash-preview
    "report": "gemini-3-flash-preview",
    "verify": "gemini-3-flash-preview",
    "audit": "gemini-3-flash-preview",
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
        return Path(f"gemini-output/spec/MISSION_{mission_key}_SPEC.md")
    elif artifact_type == ArtifactType.AUDIT:
        return Path(f"gemini-output/audit/MISSION_{mission_key}_AUDIT.md")
    elif artifact_type == ArtifactType.REVIEW:
        return Path(f"gemini-output/review/MISSION_{mission_key}_REVIEW.md")
    elif artifact_type == ArtifactType.REPORT:
        return Path(f"gemini-output/insight/REPORT_{mission_key}.md")
    
    raise ValueError(f"Unknown artifact type: {artifact_type}")
