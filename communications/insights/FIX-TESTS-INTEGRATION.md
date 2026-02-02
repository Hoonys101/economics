# Technical Debt Report: Integration Test Repair

## Context
Following the merge of `restore-integration-tests` and `jules-fix-corporate-tests`, the test suite exhibited widespread failures. This report documents the technical debt uncovered during the repair process.

## Phenomenon
1.  **Systemic Setup Failures**: `OSError` in `CrisisMonitor` due to `MagicMock` leakage into filenames.
2.  **Refactoring Lag**: Integration tests failed to reflect the `_econ_state` / `_bio_state` decomposition of agents, accessing legacy flat attributes on Mocks.
3.  **DTO Mismatches**: Tests instantiated DTOs with outdated signatures (`HousingMarketSnapshotDTO`) or called methods with legacy arguments (`make_decision`).
4.  **Mock Fragility**: `Phase4_Lifecycle` renaming caused immediate test breakage where patch targets were hardcoded string paths.

## Cause
*   **Mock Abuse**: The `mock_repository` fixture mocked `repo.save_simulation_run` but the code called `repo.runs.save_simulation_run`, leading to a Mock object propagating into file system operations.
*   **Partial Refactoring**: Core agents were refactored (Stage B), but the corresponding mock factories in integration tests were not updated synchronously.
*   **Lack of Typed Test Helpers**: Tests constructed raw DTOs manually instead of using updated factories, making them brittle to signature changes.

## Solution
*   **Robust Mocking**: Updated `test_engine.py` to mock the correct method chain for `repo.runs.save_simulation_run`.
*   **Mock Refactor**: Updated `Mock(spec=Household)` usage to explicitly initialize nested state DTOs (`_econ_state`, `_bio_state`).
*   **DTO Standardization**: Updated all `make_decision` calls to use `DecisionInputDTO` and fixed DTO constructors in tests.
*   **Patch Correction**: Renamed `Phase4_Lifecycle` to `Phase_Bankruptcy` in test patches.

## Lessons Learned
*   **Mock State, Not Just Interface**: When refactoring stateful objects (like Agents), mocks must replicate the new state structure (nested DTOs) if the system under test accesses it directly.
*   **Use Factories**: Test data should be generated via factories that are updated centrally, rather than instantiated inline in every test.
*   **Verify Mocks**: Mocks returning Mocks (recursive mocking) can lead to silent failures or weird errors (like the filename issue). Explicitly setting return values (e.g., `return_value=1`) prevents this.
