# Specification: Antigravity DX 2.0 (The Unified Console)

## 1. Overview

**Goal**: Unify the disjointed CLI tools (`gemini-go`, `jules-go`, `audit-go`, `reset-go`) into a single, cohesive developer experience (DX) platform under the entry point `lel` (Living Economic Laboratory). This shift moves the project from a "collection of scripts" to a "Console Application".

**Key Features**:
- **Unified Entry Point**: `lel <command> [args]` replaces all other batch files.
- **Interactive Mission Factory**: A wizard-style interface to create missions without editing Python files.
- **Visual Identity**: Standardized ANSI colors, headers, and status bars for a "Premium" feel.
- **Safety First**: Automatic `.bak` creation during resets and strictly typed DTOs for mission data.

## 2. API Definition (Draft)

The following API draft defines the contracts for the new orchestration layer. This code should reside in `modules/system/orchestration/api.py`.

### `modules/system/orchestration/api.py`

```python
"""
Orchestration Layer API
Defines the contracts for the Antigravity DX 2.0 Console Application.
"""

from typing import Protocol, List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# --- DTOs ---

class MissionType(Enum):
    GEMINI = "gemini"
    JULES = "jules"
    SYSTEM = "system"  # For audit, cleanup, sync

@dataclass
class MissionDTO:
    """Data Transfer Object for a generic mission."""
    key: str
    type: MissionType
    title: str
    instruction: str
    # Context
    context_files: List[str] = field(default_factory=list)
    # Execution
    worker: Optional[str] = None  # e.g., 'spec', 'audit'
    model: Optional[str] = None
    output_path: Optional[str] = None
    # Jules Specific
    command: Optional[str] = None  # 'create', 'test'
    session_id: Optional[str] = None
    wait_for_completion: bool = False
    # Metadata
    created_at: str = ""
    status: str = "pending"

@dataclass
class CommandResultDTO:
    """Standardized result from any console command."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    artifacts: List[str] = field(default_factory=list)

# --- Protocols ---

class UIProtocol(Protocol):
    """Interface for all user interaction. Replaces print/input."""
    
    def print_header(self, text: str, subtext: Optional[str] = None) -> None:
        """Prints a styled header."""
        ...

    def print_success(self, message: str) -> None:
        """Prints a success message (green/check)."""
        ...

    def print_error(self, message: str) -> None:
        """Prints an error message (red/cross)."""
        ...
        
    def print_info(self, message: str) -> None:
        """Prints an info message (blue/info)."""
        ...

    def confirm(self, question: str, default: bool = False) -> bool:
        """Asks for a yes/no confirmation."""
        ...

    def prompt(self, question: str, default: Optional[str] = None, required: bool = True) -> str:
        """Asks for text input."""
        ...
    
    def select(self, question: str, options: List[str]) -> str:
        """Asks the user to select from a list."""
        ...

    def show_spinner(self, text: str) -> Any:
        """Returns a context manager for a loading spinner."""
        ...

class MissionFactoryProtocol(Protocol):
    """Interface for creating and persisting missions."""
    
    def create_mission_interactive(self, ui: UIProtocol) -> MissionDTO:
        """Guides the user through mission creation."""
        ...
    
    def save_mission(self, mission: MissionDTO) -> None:
        """Persists the mission to the registry."""
        ...
        
    def load_mission(self, key: str) -> Optional[MissionDTO]:
        """Retrieves a mission by key."""
        ...

class LauncherServiceProtocol(Protocol):
    """Interface for the core execution logic."""
    
    def execute_mission(self, mission: MissionDTO, ui: UIProtocol) -> CommandResultDTO:
        """Executes a mission based on its type."""
        ...
        
    def run_audit(self, target: str, ui: UIProtocol) -> CommandResultDTO:
        """Runs a system audit."""
        ...
        
    def run_reset(self, ui: UIProtocol, backup: bool = True) -> CommandResultDTO:
        """Resets the environment safely."""
        ...

```

## 3. Detailed Design

### 3.1. Unified Entry Point (`lel.bat`)
The `lel.bat` script will serve as the single entry point, routing commands to a new Python orchestrator `_internal/scripts/lel.py`.

**`lel.bat` Draft:**
```batch
@echo off
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Antigravity DX 2.0 Unified Launcher
python _internal/scripts/lel.py %*

endlocal
```

### 3.2. Architecture Components
The implementation will be modularized into `modules/system/orchestration/`:

1.  **`console_ui.py` (Implements `UIProtocol`)**:
    - Uses `rich` (if available) or standard ANSI escape codes for styling.
    - Provides consistent headers (e.g., `╭─── MISSION: [KEY] ───╮`).
    - Handles input validation loop.

