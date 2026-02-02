# Fix Crisis Monitor OSError and Test Suite Instability

## Phenomenon
System tests were failing with `OSError: [Errno 22] Invalid argument` in `modules/analysis/crisis_monitor.py`. Additionally, `tests/integration/test_tick_normalization.py` failed with `AttributeError` during setup.

## Cause
1.  **Mock Structure Mismatch**: The `CrisisMonitor` initializes its log filename using `run_id`. This `run_id` is obtained from `simulation.repository.runs.save_simulation_run()`. In several test fixtures (e.g., `tests/system/test_engine.py`), the mock was set up as `repo.save_simulation_run.return_value = 1`. However, the code calls `repo.runs.save_simulation_run`. Since `repo` is a `MagicMock`, accessing `repo.runs` creates a new child `MagicMock`, and accessing `save_simulation_run` on that creates another new `MagicMock`. Consequently, `run_id` became a `MagicMock` object. When formatted into the filename string (e.g., `reports/crisis_monitor_<MagicMock...>.csv`), it created a filename containing characters or length that triggered `OSError` (likely `<` and `>` on some filesystems, or just unexpected type behavior).
2.  **Outdated Test Patches**: `tests/integration/test_tick_normalization.py` was trying to patch `simulation.orchestration.tick_orchestrator.Phase4_Lifecycle`. This class was removed/renamed in recent refactoring (replaced by `Phase_Bankruptcy`, `Phase_SystemicLiquidation`, `Phase_Consumption`), causing `AttributeError` during test setup.

## Solution
1.  **Correct Mocking**: Updated test fixtures to mock the correct path: `repo.runs.save_simulation_run.return_value = 1`. This ensures `run_id` is an integer, producing a valid filename.
2.  **Update Test Phases**: Refactored `test_tick_normalization.py` to patch the actual phases currently used in `TickOrchestrator`.

## Lesson Learned
*   **Mock Fidelity**: When mocking complex dependencies, verify the exact attribute path used by the code under test. Mismatched paths lead to silent failures or confusing type errors when `MagicMock` auto-creation kicks in.
*   **Test Maintenance**: Refactoring core orchestration logic (like renaming phases) requires a comprehensive search for tests that manually patch these classes, as they won't be caught by static analysis if accessed via string paths in `patch()`.
