# Phase 17 Optimization Strategy: Performance & Stability

## 1. Project Overview

- **Goal**: Resolve critical technical debt impacting simulation scalability, stability, and testing integrity.
- **Scope**: 
    - **Performance**: Optimize `DemographicManager` to O(1) or O(events) scaling.
    - **Stability**: Replace brittle Regex-based manifest editing with structured JSON/YAML.
    - **Architecture**: Enforce strict Protocol usage in `SettlementSystem` and fix "Ghost Constant" binding issues.
- **Success Criteria**:
    - `DemographicManager` gender stats calculation is instant (cached).
    - `command_manifest.py` is replaced by `command_registry.json` managed by a robust Service.
    - All Config access uses `GlobalRegistry` (hot-swap ready).
    - `ISettlementSystem` mocks in tests use `spec=ISettlementSystem` without failure.

## 2. Architectural Analysis (Root Causes)

### 2.1. TD-DATA-03-PERF: The Demographic Loop
- **Symptom**: `DemographicManager.get_gender_stats()` iterates over `world_state.households` (O(N)) every time it is called.
- **Root Cause**: The manager lacks an internal state for aggregate statistics and relies on a "Pull" model from the World State, which is inefficient for high-frequency queries.
- **Risk**: As population grows to 10k+, this loop will bottleneck the simulation loop (Tick Budget Exceeded).

### 2.2. TD-SYS-BATCH-FRAGILITY: Data as Code
- **Symptom**: Mission definitions are stored in `command_manifest.py`, a Python file, and modified via Regex.
- **Root Cause**: Mixing Configuration (Data) with Logic (Python Code).
- **Risk**: A single syntax error in a mission description can crash the entire Registry. Regex edits are fragile against formatting changes (e.g., whitespace, comments).

### 2.3. TD-DATA-01-MOCK: Protocol Drift
- **Symptom**: `ISettlementSystem` mocks in tests do not match the actual `api.py` definition (e.g., missing `mint_and_distribute` or `audit_total_m2`).
- **Root Cause**: Use of `MagicMock()` without `spec` argument, allowing tests to pass with fictitious methods.
- **Risk**: "False Positive" tests that pass but fail in production/integration.

### 2.4. TD-SYS-GHOST-CONSTANTS: Import-Time Binding
- **Symptom**: Modules use `from config import PARAM`.
- **Root Cause**: Python binds imported values at module load time. Subsequent updates to `GlobalRegistry` (or even `config.PARAM`) are ignored by the consuming module.
- **Risk**: Simulation parameters cannot be tuned dynamically (God Mode, AI Curriculum), leading to inconsistent simulation states.

## 3. Detailed Design

### 3.1. DemographicManager Optimization (Event-Driven)

**Pattern**: Observer / Event Listener

**Changes**:
1.  **Stateful Aggregation**: `DemographicManager` will maintain a private `_stats_cache` dictionary.
2.  **Event Hooks**:
    - `on_birth(gender)`: Increment count.
    - `on_death(gender)`: Decrement count.
    - `on_tick()`: Update `total_labor_hours` (Optimized or Sampled). *Note: Labor hours change every tick. For strict O(1), we may need to accept an approximation or calculate it lazily.*
3.  **Refactoring**:
    - Remove dependency on `world_state` for *statistics*.
    - Ensure all lifecycle events (Birth, Death) pass through `DemographicManager`.

```python
# Pseudo-code Structure
class DemographicManager:
    def __init__(self):
        self._gender_counts = {"M": 0, "F": 0}

    def register_birth(self, agent: Household):
        self._gender_counts[agent.gender] += 1
        # ... logic ...

    def register_death(self, agent: Household):
        self._gender_counts[agent.gender] -= 1
        # ... logic ...
    
    def get_gender_stats(self):
        # O(1) return of cached counters
        return self._gender_counts
```

### 3.2. Manifest Service (JSON Migration)

**Pattern**: Repository Pattern

**Changes**:
1.  **Storage**: Migrate `_internal/registry/command_manifest.py` -> `_internal/registry/mission_db.json`.
2.  **Service**: Create `MissionRegistryService` class.
    - `load_missions()`: Read JSON.
    - `register_mission(mission_dto)`: Update JSON atomically.
    - `mark_complete(mission_key)`: Update status.
