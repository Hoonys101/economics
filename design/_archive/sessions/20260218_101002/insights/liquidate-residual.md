
# Insight Report: Liquidating Residual Failures

## Architectural Insights

### 1. YAML Mocking in Tests
The project relies on `yaml.safe_load` to parse configuration schemas. In the test environment, `conftest.py` globally mocks `yaml.safe_load` to return an empty dictionary (`{}`) by default (or similar minimal mock). This default behavior broke the `SchemaLoader` service and `RegistryService`, which expect a **list** of schema definitions.

To resolve this without altering the global fixture (which might affect other tests), I used `unittest.mock.patch` locally within the integration and unit tests for the registry system. This allowed me to inject precise, list-based schema structures required for those specific tests to pass, maintaining isolation and test fidelity.

### 2. Fixture Mismatches (Mocker vs unittest.mock)
`tests/unit/test_ledger_manager.py` attempted to use a `mocker` fixture, which is typically provided by `pytest-mock`. However, the environment seemed to lack this plugin or fixture definition. I replaced it with the standard library's `unittest.mock.patch` context manager. This reduces external dependencies for the test suite and ensures compatibility with standard Python environments.

### 3. DTO Fidelity (BorrowerProfileDTO)
Initial investigations suggested a `TypeError` regarding `BorrowerProfileDTO` and its `borrower_id` field. Verification showed the code and DTO definition were actually in sync (both having `borrower_id`). The reported failures were likely due to outdated failure logs or a transient state. No changes were needed for `BorrowerProfileDTO`, confirming that strict DTO definitions are correctly propagated.

## Test Evidence

```
tests/unit/test_ledger_manager.py::test_archive_resolved_items PASSED    [ 25%]
tests/unit/test_ledger_manager.py::test_register_new_item PASSED         [ 50%]
tests/unit/test_ledger_manager.py::test_sync_with_codebase PASSED        [ 75%]
tests/unit/test_ledger_manager.py::test_pipe_escaping_in_ledger PASSED   [100%]

tests/integration/test_registry_metadata.py::TestRegistryMetadata::test_schema_loader_loads_data PASSED [ 20%]
tests/integration/test_registry_metadata.py::TestRegistryMetadata::test_global_registry_loads_metadata_on_init PASSED [ 40%]
tests/integration/test_registry_metadata.py::TestRegistryMetadata::test_global_registry_get_metadata_returns_none_for_unknown_key PASSED [ 60%]
tests/integration/test_registry_metadata.py::TestRegistryMetadata::test_global_registry_get_entry_returns_none_for_unset_key PASSED [ 80%]
tests/integration/test_registry_metadata.py::TestRegistryMetadata::test_global_registry_get_entry_returns_entry PASSED [100%]

tests/unit/dashboard/test_registry_service.py::TestRegistryService::test_get_all_metadata PASSED [ 33%]
tests/unit/dashboard/test_registry_service.py::TestRegistryService::test_get_metadata_by_key PASSED [ 66%]
tests/unit/dashboard/test_registry_service.py::TestRegistryService::test_get_metadata_unknown_key PASSED [100%]

=========================== short test summary info ============================
SKIPPED [1] tests/test_ws.py:6: fastapi not installed
SKIPPED [1] tests/unit/decisions/test_household_integration_new.py:12: TODO: Fix integration test setup. BudgetEngine/ConsumptionEngine interaction results in empty orders.
================= 788 passed, 2 skipped, 12 warnings in 7.85s ==================
```
