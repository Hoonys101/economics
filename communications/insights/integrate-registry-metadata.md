# Insight Report: GlobalRegistry Metadata Integration

## Executive Summary
This report details the successful integration of a UI metadata layer into the `GlobalRegistry`. This enhancement enables the simulation engine to serve metadata (e.g., widget type, min/max values, labels) directly to the frontend, facilitating dynamic control generation (UI-02). The changes enforce architectural purity by moving schema definitions to shared DTOs and centralizing schema loading logic within the system module.

## Architectural Decisions

### 1. Unified Metadata Source
- **Decision:** Metadata schema is defined in `config/domains/registry_schema.yaml` and loaded by both backend (`GlobalRegistry`) and frontend (`RegistryService`) via a shared `SchemaLoader`.
- **Rationale:** Ensures consistency between backend constraints and frontend validation. Allows the backend to potentially validate inputs against metadata in the future.

### 2. DTO Refactoring
- **Decision:** Moved `ParameterSchemaDTO` from `dashboard/dtos.py` to `simulation/dtos/registry_dtos.py`.
- **Rationale:** `simulation/dtos` is a lower-level shared module accessible by both `modules/system` (backend) and `dashboard` (frontend). This resolves dependency inversion issues where the backend would depend on frontend DTOs.

### 3. GlobalRegistry Enhancement
- **Decision:** Extended `IGlobalRegistry` and `GlobalRegistry` with `get_metadata(key)` and `get_entry(key)`.
- **Rationale:**
    - `get_metadata(key)` allows consumers to retrieve UI/Validation constraints for any parameter.
    - `get_entry(key)` exposes the full `RegistryEntry` (value, origin, lock status), which is crucial for the "God Mode" UI to display lock indicators and handle permissions correctly.

### 4. SchemaLoader Centralization
- **Decision:** Moved `SchemaLoader` from `dashboard/services` to `modules/system/services`.
- **Rationale:** Schema loading is a core system function required by `GlobalRegistry` on startup. Placing it in `modules/system/services` aligns with the domain model.

## Technical Debt & Future Work

- **Telemetry Integration:** Currently, `TelemetryCollector` only collects *values*. To fully leverage "God Mode" (lock status), telemetry should be enhanced to optionally transmit full `RegistryEntry` objects or a separate metadata channel should be established. For now, the dashboard may need to query `GlobalRegistry` via a direct service call or assume lock state based on other signals.
- **Validation Enforcement:** `GlobalRegistry.set()` does not yet strictly enforce `min_value`/`max_value` from metadata. This logic should be added to prevent invalid state injections.
- **Circular Imports:** The refactoring highlighted circular dependency risks between `modules/system/api.py` and `simulation/dtos`. Using `if TYPE_CHECKING:` guards resolved this, but careful dependency management is required going forward.

## [Test Evidence]

### Test Execution Log
```
$ python3 -m pytest tests/integration/test_registry_metadata.py

tests/integration/test_registry_metadata.py::TestRegistryMetadata::test_schema_loader_loads_data PASSED [ 20%]
tests/integration/test_registry_metadata.py::TestRegistryMetadata::test_global_registry_loads_metadata_on_init PASSED [ 40%]
tests/integration/test_registry_metadata.py::TestRegistryMetadata::test_global_registry_get_metadata_returns_none_for_unknown_key PASSED [ 60%]
tests/integration/test_registry_metadata.py::TestRegistryMetadata::test_global_registry_get_entry_returns_none_for_unset_key PASSED [ 80%]
tests/integration/test_registry_metadata.py::TestRegistryMetadata::test_global_registry_get_entry_returns_entry PASSED [100%]

============================== 5 passed in 0.17s ===============================
```
