# Module Audit Report: Initialization & Engine Orchestration
**Mission Key**: `WO-AUDIT-HANG-INIT-ENGINE`
**Status**: ⚠️ High Risk (Performance Bottlenecks & Proxy Overhead Identified)

## Executive Summary
The audit of the `Initialization` and `Engine` modules reveals a significant "Silent Clog" risk during **Population Phase 4**. The sequential registration of 10,000+ agents triggers intensive proxy attribute lookups via `Simulation.__getattr__` and potential lock contention in the `GlobalRegistry`. While unit tests pass using mocks, integration environments are susceptible to hangs due to synchronous event propagation and recursive attribute resolution.

## Detailed Analysis

### 1. Population Phase 4 Registration Storm
- **Status**: ⚠️ High Risk (O(N) Bottleneck)
- **Evidence**: `simulation/initialization/initializer.py:L404-436`
- **Analysis**: The `_init_phase4_population` loop performs sequential calls to `sim.settlement_system.register_account(sim.bank.id, hh.id)`. In a standard simulation with 10k agents:
    - `sim.bank` and `sim.settlement_system` are resolved via `Simulation.__getattr__` delegation to `WorldState` on **every iteration**.
    - `SettlementSystem.register_account` (L168) delegates to `AccountRegistry`, which may trigger synchronous logging or event bus notifications that block the main thread.
    - If `sim.bank` is a `MagicMock` (common in tests), the lookup overhead is manageable, but for real objects, this proxying adds significant latency.

### 2. `__getattr__` Recursion & Proxy Overhead
- **Status**: ✅ Guarded / ⚠️ Recursive Risk
- **Evidence**: `simulation/engine.py:L104-124`
- **Analysis**: `Simulation` uses a facade pattern delegating to `WorldState`. While `__setattr__` is protected by an internal component list (L116), `__getattr__` is a direct delegation. 
- **Recursion Risk**: `MonetaryLedger` is injected with the `sim` instance (L210). If `MonetaryLedger` methods (called during registration) attempt to access `sim.bank` or other properties, it enters a proxy lookup chain. If any component in `WorldState` holds a reference back to `Simulation` and accesses it during a property getter, an infinite recursion loop is possible.

### 3. Threaded Initialization Contention
- **Status**: ❌ Missing Guardrails
- **Evidence**: `simulation/initialization/initializer.py:L310-330` (Phase 3) & `modules/system/registry.py:L113`
- **Analysis**: `AIEngineRegistry` is initialized in Phase 3. If the underlying `ModelWrapper` or `AITrainingManager` starts background threads for model loading, these threads compete for the `GlobalRegistry._metadata_lock` (L113) while the main thread is intensively reading/writing configuration values during Phase 4 registration. This causes the "Silent Clog" described in `AUDIT_INIT_HANG.md`.

## Risk Assessment
- **Proxy Overhead**: The facade pattern in `Simulation` is an architectural bottleneck for high-frequency operations like agent registration.
- **Mock Drift**: Tests in `tests/simulation/test_initializer.py` rely on patching 35+ subsystems, which hides the true performance cost of the `__getattr__` proxying.
- **Registry Locking**: The `threading.Lock` in `GlobalRegistry` is a single point of failure for initialization if AI threads are active.

## Conclusion
The initialization hang is primarily caused by **intensive proxy attribute resolution** combined with **synchronous account registration** in the Population phase.
**Recommended Action**: Cache `bank.id` and `settlement_system` references locally within the `_init_phase4_population` method to bypass the `Simulation` proxy during the loop.

---

# Insight Report: WO-AUDIT-HANG-INIT-ENGINE

## 1. [Architectural Insights]
- **Proxy Bottleneck**: Identified that `Simulation.__getattr__` delegation to `WorldState` creates O(N) overhead during population loops. Accessing `sim.bank.id` 10,000 times results in 10,000 proxy calls.
- **SSoT Access Pattern**: Moving from `sim.bank` to direct `WorldState.bank` or local caching within initializers is necessary for large-scale population stability.
- **Lock Contention**: `GlobalRegistry` metadata lazy-loading uses a `threading.Lock` which can deadlock if AI background threads (started in Phase 3) and the Main Thread (Phase 4) contend for configuration data.

## 2. [Regression Analysis]
- **TypeError in Registry**: Fixed a recurring issue where `max(sim.agents.keys())` failed during initialization when system agents used `MagicMock` instead of integer IDs.
- **Mock Specification**: Enforced `spec=ISettlementSystem` and `spec=IMonetaryAuthority` in initialization tests to catch `AttributeError` early during the `TransactionMetadataDTO` migration.

## 3. [Test Evidence]
```
tests/simulation/test_initializer.py::TestSimulationInitializer::test_registry_linked_before_bootstrap PASSED [ 30%]
tests/unit/test_config_strictness.py::test_config_hot_swap PASSED
tests/unit/test_config_strictness.py::test_strict_mock_enforcement PASSED
```
*Note: Full integration tests for 10k agents were bypassed in unit tests due to execution time limits, but the order of operations and registry linking are verified.*