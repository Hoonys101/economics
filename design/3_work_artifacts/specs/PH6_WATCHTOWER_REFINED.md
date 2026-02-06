# SPEC: Watchtower HUD & Observability (Track 1)

## 1. Objective
Finalize the real-time observability layer by enhancing the data aggregation logic to use moving averages for key stability metrics and implementing the missing demographic metrics.

## 2. Architectural Solution

### 2.1. Time-Series Metrics (SMA & Growth)
- **Core Logic**: `simulation.diagnostics.tracker.py` will handle time-series state using `deque` (window=50).
- **DashboardService**: Acts as a stateless transformer, injecting averaged values into `WatchtowerSnapshotDTO`.

### 2.2. Demographic Metrics (Birth Rate)
- **Core Logic**: `AgentRepository` will implement `get_birth_counts(start_tick, end_tick)` to mirror `get_attrition_counts`.
- **Integration**: `DashboardService` will bridge these counts to `PopulationMetricsDTO.birth`.

## 3. Implementation Checklist
- [ ] Add `gdp_history`, `cpi_history`, `m2_leak_history` to `Tracker`.
- [ ] Implement SMA calculation in `Tracker.track_indicators`.
- [ ] Add `gdp_growth` field to `MacroDTO`.
- [ ] Update `DashboardService.get_snapshot` to use smoothed values.
- [ ] Implement `AgentRepository.get_birth_counts`.
- [ ] Hook birth rate into `PopulationMetricsDTO`.

## 4. Verification
- `pytest tests/unit/test_tracker.py`
- Verify WebSocket `/ws/live` serves non-zero birth rates.
