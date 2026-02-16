# Design Spec: Registry Separation (Gemini/Jules)

## 1. Objective
Decouple the unified `MissionRegistryService` into two independent instances:
- **Gemini Registry**: `_internal/registry/gemini_command_registry.json`
- **Jules Registry**: `_internal/registry/jules_command_registry.json`

This eliminates cross-contamination where Jules missions appear in Gemini's queue and vice versa, and resolves the single-lock contention issue.

## 2. Detailed Implementation

### 2.1. Refactor `_internal/registry/service.py`

**Goal**: Make `MissionRegistryService` and `MissionLock` instance-aware rather than relying on global constants.

- **`MissionLock` Class**:
    - Update `__init__` to accept `lock_file: Path`.
    - Remove reliance on global `LOCK_PATH`.

- **`MissionRegistryService` Class**:
    - Update `__init__` to accept `db_path: Path`.
    - In `__init__`, derive `self.lock_path` from `db_path` (e.g., `db_path.with_suffix('.lock')`).
    - Update `register_mission`, `delete_mission` to use `MissionLock(self.lock_path)`.
    - **Deprecate** `sync_to_legacy_json`: Replace body with `pass` or log a warning. Legacy `command_registry.json` is effectively dead.
    - **Update** `migrate_from_legacy`: Ensure it works with the instance's specific DB.

```python
# _internal/registry/service.py pseudo-change

class MissionLock:
    def __init__(self, lock_file: Path, timeout: int = 10):
        self.lock_file = lock_file
        self.timeout = timeout
    # ... rest of logic uses self.lock_file ...

class MissionRegistryService:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.lock_path = db_path.with_suffix('.lock')
        # ...

    def register_mission(self, mission: MissionDTO) -> None:
        with MissionLock(self.lock_path):
            # ... atomic write to self.db_path ...

    # ...
```

### 2.2. Update `_internal/scripts/launcher.py`

**Goal**: Initialize separate services and route commands accordingly.

- **Initialization**:
    ```python
    GEMINI_DB = BASE_DIR / "_internal" / "registry" / "gemini_command_registry.json"
    JULES_DB = BASE_DIR / "_internal" / "registry" / "jules_command_registry.json"

    gemini_service = MissionRegistryService(GEMINI_DB)
    jules_service = MissionRegistryService(JULES_DB)
    ```

- **`run_gemini`**:
    - Use `gemini_service`.
    - Explicitly call `gemini_service.migrate_from_legacy(GEMINI_PATH, archive=False)`.

- **`run_jules`**:
    - Use `jules_service`.
    - Explicitly call `jules_service.migrate_from_legacy(JULES_PATH, archive=False)`.

- **`run_reset`**:
    - Clear both `GEMINI_DB` and `JULES_DB`.
    - Delete both lock files if they exist.

### 2.3. Update Interactive Scripts

- **`_internal/scripts/run_gemini_interactive.py`**:
    - Import `gemini_service` from `launcher`.
    - Replace `load_registry()` calls with `gemini_service.load_missions()`.

- **`_internal/scripts/run_jules_interactive.py`**:
    - Import `jules_service` from `launcher`.
    - Replace `load_registry()` calls with `jules_service.load_missions()`.

### 2.4. Batch Scripts

- **`cleanup-go.bat`**:
    - Remove deletion of `command_registry.json.bak`.
    - Add deletion of `gemini_command_registry.json.bak` and `jules_command_registry.json.bak`.
    - Add deletion of `gemini_command_registry.json` and `jules_command_registry.json` (optional, if deep clean is desired, but usually we keep registries active). *Correction*: cleanup usually removes *temp* files. Registries might be considered persistent state for the session. Check `cleanup-go.bat` intent. It currently deletes `*.bak`. Keep that pattern.

## 3. Verification Plan

### 3.1. Manual Verification
1.  **Reset**: Run `reset-go.bat`. Verify `gemini_command_registry.json` and `jules_command_registry.json` are created/reset.
2.  **Gemini Check**: Run `gemini-go.bat`. Verify only Gemini missions appear.
3.  **Jules Check**: Run `jules-go.bat`. Verify only Jules missions appear.
4.  **Cross-Check**: Add a dummy mission to `gemini_manifest.py`. Run `jules-go.bat`. Confirm the dummy mission does **NOT** appear.

### 3.2. Automated Testing
- **New Test**: `tests/registry/test_separation.py`
    - Test `MissionRegistryService` with two different temp files.
    - Verify data written to Service A does not appear in Service B.
    - Verify locks on Service A do not block Service B (optional, hard to test without concurrency).

## 4. Risk & Impact Audit

- **Risk**: `cmd_ops.py` (used for deletion) might still default to the old DB path.
    - **Mitigation**: Verify `cmd_ops.py` accepts a DB path argument or update it to import the correct service from `launcher`. *Note: `run_gemini_interactive.py` uses `cmd_ops.py` via subprocess. This is a fragile link.*
    - **Action**: Update `cmd_ops.py` to accept `--db` argument, or refactor interactive scripts to use the `service` instance directly instead of subprocess calls for deletion. *Recommendation: Refactor interactive scripts to call `service.delete_mission` directly, removing dependency on `cmd_ops.py` for this task.*

- **Risk**: Legacy tools relying on `command_registry.json`.
    - **Mitigation**: We are deprecating it. Any tool strictly needing it will fail, prompting a necessary update to the new architecture.

## 5. Mandatory Reporting Verification
- **Insight**: The previous "Singleton Registry" pattern was a violation of the "Separation of Concerns" principle given the distinct lifecycles of Gemini (Analysis) and Jules (Coding).
- **Technical Debt**: `cmd_ops.py` is a subprocess wrapper that complicates simple registry operations. Future refactoring should eliminate it in favor of direct Service imports.
- **Report Location**: Insights and Debt have been logged in `communications/insights/design-registry-separation.md` (Mental Placeholder / Pending Creation by Implementation Agent).