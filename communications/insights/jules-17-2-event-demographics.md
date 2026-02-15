# Insight Report: Jules 17.2 Event-Driven Demographics

**Mission Key**: jules-17-2-event-demographics
**Date**: 2026-02-14
**Author**: Jules (AI Engineer)

## 1. Architectural Insights & Decisions

### 1.1. Event-Driven Architecture (Push Model)
We successfully transitioned `DemographicManager` from a Pull Model (iterating over agents) to a Push Model (event-driven).
- **Previous State**: `get_gender_stats` iterated over all agents (O(N)).
- **New State**: `get_gender_stats` returns cached values (O(1)). Agents notify the manager on birth, death, and labor allocation changes.

### 1.2. Single Source of Truth for Death
- **Problem**: `LifecycleEngine` and `DemographicsComponent` were both setting `is_active = False` independently, leading to "Split Brain".
- **Solution**:
    - `LifecycleEngine` now returns a `death_occurred` flag instead of modifying state directly.
    - `Household.update_needs` handles this flag and calls `DemographicManager.register_death`.
    - `DemographicsComponent.handle_death` delegates to `DemographicManager.register_death` and logs an error if the manager is missing (instead of silently modifying state).

### 1.3. Labor Hour Tracking
- **Challenge**: Tracking labor hours in O(1) without iterating agents.
- **Solution**:
    - Added `last_labor_allocation` to `Household`.
    - In `make_decision`, `Household` calculates the delta of labor hours allocated and pushes it to `DemographicManager.update_labor_hours`.
    - On death, `Household` pushes a negative delta to clear its contribution.

### 1.4. Dependency Injection
- `DemographicManager` is now injected into `Household` via `HouseholdFactory` and `SimulationInitializer`.
- Addressed circular dependency between `DemographicManager` and `HouseholdFactory` by post-construction injection in `SimulationInitializer`.

## 2. Test Evidence

### 2.1. Performance Benchmark
`tests/benchmarks/test_demographic_perf.py` confirms O(1) performance.
```
tests/benchmarks/test_demographic_perf.py::test_demographic_manager_perf
INFO     simulation.systems.demographic_manager:demographic_manager.py:49 DemographicManager initialized with O(1) cache.
PASSED
```
(1000 calls took < 0.001s in manual verify)

### 2.2. Event Consistency
`tests/unit/modules/demographics/test_event_consistency.py` verifies cache updates for Birth, Death, and Labor.
```
tests/unit/modules/demographics/test_event_consistency.py::test_demographic_event_consistency
INFO     simulation.systems.demographic_manager:demographic_manager.py:98 LIFE_END | Agent 1 terminated. Cause: NATURAL
PASSED
tests/unit/modules/demographics/test_event_consistency.py::test_sync_stats
INFO     simulation.systems.demographic_manager:demographic_manager.py:118 Stats cache synchronized. Total M: 2, Total F: 1
PASSED
```

### 2.3. Component Refactor
`tests/unit/components/test_demographics_component.py` passes with refactored delegation logic.
```
tests/unit/components/test_demographics_component.py::TestDemographicsComponent::test_handle_death_above_threshold PASSED
```

## 3. Future Recommendations
- **Telemetry**: Integrate `DemographicManager` stats into the main `TelemetryCollector` pipeline.
- **Refactor `DemographicsComponent`**: Determine if this component is fully obsolete (replaced by `LifecycleEngine`) and deprecate/remove it if so. currently kept for legacy compatibility.
