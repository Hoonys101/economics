# Mission Guide: The Industrial Revolution (Tracks A & B)

## 1. Objectives
- **Track A (Watchtower)**: Smooth out observability metrics and implement birth rate tracking.
- **Track B (Clean Sweep)**: Implement high-performance tech diffusion and R&D bridge.

## 2. Reference Context
- **Primary Specs**:
  - `design/3_work_artifacts/specs/PH6_WATCHTOWER_REFINED.md`
  - `design/3_work_artifacts/specs/WO-136_CLEAN_SWEEP_REFINED.md`
- **Critical Files**:
  - `simulation/diagnostics/tracker.py`
  - `simulation/systems/technology_manager.py`
  - `simulation/firms.py`

## 3. Implementation Roadmap

### Phase 1: Performance Foundation (Track B)
1. Implement `Firm.get_tech_info()` and the R&D bridge in the simulation logic.
2. Refactor `TechnologyManager` to `numpy` matrix and vectorize diffusion.
3. Run `scripts/bench_tech.py`.

### Phase 2: Observability Hardening (Track A)
1. Add SMA deques to `Tracker` and update indicator logic.
2. Implement birth counts in `AgentRepository`.
3. Update `DashboardService` to serve smoothed and complete snapshots.

## 4. Verification
- All existing tests pass.
- Benchmark targets met (<10ms for tech).
- HUD/WebSocket shows smoothed data and valid birth rates.
