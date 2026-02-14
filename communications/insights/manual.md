# Insight Report: Telemetry DTO Fixes

## Architectural Insights
The transition of `TelemetrySnapshotDTO` from a raw dictionary to a Pydantic `BaseModel` improves type safety and validation at the system boundary. This change requires all consumers of the DTO, particularly test suites, to use attribute access (e.g., `snapshot.tick`) instead of dictionary subscription (e.g., `snapshot["tick"]`). The internal `data` field remains a dictionary, preserving flexibility for dynamic telemetry keys.

We also updated `requirements.txt` to include `pydantic>=2.0.0` as a core dependency.

## Test Evidence
All relevant tests in `tests/unit/modules/system/test_telemetry.py`, `tests/unit/modules/system/test_telemetry_robustness.py`, and `tests/integration/test_telemetry_pipeline.py` are now passing.

```
tests/unit/modules/system/test_telemetry.py::test_subscribe_and_harvest_valid_path PASSED [  7%]
tests/unit/modules/system/test_telemetry.py::test_subscribe_invalid_path PASSED [ 15%]
tests/unit/modules/system/test_telemetry.py::test_multi_frequency PASSED [ 23%]
tests/unit/modules/system/test_telemetry.py::test_unsubscribe PASSED     [ 30%]
tests/unit/modules/system/test_telemetry.py::test_runtime_error_handling PASSED [ 38%]
tests/unit/modules/system/test_telemetry.py::test_deep_nested_path PASSED [ 46%]
tests/unit/modules/system/test_telemetry.py::test_root_object_path PASSED [ 53%]
tests/unit/modules/system/test_telemetry.py::test_subscribe_pre_validation PASSED [ 61%]
tests/unit/modules/system/test_telemetry_robustness.py::TestTelemetryRobustness::test_flat_key_resolution PASSED [ 69%]
tests/unit/modules/system/test_telemetry_robustness.py::TestTelemetryRobustness::test_mixed_resolution PASSED [ 76%]
tests/integration/test_telemetry_pipeline.py::TestTelemetryPipeline::test_update_telemetry_command_updates_subscriptions PASSED [ 84%]
tests/integration/test_telemetry_pipeline.py::TestTelemetryPipeline::test_update_telemetry_command_replaces_subscriptions PASSED [ 92%]
tests/integration/test_telemetry_pipeline.py::TestTelemetryPipeline::test_update_telemetry_invalid_value_type PASSED [100%]
```
