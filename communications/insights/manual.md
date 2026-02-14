# Insight Report: TD-UI-DTO-PURITY

## 1. Architectural Insights
*   **DTO Purity Enforced**: The `TelemetrySnapshotDTO` in `simulation/dtos/telemetry.py` has been refactored from a `TypedDict` to a Pydantic `BaseModel`. This ensures that telemetry data flowing out of the simulation core is strongly typed and validated at the boundary.
*   **Serialization Strategy**: `SimulationServer` in `modules/system/server.py` was updated to handle `BaseModel` objects by converting them to dictionaries using `model_dump(mode='json')` before JSON serialization. It also supports `dataclasses` (legacy) and `dicts` (fallback) to maintain backward compatibility and robustness.
*   **Bug Fix**: `SimulationServer`'s tick checking logic (`current_tick > last_tick`) relied on `getattr(snapshot, 'tick', -1)`. This method fails for dictionaries (returning -1 always). By switching to `BaseModel`, `getattr` works correctly. Additionally, the server logic was patched to support dictionary access (`snapshot.get('tick')`) if needed in the future.

## 2. Test Evidence
```
tests/unit/test_telemetry_purity.py::TestTelemetryPurity::test_telemetry_collector_returns_pydantic_model PASSED [ 25%]
tests/unit/test_telemetry_purity.py::TestTelemetryPurity::test_simulation_server_serializes_pydantic_model PASSED [ 50%]
tests/integration/test_server_integration.py::test_command_injection PASSED [ 75%]
tests/integration/test_server_integration.py::test_telemetry_broadcast PASSED [100%]

============================== 4 passed in 2.92s ===============================
```
