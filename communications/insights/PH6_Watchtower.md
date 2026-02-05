# PH6 Watchtower Implementation Insights

## Technical Debt & Observations

1.  **M2 Leak Calculation Integrity**:
    - The `TickOrchestrator` performs an M2 integrity check using `baseline_money_supply` (set at Tick 0) and `government.get_monetary_delta()`.
    - However, `MonetaryLedger.get_monetary_delta()` returns the delta for the *current tick*, not cumulative. Unless `baseline_money_supply` is updated or `get_monetary_delta` behaves differently than analyzed, the orchestration check might be flawed.
    - In `DashboardService`, `m2_leak` is calculated as: `Current M2 - (Baseline M2 + Cumulative Issued - Cumulative Destroyed)`. This assumes `Baseline M2` is static. This logic should be centralized (e.g., in `IntegritySystem`) to avoid divergence between the Orchestrator check and the Dashboard.

2.  **Metric Source of Truth**:
    - Macro metrics (Inflation, Gini) are accessed via `Government.sensory_data`, which receives them from `SensorySystem` (injected via `TickOrchestrator`).
    - `EconomicIndicatorTracker` also calculates metrics but `DashboardService` prioritizes `Government` sensory data for consistency with agent behavior.
    - This dual-source potential (Tracker vs Gov Sensory) could lead to discrepancies if not synchronized perfectly.

3.  **Performance Tracking**:
    - FPS is currently calculated in `DashboardService` based on poll intervals. The `Simulation` engine does not natively expose real-time performance metrics (FPS, tick duration). This should be moved to the engine level for accuracy.

4.  **GDP Growth Calculation**:
    - `DashboardService` calculates GDP growth using `government.gdp_history`. This is a derived metric that could be standardized in `EconomicIndicatorTracker`.

## Implementation Details

- **Server Architecture**: `server.py` uses `FastAPI` with a background `asyncio` task running `sim.run_tick()` in a thread pool (`asyncio.to_thread`). This prevents the heavy simulation loop from blocking the WebSocket heartbeat.
- **Throttling**: The WebSocket endpoint pushes updates at a maximum of 1Hz to comply with the contract, regardless of the simulation speed.
- **DTO**: `DashboardSnapshotDTO` strictly follows the `PH6_WATCHTOWER_CONTRACT.md`.
