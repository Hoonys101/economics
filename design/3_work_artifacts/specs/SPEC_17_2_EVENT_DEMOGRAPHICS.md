default_api:write_file{file_path:<ctrl46>modules/demographics/api.py<ctrl46>,limit:null,offset:null}
File: communications/insights/spec-17-2-event-demographics.md
```markdown
# Insight Report: Spec 17.2 Event-Driven Demographics

**Mission Key**: spec-17-2-event-demographics
**Date**: 2026-02-14
**Author**: Gemini-CLI (Scribe)

## 1. Architectural Insights & Risks

### 1.1. The "Split Brain" Death Logic
- **Issue**: Currently, `DemographicsComponent` (on the agent) and `DemographicManager` (system) both have logic to handle death. Specifically, `DemographicsComponent` can set `is_active = False` independently.
- **Risk**: If an agent "dies" silently in its component without notifying the Manager, the proposed O(1) cache will drift, leading to "Ghost Populations" in statistics.
- **Decision**: `DemographicManager` must become the **Single Source of Truth**. Components must request death via `manager.register_death(agent)`, and only the Manager should finalize the `is_active = False` state transition.

### 1.2. The Labor Hour Aggregation Dilemma
- **Issue**: The requirement for "Instant (O(1))" statistics conflicts with the dynamic nature of `labor_hours`, which changes every tick based on agent decisions (`TimeAllocation`).
- **Constraint**: Iterating `world_state` to sum labor hours is O(N) and forbidden.
- **Solution**: Adopt a **Push Model**. Agents (or their TimeComponents) must explicitly call `manager.update_labor_hours(gender, delta)` when their allocation changes. This distributes the O(N) cost across N agents' update cycles, keeping the `get_gender_stats()` query O(1).

### 1.3. Test Drift & Cache Invalidation
- **Issue**: Hundreds of existing tests likely inject agents directly into `world_state.households` without going through `DemographicManager.register_birth()`.
- **Risk**: These tests will fail or report zero stats because the cache won't be initialized.
- **Mitigation**: Introduce a `sync_stats(agents)` method on the Manager. The `conftest.py` fixtures or the Manager's `__init__` (if lazy) must trigger this sync to support legacy tests.

## 2. Technical Debt Identified

- **Service Locator Anti-Pattern**: `DemographicManager` currently accesses `simulation` via `getattr` or direct injection to find `settlement_system`. This should be replaced with strict Dependency Injection via `__init__`.
- **Ghost Configuration**: The Manager relies on `config_module` which might be stale. Migration to `GlobalRegistry` (Task 17.1) is a prerequisite for robust tuning.

## 3. Pre-Implementation Checklist

- [ ] **Refactor Component**: Remove `is_active = False` form `DemographicsComponent.handle_death`.
- [ ] **Update Protocol**: Ensure `IDemographicManager` includes `register_death` and `update_labor_hours`.
- [ ] **Test Harness**: Create a benchmark script `tests/benchmarks/test_demographic_perf.py` to verify O(1) timing.
```

File: modules/demographics/api.py
```python
"""
Demographics Module API
Defines the interface for Population Management and Statistical Aggregation.
"""
from typing import Protocol, Dict, List, Any, TypedDict, runtime_checkable
from enum import Enum

# --- Data Transfer Objects ---

class GenderStatsDTO(TypedDict):
    """
    Data Transfer Object for gender-specific statistics.
    Aggregates count and economic participation.
    """
    count: int
    total_labor_hours: float
    avg_labor_hours: float

class DemographicStatsDTO(TypedDict):
    """
    Aggregate DTO for all demographic statistics.
    """
    M: GenderStatsDTO
    F: GenderStatsDTO
    total_population: int
    active_population: int

# --- Protocols ---

@runtime_checkable
class IDemographicManager(Protocol):
    """
    Interface for the Demographic Manager.
    Acts as the Single Source of Truth for population lifecycle and statistics.
    """

    def register_birth(self, agent: Any) -> None:
        """
        Registers a new agent in the demographic system.
        Updates population caches and triggers birth events.
        
        Args:
            agent: The agent instance (must have 'gender' and 'id' attributes).
        """
        ...

    def register_death(self, agent: Any, cause: str = "NATURAL") -> None:
        """
        Processes the death of an agent.
        Updates population caches, marks agent as inactive, and triggers death events.
        
        Args:
            agent: The agent instance.
            cause: The cause of death (logging/audit).
        """
        ...

    def update_labor_hours(self, gender: str, delta: float) -> None:
        """
        Updates the running total of labor hours for a specific gender.
        Called by agents when their time allocation changes.
        
        Args:
            gender: 'M' or 'F'.
            delta: The change in labor hours (can be negative).
        """
        ...

    def get_gender_stats(self) -> DemographicStatsDTO:
        """
        Retrieves the current demographic statistics.
        MUST be O(1) - returning cached values.
        """
        ...

    def sync_stats(self, agents: List[Any]) -> None:
        """
        Force-rebuilds the internal cache from a list of agents.
        Critical for legacy tests that bypass the register_birth/death hooks.
        
        Args:
            agents: List of agent objects to aggregate.
        """
        ...
```

