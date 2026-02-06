# Technical Insight: Watchtower Connectivity & DB Lock Fixes

## 1. Problem Phenomenon
The Watchtower dashboard frequently reports "Offline" status even when the server process is running. Users report hanging or crashing during the simulation startup phase, specifically accompanied by `sqlite3.OperationalError: database is locked` exceptions. This instability prevents the WebSocket connection (port 8000/ws) from being reliably established, as the server initialization (lifespan) fails or hangs indefinitely waiting for a database lock.

## 2. Root Cause Analysis
The issue stems from three primary factors:
1.  **Concurrency Conflicts**: The `SimulationInitializer` performs heavy synchronous database operations (schema creation, clearing old data) within the async `lifespan` context of FastAPI/Uvicorn. If multiple processes (e.g., development reloads or accidental multiple instances) attempt this simultaneously, SQLite's file lock mechanism triggers a conflict.
2.  **Aggressive Locking Strategy**: The default SQLite settings used in `DatabaseManager` (default timeout, aggressive journaling) are insufficient for the burst write activity during Genesis (initialization).
3.  **Lack of Application-Level Coordination**: While `utils/simulation_builder.py` had some locking logic, it was not strictly enforced across all initialization paths (e.g., direct `SimulationInitializer` usage) and did not guarantee lock release on shutdown, potentially leaving stale locks.
4.  **Premature WebSocket Access**: The `server.py` WebSocket endpoint attempts to access `DashboardService` immediately upon connection. If the simulation is still initializing (which can take seconds due to DB operations), `dashboard_service` might be partially initialized or `sim` might be in an inconsistent state, causing crashes or blockages.

## 3. Solution Implementation Details
The solution addresses these issues through a multi-layered approach:

### A. Strict File-Based Locking
We implemented a robust file-based locking mechanism using `fcntl` (Unix) within `SimulationInitializer`.
-   **Lock Acquisition**: Before any database operation or simulation build begins, the system attempts to acquire an exclusive, non-blocking lock on `simulation.lock`.
-   **Lock Retention**: The file handle is attached to the `Simulation` instance (`sim._lock_file`) to ensure it remains open (and locked) for the duration of the simulation's life.
-   **Lock Release**: `Simulation.finalize_simulation` explicitly closes this file handle, ensuring the lock is released gracefully on shutdown.

### B. SQLite Optimization (WAL + Normal Sync)
We optimized `simulation/db/database.py` to better handle concurrent access:
-   **WAL Mode**: Confirmed `PRAGMA journal_mode=WAL` is set.
-   **Synchronous Mode**: Set `PRAGMA synchronous=NORMAL` to reduce fsync calls, improving write performance without significantly compromising integrity for this use case.
-   **Timeout Extension**: Increased SQLite connection timeout from 10.0s to 30.0s to allow longer wait times during heavy write bursts (like Genesis) instead of immediately failing.

### C. Server Readiness State
We introduced an explicit `is_ready` flag in `server.py`:
-   **Flag Management**: The flag is set to `True` only after `create_simulation` completes and the background loop starts.
-   **Endpoint Guard**: The WebSocket endpoint checks this flag. If the server is not ready, it defers processing, preventing premature access to the database or uninitialized simulation state.

## 4. Lessons Learned & Technical Debt
-   **Singleton Enforcement**: For file-based database applications (SQLite), strictly enforcing a singleton instance via file locking is crucial to prevent corruption and lock contention.
-   **Async/Sync Boundary**: Mixing heavy synchronous initialization logic within async frameworks (FastAPI) requires careful handling. Ideally, initialization should happen in a separate thread or process, but locking and readiness flags provide a viable mitigation.
-   **Tech Debt**: The `SimulationInitializer` is still doing too much heavy lifting (DB clearing, schema init) synchronously. Future refactoring should consider moving database setup to a dedicated migration/setup script or making it fully asynchronous to avoid blocking the main event loop during startup.

## 5. Additional Fixes (Discovered during Verification)
During verification, we identified and resolved two critical runtime errors that prevented server stability:

1.  **Missing `memory_v2` in `BaseAgent`**: The `Household` agent expected `self.memory_v2` to be initialized, but `BaseAgent` (its parent) was not storing the injected `memory_interface`. We updated `BaseAgent` to correctly assign `self.memory_v2`.
2.  **`PublicManager` Protocol Violation**: `PublicManager` implemented `IFinancialEntity.assets` incorrectly by returning a `Dict` instead of a `float` (Default Currency). This caused a `TypeError` in `SettlementSystem` during liquidation. We corrected `PublicManager` to return a float, aligning with the protocol.
3.  **Defensive Settlement Logic**: Added type checking and logging in `SettlementSystem._execute_withdrawal` to catch and handle cases where agents might return incorrect asset types, ensuring robustness.
