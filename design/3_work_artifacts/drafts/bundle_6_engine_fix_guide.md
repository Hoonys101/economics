# Mission Guide: Phase 6 Engine Hardening & Architectural Cleanup

## 1. Objectives
- **[BUG] Fix Tick 2 Crash**: Resolve the `TypeError: 'float' object is not subscriptable` occurring in `FinanceDepartment.record_expense`.
- **TD-125 (DTO Standardization)**: Refactor `simulation/dtos/watchtower.py` and `DashboardService` to use a flattened, production-ready structure.
- **TD-015 (Centralized Metrics)**: Centralize Gini, Social Cohesion, and GDP calculation into `EconomicIndicatorTracker`.

## 2. Context & Root Cause
### The Tick 2 Crash
- **Location**: `simulation/orchestration/phases/post_sequence.py:L117-118`
- **Error**: `expenses_this_tick` and `revenue_this_tick` are being reset to `0.0` (float) instead of the required multi-currency dictionary `{DEFAULT_CURRENCY: 0.0}`.
- **Impact**: `FinanceDepartment.record_expense` fails on Tick 2 when attempting to access the dictionary.

### Architectural Alignment
- **Golden Sample**: `design/3_work_artifacts/specs/golden_samples/watchtower_full_mock_v2.json`
- **DTO Spec**: `simulation/dtos/watchtower.py` should be the Single Source of Truth for the dashboard contract.

## 3. Implementation roadmap

### Phase 1: Emergency Bug Fix
- **Modify**: `simulation/orchestration/phases/post_sequence.py`
- **Change**: 
    - Aggregate/sum the current `expenses_this_tick` (dict) into a float for `last_daily_expenses`.
    - Reset `expenses_this_tick` and `revenue_this_tick` to `{DEFAULT_CURRENCY: 0.0}`.
- **Verify**: Tick 2 of `scenarios/scenario_stress_100.py` passes.

### Phase 1.5: Multi-Currency Compatibility (MAManager)
- **Modify**: `simulation/systems/ma_manager.py:L91`
- **Error**: `TypeError: '>' not supported between instances of 'dict' and 'int'`
- **Fix**: Update the condition to check for a specific currency in `firm.finance.current_profit`:
  ```python
  if firm_balance > avg_assets * 1.5 and firm.finance.current_profit.get(DEFAULT_CURRENCY, 0) > 0:
  ```

### Phase 2: DTO & Metric Centralization (TD-125, TD-015)
- **Merge First**: Ensure `td-125` is merged into `main` before refactoring.
- **Modify**: `simulation/metrics/economic_tracker.py`
    - Implement `calculate_gini()`.
    - Track "Social Cohesion" (can proxy with average approval for now).
- **Modify**: `simulation/orchestration/dashboard_service.py`
    - Update assembly logic to use the new centralized metrics.
    - Ensure `TheWatchtowerSnapshotDTO` is fully populated.
    - **Hook**: Re-integrate the `PersistenceBridge` call:
      ```python
      from simulation.orchestration.persistence_bridge import PersistenceBridge
      # In __init__: self.persistence = PersistenceBridge(simulation)
      # In get_snapshot: self.persistence.save_snapshot(snapshot)
      ```

## 4. Verification
1. **Run Stress Test**: `python scenarios/scenario_stress_100.py`.
2. **Success Criteria**:
    - Achievement of 100 ticks without crash.
    - Observation of the **0.002% Ghost Household leak** (baseline establish).
    - Snapshots correctly saved to `reports/snapshots/` by the `PersistenceBridge`.

---
*Orchestrated by Antigravity*
