# TD-122: Test Directory Organization Insight Report

## 1. Context & Motivation (TD-122)
*   **Original State**: The `tests/` directory was cluttered with a mix of unit tests, integration scenarios, and ad-hoc verification scripts (`tests/scenarios`, `tests/modules`, `tests/decisions`).
*   **Issue**: This lack of structure made it difficult to:
    1.  Distinguish between fast-running unit tests and slow-running integration/stress tests.
    2.  Locate relevant tests for specific components.
    3.  Maintain clear boundaries between test types.
*   **Goal**: Reorganize the directory into `unit`, `integration`, and `stress` subdirectories as mandated by TD-122.

## 2. Changes Implemented
The `tests/` directory has been restructured into three primary categories:

### A. `tests/unit`
*   **Purpose**: Isolated tests for individual components (Agents, Managers, Engines).
*   **Content**:
    *   Moved `tests/decisions/*.py` to `tests/unit/decisions/`.
    *   Moved `tests/modules/government/components/*.py` to `tests/unit/modules/government/components/`.
    *   Moved `tests/factories.py` to `tests/unit/factories.py` (as it is primarily used by unit tests).
    *   Consolidated existing unit tests.

### B. `tests/integration`
*   **Purpose**: Tests verifying interactions between multiple systems, scenarios, and end-to-end flows.
*   **Content**:
    *   Moved `tests/scenarios` (excluding stress tests) to `tests/integration/scenarios`. This includes diagnosis, verification, and phase-specific integration tests.
    *   Moved `tests/goldens` to `tests/integration/goldens`. Goldens represent full system snapshots and are inherently integration artifacts, though utilized by some unit tests for convenience.

### C. `tests/stress`
*   **Purpose**: High-load or boundary-condition tests intended to break the system or verify resilience.
*   **Content**:
    *   Moved `tests/scenarios/phase28/test_stress_scenarios.py` to `tests/stress/`.

## 3. Technical Challenges & Resolutions

### Shared Resources (Goldens & Factories)
*   **Challenge**: `tests/goldens` and `tests/factories.py` were located at the root and used by both unit and integration tests.
*   **Resolution**:
    *   Moved `goldens` to `tests/integration/goldens` as they conceptually belong to integration state. Updated `tests/conftest.py` and `tests/unit/api/test_dashboard_api.py` to reference the new path.
    *   Moved `factories.py` to `tests/unit/factories.py` and updated imports in `tests/unit/test_household_decision_engine_new.py`.

### Relative Imports
*   **Challenge**: Tests in `tests/decisions` used relative imports for fixtures.
*   **Resolution**: Updated imports to use full package paths (e.g., `tests.unit.decisions.legacy_household_engine_fixture`) to ensure stability regardless of test runner invocation context.

## 4. Verification
*   **File Structure**: Verified via `find` command that all files reside in the target directories (`unit`, `integration`, `stress`) and no legacy directories (`scenarios`, `decisions`, `modules`) remain at the root.
*   **Imports**: Verified that modified tests reference their dependencies correctly.

## 5. Conclusion
The new structure aligns with the project's architectural maturity goals. It separates concerns, simplifies test discovery, and paves the way for optimized CI/CD pipelines (e.g., running unit tests on every commit, integration/stress tests on nightly builds).
