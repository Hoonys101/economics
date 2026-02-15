_internal/registry/api.py
```python
"""
Mission Registry API Definition.
Defines the Data Transfer Objects and Service Interface for the Mission Registry System.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Protocol, Union, Any, runtime_checkable
from enum import Enum

class MissionType(Enum):
    JULES = "jules"
    GEMINI = "gemini"

@dataclass
class MissionDTO:
    """
    Data Transfer Object representing a single mission (task).
    Unified structure for both Jules and Gemini missions.
    """
    key: str
    title: str
    type: MissionType
    instruction_raw: str  # The raw instruction without protocol injections
    
    # Common Optional
    status: str = "pending"
    created_at: str = ""
    
    # Jules Specific
    command: Optional[str] = None  # 'create', 'send-message'
    file_path: Optional[str] = None
    wait: bool = False
    session_id: Optional[str] = None
    
    # Gemini Specific
    worker: Optional[str] = None  # 'spec', 'reporter', etc.
    context_files: List[str] = field(default_factory=list)
    output_path: Optional[str] = None
    model: Optional[str] = None
    audit_requirements: Optional[str] = None

@runtime_checkable
class IMissionRegistryService(Protocol):
    """
    Interface for the Mission Registry Service.
    Handles CRUD operations for missions and protocol injection.
    """
    
    def load_missions(self) -> Dict[str, MissionDTO]:
        """
        Loads all missions from the persistence layer (mission_db.json).
        """
        ...

    def get_mission(self, key: str) -> Optional[MissionDTO]:
        """
        Retrieves a specific mission by key.
        """
        ...

    def register_mission(self, mission: MissionDTO) -> None:
        """
        Saves or updates a mission atomically.
        """
        ...

    def delete_mission(self, key: str) -> bool:
        """
        Removes a mission by key. Returns True if found and deleted.
        """
        ...

    def get_mission_prompt(self, key: str) -> str:
        """
        Constructs the full, protocol-compliant prompt for a mission.
        Injects META, GUARDRAILS, and OUTPUT_DISCIPLINE dynamically.
        """
        ...

    def migrate_from_legacy(self, legacy_file_path: str) -> int:
        """
        One-time migration from legacy command_manifest.py to mission_db.json.
        Returns the number of missions migrated.
        """
        ...
```

design/3_work_artifacts/specs/SPEC_17_1_MANIFEST_SERVICE.md
```markdown
# Spec 17.1: Structured Mission Registry (JSON)

## 1. Introduction

-   **Purpose**: To migrate the mission registry from a fragile "Data as Code" Python file (`command_manifest.py`) to a robust, serialized JSON database (`mission_db.json`), managed by a dedicated Service.
-   **Scope**:
    -   Create `MissionRegistryService`.
    -   Define `MissionDTO` and JSON Schema.
    -   Refactor `launcher.py` to use the Service.
    -   Implement "Protocol Injection" to ensure guardrails are applied dynamically.
-   **Goals**:
    -   Eliminate Regex-based file editing in `launcher.py`.
    -   Prevent "Stale Guardrails" by decoupling data from protocol strings.
    -   Ensure thread-safe/process-safe mission management.

## 2. System Architecture

### 2.1. Component Diagram

```mermaid
graph TD
    CLI[Launcher (CLI)] -->|Uses| Service[MissionRegistryService]
    Service -->|Reads/Writes| DB[(mission_db.json)]
    Service -->|Injects| Protocol[MissionProtocol (py)]
    Service -->|Locks| LockFile[mission.lock]