3.  **Legacy Support**: `command_manifest.py` becomes a deprecated loader that imports from the JSON service if needed, or is removed entirely.

### 3.3. Strict Protocol Enforcement

**Pattern**: Interface Segregation & Strict Mocking

**Changes**:
1.  **Protocol Split (Optional)**: If `mint_and_distribute` is only for God Mode, move it to `IMonetaryAuthority`. Keep `ISettlementSystem` for pure transfers.
    - *Decision*: For now, keep in `ISettlementSystem` but mark as `System-Only`.
2.  **Test Refactoring**:
    - Global Search & Replace: `MagicMock()` -> `MagicMock(spec=ISettlementSystem)` for all settlement mocks.
    - Fix all resulting `AttributeError` failures by implementing the missing methods in the Test Stubs.

### 3.4. GlobalRegistry Binding Migration

**Pattern**: Accessor Pattern

**Changes**:
1.  **Ban**: `from config import X`.
2.  **Enforce**: `import config` -> usage `config.X`.
3.  **Implementation**:
    - Use `grep` to find all violations.
    - Refactor to property access.
    - Ensure `config/__init__.py` properly proxies `__getattr__` to `GlobalRegistry`.

## 4. Implementation Plan (Jules Tasks)

### Lane 1: Core Architecture (Performance & Config)
- **Task 17.1**: **Refactor Config Access**
    - **Goal**: Eliminate `from config import` pattern.
    - **Action**: Grep codebase, refactor to `import config`, verify `GlobalRegistry` is hit.
- **Task 17.2**: **Optimize DemographicManager**
    - **Goal**: Implement Event-Driven Stats.
    - **Action**: Add `_stats_cache`. Update `process_births` and `_execute_natural_death` to update cache. Remove `world_state` loop in `get_gender_stats`.

### Lane 2: Stability & Hygiene (Manifest & Tests)
- **Task 17.3**: **Migrate Manifest to JSON**
    - **Goal**: Replace `command_manifest.py`.
    - **Action**: Create `MissionRegistryService`. Convert existing manifest to `mission_db.json`. Update `jules-go.bat` / scripts to use new Service.
- **Task 17.4**: **Strict Mock Enforcement**
    - **Goal**: Fix Test Drift.
    - **Action**: Update `tests/` to use `spec=Protocol`. Run tests, fix breakages by updating Stubs to match `api.py`.

## 5. Verification Plan

### 5.1. Performance Verification
- **Benchmark**: Run `DemographicManager.get_gender_stats()` with 10,000 agents.
    - **Before**: > 10ms (estimate).
    - **After**: < 0.01ms (Instant).

### 5.2. Stability Verification
- **Test**: Add a mission with special characters and newlines via `MissionRegistryService`.
    - **Pass**: JSON parses correctly, no syntax errors.

### 5.3. Mock Verification
- **Test**: `pytest tests/unit/modules/finance/test_settlement.py`
    - **Pass**: All tests pass with `spec=ISettlementSystem` enabled.

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| **Circular Imports (Config)** | High | Critical | Use local imports inside functions if modules depend on each other during config load. |
| **Data Loss (Manifest)** | Low | High | Backup `command_manifest.py` before deleting. Validate JSON schema. |
| **Test Explosion** | Medium | Medium | Strict mocking may reveal many hidden bugs. Timebox the fix effort. |

---

## 7. Insight & Audit Report (Mandatory)

### 7.1. The "Ghost Constant" Peril
The `TD-SYS-GHOST-CONSTANTS` issue is a "time-bomb". The refactor must be thorough. Any skipped module will continue to use stale values, leading to confusing bugs where "changing the config doesn't work".

### 7.2. Service Locator in DemographicManager
The current `DemographicManager` uses `getattr(simulation, ...)` which is a Service Locator anti-pattern. The optimization task (17.2) should also introduce proper Dependency Injection (DI) to make the class testable without the full Engine.

### 7.3. Interface Segregation
`ISettlementSystem` is becoming a God Interface. While we are fixing mocks, we should consider splitting `minting` (God Mode) from `transfers` (Agent Mode) to prevent normal agents from even seeing the minting methods in their interface definition.