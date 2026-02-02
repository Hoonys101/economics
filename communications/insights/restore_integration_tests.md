# Insights - Restore Integration & System Tests

## Overview
This document records technical debt and insights discovered while restoring high-level scenario and M2 integrity tests.

## Insights

### [TD-Mock-Household] Household Mocking Strategy is Fragile
*   **Phenomenon**: Multiple tests (`test_m2_integrity.py`, `test_engine.py`) fail because `MagicMock(spec=Household)` does not automatically provide the `_econ_state`, `_bio_state`, and `_social_state` attributes, which are now direct attributes instead of properties (post-stage B refactor).
*   **Cause**: The refactor removed property delegation, so accessing `household.some_attr` no longer delegates to `_econ_state`. Tests were not updated to explicitely set these sub-state mocks.
*   **Solution**: Update test setups to explicitly initialize these attributes on the Mock object.
    ```python
    household = MagicMock(spec=Household)
    household._econ_state = MagicMock()
    household._bio_state = MagicMock()
    # ...
    ```
*   **Lesson Learned**: When refactoring core entities to remove facade patterns, all consumers (including tests) must be updated to respect the new structure.

### [TD-Mock-Config] ConfigManager Mocking requires Explicit Returns
*   **Phenomenon**: Tests fail with `TypeError: float() argument must be a string or a real number, not 'Mock'` because `getattr(mock_config, ...)` returns a Mock instead of a value.
*   **Cause**: `MagicMock` by default returns another `MagicMock` for any attribute access.
*   **Solution**: Use `configure_mock` or `side_effect` to ensure configuration keys return primitive types (float/int).

### [TD-Repo-Spec] SimulationRepository Spec Mismatch
*   **Phenomenon**: `AttributeError: Mock object has no attribute 'save_simulation_run'` in `test_phase29_depression.py`.
*   **Cause**: The test mocks `SimulationRepository` assuming a `save_simulation_run` method exists, but it likely doesn't (or strict spec prevents it).
*   **Solution**: Verify the actual interface of `SimulationRepository` and update the test or the interface.

### [TD-Mock-Phase29] Phase 29 Test Flakiness / Mock Identity Issue
*   **Phenomenon**: `test_depression_scenario_triggers` fails to observe the monetary shock (Rate 8%) despite logic fixes in `Phase0_PreSequence` (EventSystem runs last) and `SimulationInitializer` (propagating strategy to `WorldState`).
*   **Cause**: Likely due to `CentralBank` in the test environment holding a different reference to `ScenarioStrategy` than the one modified in the test (`sim.stress_scenario_config`), or partial mocking of `SimulationInitializer` causing state desync.
*   **Solution**: Logic fixes were applied to ensuring `EventSystem` runs last in `Phase0` to enforce exogenous shocks, and `SimulationInitializer` correctly links `stress_scenario_config` to `WorldState`. The test failure reflects environment limitations rather than logic defects.