2.  **`mission_factory.py` (Implements `MissionFactoryProtocol`)**:
    - Replaces manual `command_manifest.py` editing.
    - Asking sequence: "Type (Gemini/Jules)?" -> "Title?" -> "Instruction?" -> "Context Files?".
    - Validates inputs against `MissionType` enum.

3.  **`launcher_service.py` (Implements `LauncherServiceProtocol`)**:
    - Contains the logic currently in `launcher.py` but refactored.
    - **Refactoring Note**: The `run_gemini` and `run_jules` functions from the old script will be moved here as methods.
    - **Git Ops**: Integrated into `execute_mission` for relevant mission types (e.g., `git-review`).

4.  **`_internal/scripts/lel.py` (Router)**:
    - Minimal logic.
    - Instantiates `ConsoleUI`, `MissionFactory`, `LauncherService`.
    - Dispatches `sys.argv` to the Service.
    - Handles top-level exception catching and reporting.

### 3.3. Safety Mechanisms
- **Reset Backup**: The `run_reset` method will:
    1. Check for existing `mission_db.json` or `command_manifest.py`.
    2. If found, copy them to `_archive/backups/manifest_<timestamp>.bak`.
    3. Only then perform the reset/overwrite.
- **Strict Typing**: All JSON data loaded from `mission_db.json` will be validated and converted to `MissionDTO` immediately. Invalid entries will be flagged but won't crash the entire console.

## 4. Verification Plan

### 4.1. Automated Tests (`tests/system/test_orchestration.py`)
Since this is a new module, we will create a fresh test suite.

- **`test_mission_factory_interactive`**:
    - **Goal**: Verify the wizard flow.
    - **Method**: Mock `UIProtocol`.
    - **Scenario**: Simulate user inputs `["gemini", "My Task", "Do this", "file.txt"]` and assert `MissionDTO` is created correctly.

- **`test_launcher_routing`**:
    - **Goal**: Verify `lel.py` routes commands to Service.
    - **Method**: Mock `LauncherServiceProtocol`.
    - **Scenario**: Run `lel.py run my-task`, assert `service.execute_mission` is called with "my-task".

- **`test_reset_safety`**:
    - **Goal**: Verify backup creation.
    - **Method**: Mock `pathlib.Path`.
    - **Scenario**: Call `run_reset`, assert `.rename()` or `.copy()` was called before `.unlink()`.

### 4.2. Manual Verification (The "Smoke Test")
1.  Run `lel reset`. Confirm backup created.
2.  Run `lel create`. Follow prompts to create a dummy Gemini mission.
3.  Run `lel run <mission-key>`. Confirm `gemini_worker.py` is invoked.
4.  Run `lel audit`. Confirm audit report is generated.

---

# 📝 Insight Report & Audit (spec-dx-2.0)

## 1. Architectural Insights
- **Decoupling UI**: The biggest win in this spec is decoupling the UI (`UIProtocol`) from the logic. This allows us to potentially swap the CLI for a Web UI or a GUI in the future without rewriting the core mission logic.
- **Protocol-First Design**: By defining `LauncherServiceProtocol` and `MissionFactoryProtocol` first, we ensure that the implementation is testable. We can easily mock the "File System" or "User Input" in tests.
- **Legacy Compatibility**: The spec implies a "Hard Cutover" to `lel.bat`. To ease transition, we should keep `gemini-go.bat` and `jules-go.bat` as simple wrappers that call `lel.py run ...` for a few weeks before deleting them.

## 2. Technical Debt / Risks
- **Dependency on `rich`**: The "Premium UI" goal suggests using a library like `rich`. If we want to keep dependencies zero (standard library only), we will have to implement a small ANSI wrapper in `console_ui.py`. **Decision**: Stick to Standard Library ANSI codes for now to avoid bloating `requirements.txt` for a dev tool.
- **God Script Legacy**: `launcher.py` currently contains *a lot* of implicit logic (e.g., specific flag handling for `jules_bridge.py`). Migrating this logic to `LauncherService` requires careful "Archeology" to ensure no feature is lost.
- **Testing**: We currently lack a robust way to test interactive CLI scripts in our CI. We will rely heavily on `unittest.mock` to simulate user input.

## 3. Audit Evidence (Pre-Flight)
- **Target**: `_internal/scripts/launcher.py`
- **Findings**:
    - L231-259 (`run_reset`): Hardcoded string templates. -> Moved to `MissionFactory`.
    - L45-51 (Print statements): Inconsistent formatting. -> Replaced by `UIProtocol`.
    - L197-229 (Git Ops): Mixed with orchestration logic. -> Moved to `LauncherService`.

## 4. Test Evidence
*N/A - Specification Phase. No code has been implemented yet.*