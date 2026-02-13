# Insight Report: Fix Import Error & Simulation Loop

## Architectural Insights
- **Circular Dependency Resolved:** The `MarketSnapshotDTO` was originally defined in `simulation/api.py`, which caused circular dependencies when low-level modules like `finance` or `system` tried to import it. It has been moved to `modules/system/api.py`, making it a foundational DTO available to the entire system without upstream dependencies.
- **DTO Structure Alignment:** The `MarketSnapshotDTO` structure in `simulation/api.py` was outdated (containing only order book data) compared to what the `MarketSnapshotFactory` was producing (signals, housing, labor, loan data). The definition in `modules/system/api.py` now matches the factory's output, ensuring type consistency.
- **Simulation Loop Fix:** The `Simulation.run_tick()` method was missing a call to `self._process_commands()`. This meant that external commands (like `PAUSE` or `SET_PARAM`) injected into the queue were never processed, causing integration tests to fail on logic assertions even after the import errors were fixed. This has been rectified.

## Test Evidence
The following output demonstrates that `tests/integration/test_cockpit_integration.py` now passes successfully:

```
tests/integration/test_cockpit_integration.py::test_simulation_processes_pause_resume
-------------------------------- live log call ---------------------------------
INFO     simulation.engine:engine.py:126 System Pause State set to True
INFO     simulation.engine:engine.py:126 System Pause State set to False
PASSED                                                                   [ 33%]
tests/integration/test_cockpit_integration.py::test_simulation_processes_set_base_rate PASSED [ 66%]
tests/integration/test_cockpit_integration.py::test_simulation_processes_set_tax_rate PASSED [100%]

=============================== warnings summary ===============================
...
======================== 3 passed, 2 warnings in 0.21s =========================
```
