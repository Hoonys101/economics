# Mission Guide: Watchtower Observability Recovery (TD-263)

## 1. Context & Phenomenon
The Watchtower dashboard frequently reports as "Offline" despite the server process running. During startup, the simulation builder sometimes hangs or crashes due to database locking conflicts (`sqlite3.OperationalError: database is locked`). This prevents the WebSocket from establishing a stable connection.

## 2. Technical Analysis
- **Locking Conflict**: Multiple processes (or multiple async tasks inside Uvicorn) may be attempting to initialize the `SimRepository` or write to the snapshot table simultaneously.
- **Async Collisions**: The `SimulationInitializer` runs synchronous DB operations inside an async lifespan context. If uvicorn attempts to restart or scale, locks collide.
- **WAL Mode**: While WAL mode is enabled, SQLite still requires application-level coordination for schema changes or heavy write bursts during Genesis.

## 3. Targeted Fixes
### A. Application-Level Lock (File-Based)
Implement a directory-level lock (e.g., `simulation.lock`) using `fcntl` (or a cross-platform equivalent) to ensure only one `Simulation` instance can write to the database during a session.

### B. Graceful Shutdown Protocol
Ensure that when the server receives a SIGINT/SIGTERM, it calls `sim.finalize_simulation()` which MUST safely close DB connections and release file locks.

### C. Socket Stability
Verify that `DashboardService.get_snapshot()` is not being called before the simulation is fully initialized. Use a "Ready" flag in the lifespan.

## 4. Instructions for Jules
1.  **Modify `simulation/initialization/initializer.py`**: Add logic to check for/create a file lock.
2.  **Optimize `simulation/db/repository.py`**: Tighten timeout settings and ensure `PRAGMA journal_mode=WAL` is explicitly set on every connection.
3.  **Update `server.py`**: Add the `Ready` flag check in the WebSocket endpoint.
4.  **Verification**: Start the server and ensure the Dashboard (port 8000/ws) stays "Online" for at least 100 ticks without "Database is locked" errors.

🛡️ [ARCHITECTURAL GUARDRAILS]
1. Zero-Sum Integrity: No magic money creation/leaks.
2. Protocol Purity: Use `@runtime_checkable` Protocols.
3. DTO Purity: Use typed DTOs for snapshots.