```

### 2.2. Data Model (JSON Schema)

The `mission_db.json` will store the *definitions* of missions, not the *protocols*.

```json
{
  "_meta": {
    "version": "1.0",
    "updated": "2026-02-14T..."
  },
  "missions": {
    "spec-17-1": {
      "type": "gemini",
      "title": "Migrate Manifest",
      "instruction_raw": "Design the migration...",
      "worker": "spec",
      "context": ["path/to/file"],
      "output": "path/to/output"
    },
    "refactor-auth": {
      "type": "jules",
      "title": "Refactor Auth",
      "instruction_raw": "Update auth logic...",
      "command": "create",
      "wait": true
    }
  }
}
```

## 3. Detailed Design

### 3.1. Class: `MissionRegistryService`

-   **Responsibility**: The Single Source of Truth for mission data.
-   **Location**: `_internal/registry/service.py`
-   **Dependencies**: `json`, `pathlib`, `_internal.registry.api` (DTOs), `_internal.registry.mission_protocol` (Constants).

#### Key Methods (Logic)

1.  **`load_missions()`**:
    -   Read `mission_db.json`.
    -   Parse JSON into `MissionDTO` objects.
    -   Handle `JSONDecodeError` gracefully (return empty or backup).

2.  **`save_mission(dto)` / `delete_mission(key)`**:
    -   **Concurrency**: MUST use `MissionLock` (encapsulated within the service or imported).
    -   **Atomic Write**: Read -> Update Dict -> Write to Temp -> Rename to `mission_db.json`.

3.  **`get_mission_prompt(key)` (Crucial Protocol Injection)**:
    -   Retrieve `MissionDTO`.
    -   Import `construct_mission_prompt` from `_internal.registry.mission_protocol`.
    -   Call `construct_mission_prompt(key, dto.title, dto.instruction_raw)`.
    -   **Why**: This satisfies the audit constraint. The JSON only holds the "What", the Service injects the "How" (Safety Protocols).

4.  **`migrate_from_legacy()`**:
    -   Check if `mission_db.json` exists. If yes, skip.
    -   Import `command_manifest.py` dynamically.
    -   Iterate `JULES_MISSIONS` and `GEMINI_MISSIONS`.
    -   Convert to `MissionDTO`s.
    -   Save to JSON.
    -   Rename `command_manifest.py` to `command_manifest.py.bak`.

### 3.2. Refactoring `launcher.py`

-   **Remove**:
    -   `delete_mission_from_manifest` (Regex logic).
    -   `_load_manifest`, `_build_json_from_manifest`.
    -   `MissionLock` (Move this class to `_internal/registry/lock.py` or inside Service).
-   **Update**:
    -   `run_gemini`:
        ```python
        service = MissionRegistryService()
        mission = service.get_mission(key)
        # prompt construction delegated or kept simple using DTO
        prompt = service.get_mission_prompt(key)
        # execute worker...
        service.delete_mission(key) # Atomic delete
        ```
    -   `run_jules`: Similar update.

## 4. Verification Plan

### 4.1. Migration Test
1.  Populate `command_manifest.py` with 1 dummy Jules mission and 1 Gemini mission.
2.  Run `launcher.py migrate` (or auto-trigger).
3.  **Verify**: `mission_db.json` contains keys. `command_manifest.py` is renamed.

### 4.2. Protocol Injection Verification
1.  Register a mission with instruction "Say Hello".
2.  Call `service.get_mission_prompt(key)`.
3.  **Verify**: Output string contains `META`, `GUARDRAILS`, and "Say Hello".

### 4.3. Concurrency Test
1.  Spawn 2 processes trying to `delete_mission` the same key simultaneously.
2.  **Verify**: One succeeds, one handles "Not Found" gracefully. File is not corrupted.

## 5. Risk Management

-   **Bootstrapping**: If `launcher.py` depends on the Service, and the Service depends on `mission_protocol.py`, ensure no circular imports with `launcher.py`. `launcher.py` should remain the entry point.
-   **Locking**: File locking on Windows can be tricky. Ensure `MissionLock` handles stale locks (as the current implementation attempts to do).

## 6. Implementation Steps
1.  Create `_internal/registry/api.py`.
2.  Create `_internal/registry/service.py` (Implement Service & Locking).
3.  Update `launcher.py` to strip regex logic and integrate Service.
4.  Run Migration.

```

communications/insights/spec-17-1-manifest-json.md
```markdown
# Architectural Insight: Spec 17.1 (Manifest Migration)

## 1. Technical Debt Retired
-   **TD-SYS-BATCH-FRAGILITY (Data as Code)**: Removed the fragility of editing Python files via Regex. This was a major stability risk where a single syntax error could crash the entire CLI.
-   **TD-SYS-REGEX-PARSING**: The complex, brittle regex logic in `launcher.py` (50+ lines) is replaced by standard `json` library usage.

## 2. Architectural Decisions
-   **Protocol Injection Pattern**: We decided to **not** store the full prompt in the database. Instead, `mission_db.json` stores only the raw instruction. The `MissionRegistryService` is responsible for re-hydrating the instruction with `META`, `GUARDRAILS`, and `OUTPUT_DISCIPLINE` at runtime. This ensures that even old pending missions will always use the *latest* safety protocols when executed.
-   **Service-Based Locking**: File locking logic is moved from the consumer (`launcher.py`) to the provider (`MissionRegistryService`). This enforces transactional integrity for all clients, not just the CLI.

## 3. Risk Analysis
-   **Migration One-Way Valve**: The migration is designed as a "One-Way Valve". Once `mission_db.json` is authoritative, `command_manifest.py` is deprecated. Reverting requires manual intervention.
-   **Context Loss**: JSON cannot store Python objects (like complex context dictionaries if they existed). We restricted `context` to `List[str]` (file paths), which enforces the "Context as File" best practice.

## 4. Pre-Implementation Audit (Self-Correction)
-   **Issue**: `launcher.py` currently handles `construct_mission_prompt`.
-   **Resolution**: The `MissionRegistryService` exposes `get_mission_prompt(key)` to encapsulate this logic, preventing `launcher.py` from needing direct knowledge of protocol internals.
```