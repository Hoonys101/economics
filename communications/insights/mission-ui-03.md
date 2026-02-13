# Mission UI-03: Scenario Progress & KPI Visualizers Insights

## 1. Overview
This mission focused on implementing the "Scenario Progress & KPI Visualizers" for the GodMode Dashboard. The goal was to visualize scenario verification results and enable drill-down capabilities into micro-data using On-Demand Telemetry.

## 2. Architectural Decisions & Technical Insights

### 2.1 Component-Driven Masking (Pull Model)
We implemented a "Pull Model" where the dashboard UI determines the required telemetry mask based on active visualizers.
- **Mechanism**: `dashboard/components/main_cockpit.py` aggregates `required_mask` from all active visualizers (e.g., `AgentHeatmapVisualizer`).
- **Communication**: If the aggregated mask changes, the UI sends an `UPDATE_TELEMETRY` command to the simulation via WebSocket.
- **Backend Logic**: `CommandService` handles this command by updating the `TelemetryCollector`'s subscription list dynamically.

### 2.2 DTO Enhancements
To support this flow, we enhanced existing DTOs:
- **`GodCommandDTO`**: Added `UPDATE_TELEMETRY` command type.
- **`WatchtowerV2DTO`**: Added `scenario_reports` (for scenario status) and `custom_data` (for masked on-demand telemetry).

### 2.3 Technical Debt & Future Work
- **Websocket Integration**: The live websocket server integration point was not found in the provided codebase. We implemented the logic in `CommandService` and updated `scripts/mock_ws_server.py` to simulate the behavior. The actual wiring in the real simulation loop might need verification.
- **Visualization Performance**: Rendering large heatmaps (e.g., thousands of agents) in Streamlit via Plotly might be slow. Future optimization could involve server-side pre-rendering or aggregation.
- **Scenario Report Serialization**: We manually reconstruct `ScenarioReportDTO` from the dictionary received via WebSocket. Using a serialization library like `dacite` would be cleaner.

## 3. Test Evidence

The following `pytest` execution confirms that the `UPDATE_TELEMETRY` command correctly updates the `TelemetryCollector`'s subscriptions and that data harvesting works as expected.

### `tests/integration/test_telemetry_pipeline.py`

```text
tests/integration/test_telemetry_pipeline.py::TestTelemetryPipeline::test_update_telemetry_command_updates_subscriptions
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:310 Telemetry mask updated: ['econ.gdp', 'pop.count']
PASSED                                                                   [ 33%]

tests/integration/test_telemetry_pipeline.py::TestTelemetryPipeline::test_update_telemetry_command_replaces_subscriptions
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:310 Telemetry mask updated: ['new.metric']
PASSED                                                                   [ 66%]

tests/integration/test_telemetry_pipeline.py::TestTelemetryPipeline::test_update_telemetry_invalid_value_type
-------------------------------- live log call ---------------------------------
ERROR    modules.system.services.command_service:command_service.py:97 Execution failed for 47823207-a709-4be3-96e7-f167166df6b2: New value for UPDATE_TELEMETRY must be a list of strings (mask).
Traceback (most recent call last):
  File "/app/modules/system/services/command_service.py", line 86, in execute_command_batch
    self._handle_update_telemetry(cmd)
  File "/app/modules/system/services/command_service.py", line 297, in _handle_update_telemetry
    raise ValueError("New value for UPDATE_TELEMETRY must be a list of strings (mask).")
ValueError: New value for UPDATE_TELEMETRY must be a list of strings (mask).
INFO     modules.system.services.command_service:command_service.py:120 ROLLBACK_SUCCESS | Batch reversed.
PASSED                                                                   [100%]

============================== 3 passed in 0.14s ===============================
```
