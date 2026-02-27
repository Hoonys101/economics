# MISSION: Track C - Simulation Stability & Performance Profiling
# Role: Jules (System Reliability Engineer)

## Objective
Detect and eliminate deadlocks and resource leaks in the simulation kernel, ensuring high-performance batch execution.

## Scope
- `modules/system/config_api.py`
- `tests/conftest.py`
- `simulation/orchestration/tick_orchestrator.py`
- Core Registry APIs (`modules/system/registry.py`)

## Specific Tasks
1. **Deadlock Free Init**: Refactor `ConfigProxy` to ensure lazy loading never triggers re-entry or recursive locking.
2. **Collection Optimization**: Reduce `pytest --collect-only` time by trimming redundant imports in `conftest.py`.
3. **Memory Audit**: Profile memory usage over a 2000-tick run to detect leak patterns in `EconomicMetricsService`.
4. **PID Locking**: Finalize `PlatformLockManager` hardening to prevent stale locks in local development environments.

## Success Criteria
- Full test collection in < 2 seconds.
- 2000-tick run completes without OOM or manual termination.