File: design/3_work_artifacts/specs/spec_17_2_event_demographics.md
```markdown
# Spec 17.2: Event-Driven Demographic Manager

## 1. Introduction

- **Purpose**: Optimize `DemographicManager` to strictly O(1) query time for gender statistics.
- **Scope**: `DemographicManager`, `DemographicsComponent`.
- **Key Requirement**: Eliminate O(N) iteration over `world_state.households` in `get_gender_stats()`.

## 2. High-Level Design

The system transitions from a **Pull Model** (calculating stats on demand) to a **Push/Event Model** (maintaining a running cache).

### 2.1. The "Stats Cache"
The Manager will maintain a private state:
```python
_stats_cache = {
    "M": {"count": 0, "total_labor_hours": 0.0},
    "F": {"count": 0, "total_labor_hours": 0.0}
}
```

### 2.2. Event Hooks
1.  **On Birth (`register_birth`)**: Increment `count`.
2.  **On Death (`register_death`)**: Decrement `count`.
3.  **On Allocation Change (`update_labor_hours`)**: Add `delta` to `total_labor_hours`.

## 3. Detailed Logic (Pseudo-code)

### 3.1. DemographicManager

```python
class DemographicManager(IDemographicManager):
    def __init__(self):
        self._stats_cache = {
            "M": {"count": 0, "total_labor_hours": 0.0},
            "F": {"count": 0, "total_labor_hours": 0.0}
        }

    def register_birth(self, agent: Any):
        # 1. Update Cache
        if agent.gender in self._stats_cache:
            self._stats_cache[agent.gender]["count"] += 1
        
        # 2. Log & Event
        self.logger.info(f"BIRTH registered: {agent.id}")

    def register_death(self, agent: Any, cause: str = "NATURAL"):
        if not agent.is_active:
            return # Idempotency check

        # 1. Mark Inactive (Single Source of Truth)
        agent.is_active = False

        # 2. Update Cache
        if agent.gender in self._stats_cache:
            stats = self._stats_cache[agent.gender]
            stats["count"] = max(0, stats["count"] - 1)
            # Note: Labor hours should ideally be cleared by the agent 
            # sending a negative delta before death, or we lazily accept slight drift.
            # Decision: Resetting labor is complex without tracking per-agent labor.
            # For Phase 17, we rely on the agent's component to zero out labor on death if needed.

    def update_labor_hours(self, gender: str, delta: float):
        if gender in self._stats_cache:
            self._stats_cache[gender]["total_labor_hours"] += delta

    def get_gender_stats(self) -> DemographicStatsDTO:
        # O(1) Return
        result = {}
        for g, data in self._stats_cache.items():
            avg = 0.0
            if data["count"] > 0:
                avg = data["total_labor_hours"] / data["count"]
            
            result[g] = {
                "count": data["count"],
                "total_labor_hours": data["total_labor_hours"],
                "avg_labor_hours": avg
            }
        return result

    def sync_stats(self, agents: List[Any]):
        # O(N) Recovery for Tests/Startup
        self._stats_cache = {"M": {"count": 0...}, "F": ...}
        for agent in agents:
            if agent.is_active:
                self._stats_cache[agent.gender]["count"] += 1
                # Recalculate labor if possible, or assume 0 for fresh sync
```

### 3.2. Migration: DemographicsComponent

The component currently handles death probabilistically and sets `is_active=False`. This must change to a **Request** pattern.

```python
# Old
if random.random() < death_prob:
    self.owner.is_active = False # ❌ BAD

# New
if random.random() < death_prob:
    # ✅ Delegate to Manager
    # Requires manager injection or service locator (temporary)
    self.owner.demographic_manager.register_death(self.owner, cause="OLD_AGE")
```

## 4. Verification Plan

### 4.1. Performance Benchmark
- **Test**: `tests/benchmarks/test_demographic_perf.py`
- **Setup**: Create 10,000 mocked agents.
- **Action**: Call `get_gender_stats()` 1,000 times.
- **Assert**: Total time < 0.1s (Should be near-instant).

### 4.2. Cache Consistency
- **Test**: `tests/unit/modules/demographics/test_event_consistency.py`
- **Scenario**:
    1. Create Manager.
    2. `register_birth(male_agent)` -> Assert Count M=1.
    3. `register_birth(female_agent)` -> Assert Count F=1.
    4. `register_death(male_agent)` -> Assert Count M=0.
    5. `update_labor_hours("F", 5.0)` -> Assert Avg Labor F=5.0.

### 4.3. Legacy Integration
- **Test**: Run existing `tests/unit/modules/simulation/test_population.py`.
- **Fix**: Inject `sync_stats(simulation.agents.values())` in the test setup if it fails due to zero stats.

## 5. Risk Audit
- **Risk**: `update_labor_hours` spam.
- **Mitigation**: Agents should only call this when allocation *changes*, not every tick.
- **Risk**: "Zombie Agents" (Active but not in cache).
- **Mitigation**: `sync_stats` is the fallback. 
```