# Technical Report: CLI Dispatch Pipeline Audit

## Executive Summary
The audit of the `jules-go` and `gemini-go` dispatch pipelines confirms a critical data loss vulnerability during the migration of JULES missions from Python manifests to JSON storage. The root cause is an asymmetric implementation in `MissionRegistryService.migrate_from_registry_dir()`, where the JULES `MissionDTO` constructor omits the `context_files` field, causing all manually defined context references to be stripped upon registration.

## Detailed Analysis

### 1. Pipeline Trace: Dispatch Lifecycle
The following sequence describes the execution flow for a CLI mission:

1.  **Entry Point**: `jules-go.bat` (or `gemini-go.bat`) invokes `_internal/scripts/launcher.py` with the `jules` (or `gemini`) command prefix.
2.  **Bootstrap**: `launcher.py` initializes a `CommandContext` and retrieves the appropriate dispatcher (`JulesDispatcher` or `GeminiDispatcher`) from the `fixed_registry`.
3.  **Auto-Migration**: Before execution, the dispatcher calls `service.migrate_from_registry_dir()`. This parses `*_manifest.py` files, creates `MissionDTO` objects, and persists them to `*_command_registry.json`.
4.  **Retrieval**: The dispatcher fetches the `MissionDTO` from the JSON database using the provided mission key.
5.  **Execution**: 
    -   **Gemini**: Dispatched via `gemini_worker.py`.
    -   **Jules**: Dispatched via `jules_bridge.py`.
6.  **Cleanup**: Upon successful exit, the mission is deleted from the JSON database.

### 2. Root Cause Verification: JULES Data Loss
Evidence found in `_internal/registry/service.py`:

- **GEMINI Migration (L188-195)**: Correct implementation.
  ```python
  context_files=m_data.get("context_files", []), # Correctly retrieved
  output_path=m_data.get("output_path"),
  model=m_data.get("model"),
  audit_requirements=m_data.get("audit_requirements")
  ```
- **JULES Migration (L170-179)**: Faulty implementation.
  ```python
  dto = MissionDTO(
      key=key,
      title=m_data.get("title", key),
      type=MissionType.JULES,
      instruction_raw=m_data.get("instruction", ""),
      command=m_data.get("command", "create"),
      file_path=m_data.get("file"),
      wait=m_data.get("wait", False),
      session_id=m_data.get("session_id")
      # context_files is missing here
  )
  ```
Because `context_files` defaults to an empty list in the `MissionDTO` dataclass, any files specified in `jules_manifest.py` are discarded during this step.

### 3. Field Audit: Silently Dropped Attributes
In addition to `context_files`, the following fields are silently dropped for JULES missions during both `migrate_from_registry_dir` and `migrate_from_legacy`:

| Field | Impact | Notes |
| :--- | :--- | :--- |
| `context_files` | **CRITICAL** | Prevents Jules from receiving specific file context required for implementation. |
| `worker` | **LOW** | Currently hardcoded to `"spec"` in `JulesDispatcher`. |
| `model` | **MEDIUM** | Prevents overriding the default LLM for specific JULES missions. |
| `output_path` | **LOW** | JULES outputs are typically logged to `communications/jules_logs/`. |
| `audit_requirements`| **MEDIUM** | Prevents passing specialized audit constraints to the bridge. |

### 4. Interactive Menu Behavior
The `jules-go` (without args) launches `run_jules_interactive.py`. This script reads directly from the JSON database (`jules_command_registry.json`) to populate the menu. Since the JSON is populated by the faulty migration logic, the interactive menu presents missions that are already "context-starved," leading to session creations that lack the necessary background files.

## Risk Assessment
The primary risk is **Contextual Blindness**. If a user defines a mission to "Update logic in X.py" and includes `X.py` in `context_files`, JULES will not receive the content of `X.py` because the link was broken during migration. This leads to hallucination or "File Not Found" errors during the session.

## Fix Specification

### 1. Update `_internal/registry/service.py`
Modify both `migrate_from_registry_dir` and `migrate_from_legacy` to include the missing fields in the JULES section:

```python
# In migrate_from_registry_dir (approx L170)
# In migrate_from_legacy (approx L258)
dto = MissionDTO(
    key=key,
    title=m_data.get("title", key),
    type=MissionType.JULES,
    instruction_raw=m_data.get("instruction", ""),
    command=m_data.get("command", "create"),
    file_path=m_data.get("file"),
    wait=m_data.get("wait", False),
    session_id=m_data.get("session_id"),
    context_files=m_data.get("context_files", []),  # ADD THIS
    worker=m_data.get("worker", "spec"),            # ADD THIS
    model=m_data.get("model"),                      # ADD THIS
    audit_requirements=m_data.get("audit_requirements") # ADD THIS
)
```

### 2. Update `_internal/registry/commands/dispatchers.py`
Modify `JulesDispatcher.execute` to honor the `mission.model` and `mission.worker` if present, rather than hardcoding.

## Conclusion
The pipeline is structurally sound, but the JULES data ingestion logic is incomplete. Implementing the fix above will restore full context injection capabilities to the JULES orchestration CLI.