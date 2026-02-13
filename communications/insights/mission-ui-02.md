# Technical Insight Report: Mission UI-02 (Dynamic Registry Controls)

## 1. Executive Summary
This mission implemented dynamic UI controls for the Simulation Cockpit, enabling real-time manipulation of `GlobalRegistry` parameters. Key deliverables include a schema-driven rendering engine (`dashboard/components/controls.py`), a YAML-based schema definition (`config/domains/registry_schema.yaml`), and robustness enhancements to `TelemetryCollector`.

## 2. Key Architectural Decisions

### 2.1 Schema-Driven UI with Units
Instead of hardcoding widgets, we adopted a schema-driven approach. `config/domains/registry_schema.yaml` serves as the single source of truth for parameter metadata (min/max, description, category, unit). This allows domain experts to expose new parameters without touching frontend code. We added a `unit` field (e.g., "%", "x") to improve clarity.

### 2.2 Telemetry Robustness (Flat Key Support)
A significant impedance mismatch was identified between `GlobalRegistry` (which supports flat KV pairs like `government.tax_rate`) and `TelemetryCollector` (which assumed object traversal via dot notation).
- **Decision**: Enhanced `TelemetryCollector._resolve_path` to attempt a full-key lookup before falling back to object traversal. This ensures compatibility with both storage patterns.

### 2.3 Command Synchronization & Jitter Prevention
Streamlit's execution model introduces potential "jitter" when backend state updates concurrently with user interaction.
- **Solution**: Implemented a "Sync Logic" in `controls.py`. Local session state is updated from telemetry *only if* the user is not actively modifying that specific parameter (determined by `pending_commands` queue). This ensures backend updates (e.g., adaptive policy changes) are reflected in the UI without overwriting user input during adjustment.
- **Debouncing**: Leveraged Streamlit's native `st.slider(on_change=...)` behavior, which triggers only on handle release, preventing command floods.

### 2.4 Mismatch Handling & God-Mode Lock
- **God-Mode**: The sidebar toggle acts as a master switch. When disabled, all dynamic controls are rendered in a read-only state.
- **Registry Mismatch**: If a parameter defined in the schema is missing from the live registry (telemetry), the widget is automatically disabled and labeled with "⚠️ N/A" to prevent invalid commands.

### 2.5 Hot-Reloading
`RegistryService` re-instantiates and reloads the YAML schema on every Streamlit script execution. This supports hot-reloading: developers can edit `registry_schema.yaml` while the dashboard is running, and changes appear immediately upon the next refresh.

## 3. Technical Debt & Future Work

### 3.1 Shadow Value Issue
Currently, `CommandService` updates `GlobalRegistry` using `set(key, value)`. If the simulation engine uses object attributes (e.g., `government.tax_rate`) instead of querying the registry, a "shadow value" is created where the Registry holds the desired state, but the Agent holds the actual state.
- **Mitigation**: Future refactoring should ensure Agents bind their parameters to `GlobalRegistry` or `CommandService` should propagate changes to Agents explicitly.

### 3.2 Telemetry Latency
The UI relies on `telemetry_buffer` which is updated via WebSocket. There is a slight latency between command commit and visual feedback. The "Pending" state in the UI helps mitigate this perception.

## 4. Test Evidence

### Unit Tests
Executed `pytest` on relevant modules. All tests passed, covering schema loading, telemetry robustness, and UI control logic (including mismatch handling).

```text
tests/unit/dashboard/services/test_schema_loader.py::TestSchemaLoader::test_load_schema_file_not_found PASSED
tests/unit/dashboard/services/test_schema_loader.py::TestSchemaLoader::test_load_schema_invalid_structure PASSED
tests/unit/dashboard/services/test_schema_loader.py::TestSchemaLoader::test_load_schema_success PASSED
tests/unit/dashboard/services/test_schema_loader.py::TestSchemaLoader::test_load_schema_yaml_error PASSED
tests/unit/modules/system/test_telemetry_robustness.py::TestTelemetryRobustness::test_flat_key_resolution PASSED
tests/unit/modules/system/test_telemetry_robustness.py::TestTelemetryRobustness::test_mixed_resolution PASSED
tests/unit/dashboard/components/test_controls.py::TestControls::test_missing_registry_value_disables_widget PASSED
tests/unit/dashboard/components/test_controls.py::TestControls::test_on_change_generates_command PASSED
tests/unit/dashboard/components/test_controls.py::TestControls::test_render_dynamic_controls_tabs PASSED
```

### Frontend Verification
Verified using Playwright script `verification/verify_controls.py`.
- **Scenario**: Start app, verify initial state, enable God Mode, verify controls appear.
- **Screenshot**: `verification/step2_god_mode.png` confirms controls are visible and unlocked when God Mode is enabled.
