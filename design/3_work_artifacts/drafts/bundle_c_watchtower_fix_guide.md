# Integrated Mission Guide: Watchtower Observability Recovery (TD-263)

## 1. Objective
Restore full real-time observability to the Watchtower Dashboard. Resolve the "WebSocket Connection Failure" and underlying server/database synchronization issues.

## 2. Current Context (Forensics)
- **Problem**: Port 8000 is in `TIME_WAIT`. Server process (PID 23960) exists but is non-responsive.
- **Fail Pattern**: Restarting `server.py` yields `closed database` or `database is locked`.
- **Cause Hypothesis**: 
    1. A zombie Python process is holding `simulation_data.db` lock.
    2. `SimulationRepository.clear_all_data()` (called by `simulation_builder.py`) is conflicting with asynchronous WebSocket polls.
    3. `TIME_WAIT` status suggests a socket leak or improper shutdown of previous connections.

## 3. Implementation Roadmap

### Phase 1: Process & Socket Cleanup
- Kill all rogue python processes except the orchestrator.
- Implement a robust `shutdown` signal handler in `server.py` that explicitly closes the `DashboardService -> Simulation -> SimulationRepository` chain.

### Phase 2: Database Suture
- Modify `simulation_builder.py` to check for an existing simulation instance/lock before calling `clear_all_data()`.
- Ensure `SimulationRepository` uses `detect_types` and proper isolation levels for concurrent read (WebSocket) / write (Simulation) access.

### Phase 3: WebSocket Handshake Hardening
- Update `useWatchtowerStore.ts` to log specific handshake error codes.
- Ensure `server.py` handles `WebSocketDisconnect` cleanly even if the simulation is paused.

## 4. Verification
- `netstat -ano | findstr :8000`: Must show `LISTENING`.
- Open Browser to `http://localhost:8000/`: Must return `{"status": "Watchtower Server Running"}`.
- Dashboard UI: Connection indicator must be Green.
