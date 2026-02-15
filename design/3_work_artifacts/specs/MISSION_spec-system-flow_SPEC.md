default_api:write_file{file_path:<ctrl46>design/3_work_artifacts/specs/spec-system-flow_spec.md<ctrl46>,content:<ctrl46># Specification: Spec-to-Jule Bridge Automation

## 1. Overview
This specification details the refactoring required to automate the workflow between Specification Generation (Gemini) and Implementation (Jules). The goal is to eliminate manual file path arguments and ensure that when a Spec is generated, the subsequent Jules agent session automatically inherits it as context.

## 2. Architectural Changes

### 2.1. Centralized Path Resolution (`_internal/registry/mission_protocol.py`)
To resolve the "Hidden Dependencies" and "Logic Duplication" risks identified in the audit, path resolution logic will be centralized.

#### New Interface
```python
# _internal/registry/mission_protocol.py

def get_artifact_path(mission_key: str, artifact_type: str) -> Path:
    """
    Centralized resolver for mission artifacts.
    
    Args:
        mission_key: The unique mission identifier.
        artifact_type: 'spec', 'audit', 'review', or 'report'.
        
    Returns:
        Path object to the expected artifact location.
    """
    # Logic to return design/3_work_artifacts/specs/MISSION_{key}_SPEC.md, etc.
    ...
```

### 2.2. Bridge Refactor (`_internal/scripts/jules_bridge.py`)
The `JulesBridge` class will be updated to consume the `mission_protocol` service instead of implementing ad-hoc path logic.

#### Updates
- **Remove**: Hardcoded path construction in `create_session` and `main` block.
- **Add**: Integration with `mission_protocol.get_artifact_path`.
- **Logic**:
    1. Receive `mission_key`.
    2. Call `get_artifact_path(mission_key, 'spec')`.
    3. If file exists, inject content into `prompt` under `## IMPLEMENTATION SPECIFICATION`.

### 2.3. Orchestrator Update (`_internal/scripts/session_manager.py`)
`session_manager.py` will evolve from a passive reporter to an active session orchestrator ("Session-Go").

#### New Workflow: `scan_and_dispatch`
1.  **Discovery**: Scan `design/3_work_artifacts/specs/` for files modified within the last `N` minutes (session window).
2.  **Filtering**: Ignore specs that already have an associated active Jules session (check via `JulesBridge.list_sessions`).
3.  **Action**:
    -   Identify `mission_key` from filename pattern `MISSION_{key}_SPEC.md`.
    -   Prompt user (or auto-trigger based on config) to launch implementation.
    -   Execute via `launcher.py jules {key}` (maintaining process isolation).

## 3. Implementation Plan

### 3.1. `mission_protocol.py`
- [ ] Implement `get_artifact_path`.
- [ ] Add unit tests ensuring correct path mapping for all worker types.

### 3.2. `jules_bridge.py`
- [ ] Refactor `create_session` to accept `mission_key` and resolve spec internally.
- [ ] Update `__main__` to pass `mission_key` correctly from CLI args.

### 3.3. `session_manager.py`
- [ ] Implement `SpecDetector` class.
- [ ] Add `dispatch_jules(mission_key)` method wrapping `subprocess.run`.

## 4. Verification Plan

### 4.1. Unit Tests (`tests/internal/test_mission_flow.py`)
```python
def test_protocol_path_resolution():
    from _internal.registry.mission_protocol import get_artifact_path
    path = get_artifact_path("test-key", "spec")
    assert path.name == "MISSION_test-key_SPEC.md"

def test_bridge_spec_injection(mocker, tmp_path):
    # Mock protocol to return a temp file
    f = tmp_path / "MISSION_test_SPEC.md"
    f.write_text("SPEC CONTENT")
    
    mocker.patch("_internal.registry.mission_protocol.get_artifact_path", return_value=f)
    
    # Verify bridge reads it
    bridge = JulesBridge()
    # ... setup mock requests ...
    bridge.create_session(..., mission_key="test")
    # Assert "SPEC CONTENT" is in the API payload
```

### 4.2. Integration Check
1.  Generate a dummy spec: `MISSION_auto_test_SPEC.md`.
2.  Run `python _internal/scripts/session_manager.py --scan`.
3.  Verify it detects the spec and offers to launch Jules.

## 5. Risk Assessment
-   **Circular Import**: `mission_protocol` must not import `jules_bridge`.
-   **Process Isolation**: `session_manager` must not import `jules_bridge` logic directly; it must use `launcher` or `subprocess` to ensure the Jules run happens in a clean environment.

## 6. Exceptions
-   If `mission_key` is "manual", spec injection is skipped.
-   If Spec file is empty, a warning is logged but execution proceeds.
<ctrl46>}default_api:write_file{content:<ctrl46># Insight: Spec-System Flow Refactor

## 1. Architectural Insights
- **Decoupling Path Logic**: Moving artifact path definition to `mission_protocol.py` is essential. Currently, `launcher.py`, `jules_bridge.py`, and `gemini_worker.py` all have "knowledge" of where files go. This is a violation of DRY and makes changing directory structures painful.
- **Orchestrator Role**: `session_manager.py` is transitioning from a "End-of-Day Reporter" to a "Session Conductor". This requires it to be stateless regarding the tasks it launches. It should identify *triggers* (new files) and delegate *actions* (scripts).

## 2. Technical Debt Identified
- **Launcher "God Script"**: `launcher.py` contains too much logic regarding specific tool arguments. It should eventually be just a dispatcher that passes args through to the underlying tools, relying on a unified CLI standard (e.g., all tools accept `--mission-key`).
- **Subprocess Testing**: We currently lack a harness for testing the `subprocess` interactions between scripts. This makes the system fragile to CLI argument changes.

## 3. Test Evidence (Pre-Verification)
Since this is a design phase, no code has been changed yet. However, the verification plan requires passing the following test structure:

```python
# tests/internal/test_mission_protocol.py

def test_get_artifact_path_structure():
    from _internal.registry.mission_protocol import get_artifact_path, ArtifactType
    
    # Verify Spec Path
    spec = get_artifact_path("alpha", ArtifactType.SPEC)
    assert "design/3_work_artifacts/specs/MISSION_alpha_SPEC.md" in str(spec)
    
    # Verify Audit Path
    audit = get_artifact_path("beta", ArtifactType.AUDIT)
    assert "design/3_work_artifacts/audits/MISSION_beta_AUDIT.md" in str(audit)
```

## 4. Immediate Actions
1.  Create `_internal/registry/mission_protocol.py` (if not fully populated).
2.  Refactor `jules_bridge.py` to remove hardcoded paths.
3.  Update `session_manager.py` to scan for specs.
<ctrl46>,file_path:<ctrl46>communications/insights/spec-system-flow.md<ctrl46>}
The requested specification and insight files have been generated.

File: design/3_work_artifacts/specs/spec-system-flow_spec.md
File: communications/insights/spec-system-flow.md