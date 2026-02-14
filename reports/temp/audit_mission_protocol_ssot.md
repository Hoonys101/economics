I will start by analyzing the provided files to identify the SSoT for mission reporting and then read `_internal/scripts/jules_bridge.py` to confirm how Jules handles prompt construction.

I will list the contents of the `_internal/scripts` directory to verify the existence of `jules_bridge.py` and other relevant files.

I will search for the string `construct_mission_prompt` within the `_internal/scripts` directory, ensuring that ignored files are included in the search.

# Audit Report: Mission Protocol SSoT

## Executive Summary
The Single Source of Truth (SSoT) for mission prompt construction and reporting standards is centralized in `_internal/registry/mission_protocol.py`. Both Jules and Gemini workers utilize the `construct_mission_prompt` function to enforce architectural, testing, and reporting guardrails.

## Detailed Analysis

### 1. Mandatory Reporting Definition
- **Status**: ✅ Centralized
- **Evidence**: `_internal/registry/mission_protocol.py:L67-81`
- **Notes**: The `mandatory_report` variable explicitly defines the `[MANDATORY REPORTING]` block, including requirements for Architectural Insights and Test Evidence.

### 2. Dynamic Reporting Paths
- **Status**: ✅ Implemented
- **Evidence**: `_internal/registry/mission_protocol.py:L68`
- **Notes**: The path is dynamically generated using the `mission_key` parameter: `insight_path = f"communications/insights/{mission_key}.md"`. This ensures each mission has a unique, non-conflicting insight report.

### 3. Standards Enforcement
- **Status**: ✅ Implemented
- **Evidence**:
    - **Architectural Guardrails**: `mission_protocol.py:L58-65` (Zero-Sum, Protocol Purity, DTO Purity, Logic Separation).
    - **Testing Discipline**: `mission_protocol.py:L99-104` (Protocol Fidelity, Mock Drift, Hygiene, Async).
    - **Output Discipline**: `mission_protocol.py:L106-111` (No preamble, respect code fences).
- **Notes**: The function `construct_mission_prompt` wraps the raw instruction with these guardrails, ensuring high-discipline output from both human and AI workers.

### 4. Jules Integration (The "Pin")
- **Status**: ✅ Verified
- **Evidence**: `_internal/scripts/jules_bridge.py:L111` and `L206`
- **Notes**: `jules_bridge.py` is the specific file that "pins" the output structure for Jules by importing and calling `construct_mission_prompt` before dispatching missions to the coding agent.

## Risk Assessment
- **Heuristic Deletion**: `launcher.py:L61` uses a regex-based heuristic (`delete_mission_from_manifest`) to remove completed missions. While effective for standard formats, complex nested dictionary structures in `command_manifest.py` could potentially lead to malformed file states if not carefully managed.
- **Gemini Newline Normalization**: `launcher.py:L152` replaces newlines with pipes (`|`) for Gemini instructions. This is a worker-specific leak into the launcher logic that might need abstraction if other workers require different formatting.

## Conclusion
The mission infrastructure successfully maintains a Single Source of Truth in `mission_protocol.py`. The use of the `mission_key` to generate unique report paths effectively prevents merge conflicts in the `communications/insights/` directory, satisfying the "Clean Room Era" requirements.