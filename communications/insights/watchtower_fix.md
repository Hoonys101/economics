# Technical Insight Report: Watchtower Observability Recovery (TD-263)

## 1. Problem Phenomenon
- **Symptoms**:
    - `server.py` failed to restart with `sqlite3.OperationalError: database is locked`.
    - Port 8000 remained in `TIME_WAIT` or `LISTEN` state by "ghost" processes.
    - WebSocket connections on the dashboard would repeatedly disconnect and reconnect without clear error messages.
    - "Closed database" errors appearing in logs when the server was killed abruptly.

## 2. Root Cause Analysis
- **Zombie Processes**: Previous server instances were not shutting down cleanly, leaving Python processes active. These processes held locks on `simulation_data.db`.
- **Race Condition in Initialization**: `utils/simulation_builder.py` indiscriminately called `repository.clear_all_data()` (which performs a heavy `VACUUM` operation) upon startup. If a zombie process was holding a read lock (via WebSocket) or write lock, the new process would crash or hang.
- **Missing Application-Level Locking**: There was no mechanism to prevent multiple `server.py` instances from running simultaneously and competing for the same SQLite file.
- **SQLite Concurrency Settings**: The default SQLite connection settings were strict (default timeout) and didn't explicitly enforce `WAL` (Write-Ahead Logging) mode in the connection parameters for optimal concurrency.

## 3. Solution Implementation Details
- **Process Isolation**: Implemented a file-based lock (`simulation.lock`) using `fcntl` in `utils/simulation_builder.py`. The server now refuses to start if another instance holds the lock.
- **Database Hardening**:
    - Updated `simulation/db/database.py` to set `PRAGMA journal_mode=WAL` explicitly on connection.
    - Increased connection timeout to 10.0 seconds to tolerate transient locks.
    - Added `detect_types` for better type safety.
- **Graceful Shutdown**:
    - Added `signal` handlers (`SIGINT`, `SIGTERM`) in `server.py` to set a global `is_running` flag, allowing the simulation loop to exit cleanly.
    - Wrapped `lifespan` startup in a `try-except` block to prevent partial initialization from leaving zombie resources.
    - Ensured `sim.finalize_simulation()` is called exactly once.
- **Observability**: Updated frontend `useWatchtowerStore.ts` to log specific WebSocket close codes and reasons, aiding future debugging.

## 4. Lessons Learned & Technical Debt
- **Lesson**: SQLite `VACUUM` is a blocking operation and should be used with caution in auto-starting sequences.
- **Lesson**: For long-running async services, relying solely on `uvicorn`'s default signal handling might not be enough if background threads/tasks are heavy. Explicit cancellation logic is required.
- **Technical Debt**: The `Simulation` class "facade" pattern is slightly leaky; `server.py` interacts with `dashboard_service` which interacts with `sim`. A cleaner separation of concerns for lifecycle management (e.g., a `SimulationManager`) would be better.
