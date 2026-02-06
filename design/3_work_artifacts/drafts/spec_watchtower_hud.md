# Work Order: Watchtower HUD & Observability (Track 1)

## 1. Objective
Finalize the real-time observability layer (Phase 6) by enhancing the data aggregation logic and implementing the missing demographic metrics.

## 2. Technical Requirements

### 2.1 DashboardService (Aggregation)
- **Path**: `simulation/orchestration/dashboard_service.py`
- **Tasks**:
  - Implement 50-tick Simple Moving Average (SMA) for `gdp`, `cpi`, and `m2_leak`.
  - Ensure `IntegrityDTO.m2_leak` reflects the averaged value to avoid transient spikes.
  - Update `MacroDTO` to include `gdp_growth` relative to the previous turn.

### 2.2 Demographic Metrics (Birth Rate)
- **Path**: `simulation/systems/demographic_manager.py` (or repository)
- **Tasks**:
  - Implement birth rate tracking in the `SimulationState` or `WorldState`.
  - Hook the birth rate into `DashboardService.get_snapshot()` to populate `PopulationMetricsDTO.birth`.

### 2.3 Frontend HUD Wiring
- **Objective**: Ensure the WebSocket client correctly Map-Reduces the `WatchtowerSnapshotDTO` into the HUD UI.
- **Reference**: `PH6_THE_WATCHTOWER_PLAN.md`

## 3. Success Criteria
- WebSocket `/ws/live` serves snapshots with valid `birth` rates.
- `m2_leak` stabilizes via moving averages.
- HUD displays real-time GDP growth.
