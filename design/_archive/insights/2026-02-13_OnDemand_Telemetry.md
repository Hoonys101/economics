# Insight Report: On-Demand Telemetry Engine (DATA-02)

**Mission Key**: DATA-02
**Status**: Completed
**Date**: 2024-05-24

---

## 1. Technical Insights & Architectural Decisions

### 1.1 DTO Placement (`simulation/dtos` vs `core/dtos`)
The specification requested `core/dtos/telemetry.py`. However, the `core` directory does not exist in the current repository structure. To maintain consistency with existing patterns, `TelemetrySnapshotDTO` was placed in `simulation/dtos/telemetry.py`. This ensures it resides alongside other DTO definitions like `HouseholdConfigDTO` and `MarketSnapshotDTO`.

### 1.2 Path Resolution & Pre-Validation Strategy
The `GlobalRegistry` interface (`IGlobalRegistry`) only supports simple key-based retrieval (`get(key)`). It does not natively support dot-notation traversal or path parsing.
- **Decision**: Implemented `_resolve_path` and `_create_accessor` logic within `TelemetryCollector`.
- **Pre-Validation**: As requested, path validation occurs immediately during `subscribe()`. If a path cannot be resolved at subscription time (e.g., the target object or attribute does not exist), it is marked as "invalid" and stored in `_invalid_paths`.
- **Runtime Handling**: `harvest()` attempts to use the pre-resolved accessor. If a runtime error occurs (e.g., a dynamic attribute was removed), it is caught and reported in the `errors` list of the snapshot. This ensures the simulation does not crash due to telemetry failures.

### 1.3 Strict Subscription Policy
The pre-validation mechanism is strict: the path *must* exist at the moment of subscription. This assumes that all relevant simulation modules and objects are initialized before telemetry subscriptions are made. If subscriptions happen too early (before initialization), they will fail. This dependency on initialization order is a potential constraint but aligns with the "reduce runtime overhead" goal.

---

## 2. Test Evidence

The following `pytest` execution logs confirm the successful implementation of `TelemetryCollector`, covering happy paths, error handling, multi-frequency sampling, and deep nesting.

**Command**: `pytest tests/unit/modules/system/test_telemetry.py`

```text
tests/unit/modules/system/test_telemetry.py::test_subscribe_and_harvest_valid_path PASSED [ 12%]
tests/unit/modules/system/test_telemetry.py::test_subscribe_invalid_path PASSED [ 25%]
tests/unit/modules/system/test_telemetry.py::test_multi_frequency PASSED [ 37%]
tests/unit/modules/system/test_telemetry.py::test_unsubscribe PASSED     [ 50%]
tests/unit/modules/system/test_telemetry.py::test_runtime_error_handling PASSED [ 62%]
tests/unit/modules/system/test_telemetry.py::test_deep_nested_path PASSED [ 75%]
tests/unit/modules/system/test_telemetry.py::test_root_object_path PASSED [ 87%]
tests/unit/modules/system/test_telemetry.py::test_subscribe_pre_validation PASSED [100%]

============================== 8 passed in 0.18s ===============================
```
