# SPEC: TD-122 Test Directory Reorganization

**Objective**: Liquidate technical debt TD-122 by defining and implementing a tiered directory structure for tests, ensuring discoverability and improving project organization.

---

## 1. Problem Definition

-   **TD-122 (Test Directory Fragmentation)**: The current `tests/` directory is flat. It is difficult to distinguish between fast unit tests, slower integration tests, and full system tests. This increases maintenance overhead and developer friction when adding new tests.

## 2. Implementation Plan

### Phase 1: Directory Structure and Configuration

1.  **Create Directories**: Create the following new subdirectories within the `tests/` folder:
    -   `tests/unit/`: For tests of a single class or function in isolation. Must not have external dependencies like files, databases, or network calls. Mocks are used for all collaborators. These should be very fast.
    -   `tests/integration/`: For tests that verify the interaction between two or more components. For example, testing that a `CorporateManager`'s decision correctly creates an `Order` that a `Market` can process. These tests can use fixtures that load data (e.g., `golden_households`) but should not run a full simulation loop.
    -   `tests/system/`: For end-to-end tests. These tests typically run a full simulation for a small number of ticks to ensure all major components of the system work together correctly.

2.  **Update `pytest.ini`**: Modify the `pytest.ini` file in the project root to ensure `pytest` discovers tests in the new directories, while also maintaining discovery in the root for the transition period.

    ```ini
    [pytest]
    # Explicitly define all paths where tests can be found.
    # The root 'tests' is kept for backward compatibility during migration.
    testpaths =
        tests/unit
        tests/integration
        tests/system
        tests
    ```

### Phase 2: Migration Policy and Initial Move

1.  **Document the Policy**: Update the project's primary development guide (e.g., `CONTRIBUTING.md` or `design/2_operations/development_workflow.md`) with the new testing policy.
    -   **Policy Statement**: "All *new* tests must be placed in the appropriate `tests/unit/`, `tests/integration/`, or `tests/system/` subdirectory. Existing tests located in the `tests/` root directory are to be migrated to the new structure only when they are next modified. There will be no dedicated, large-scale effort to move all old tests at once."

2.  **Proof-of-Concept Migration**: To validate the setup, move a small number of existing tests to their new homes:
    -   Find a simple unit test (e.g., `test_some_dto.py`) and move it to `tests/unit/`.
    -   Find a test that uses a fixture like `golden_firms` (e.g., `test_corporate_manager.py`) and move it to `tests/integration/`.
    -   Find a test that runs `Simulation.run_for_n_ticks` and move it to `tests/system/`.

## 3. Verification Plan

1.  **Pytest Discovery**: Run `pytest --collect-only -q` from the project root. The output should list test files from the newly migrated locations as well as from the root `tests/` directory.
2.  **Test Count Verification**:
    -   Run `pytest` *before* the changes and record the total number of tests collected and run.
    -   Run `pytest` *after* the proof-of-concept migration.
    -   Assert that the total number of tests collected and run is identical, proving that no tests were "lost" during the move.
3.  **CI Pipeline Audit**:
    -   Manually inspect the project's CI/CD configuration file (e.g., `.github/workflows/ci.yml`, `azure-pipelines.yml`).
    -   Locate the testing step. Ensure that the command used is generic (e.g., `pytest` or `python -m pytest`) and does not contain a hardcoded path like `pytest tests/`. If it does, remove the explicit path to allow `pytest.ini` to control discovery.

## 4. Risk & Impact Audit

-   **Critical Risk**: **CI Test Blindness**. If the CI/CD script is hardcoded to run tests only in the root `tests/` folder, it will not discover any tests moved or added to the new subdirectories. This would create a silent and critical gap in test coverage.
    -   **Mitigation**: The implementation plan has two key safeguards:
        1.  Using `pytest.ini`'s `testpaths` is the canonical and most robust way to configure test discovery, making it less likely to be overridden.
        2.  The verification plan includes a **mandatory manual audit** of the CI configuration file to find and remove any such hardcoded paths.
-   **Architectural Impact**: **Positive**. This resolves TD-122 and introduces a clean, scalable, and conventional structure for tests, which will improve developer experience and the long-term maintainability of the test suite.
