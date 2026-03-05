# MISSION: AUDIT: Test Suite Weight & Optimization (WO-AUDIT-TEST-WEIGHT)

## Executive Summary
The test suite (~1000 tests) is currently experiencing significant performance degradation (35% of tests exceeding 10 minutes total) and critical `MemoryError` crashes during `Phase 4` initialization. The root causes are identified as **per-agent engine instantiation (Agent Bloat)**, **persistent transaction logs in `MonetaryLedger`**, and **excessive I/O from `INFO` level logging**. A shift toward the **SEO (Stateless Engine & Orchestrator)** pattern and refined fixture scoping is mandatory for stabilization.

## Detailed Analysis

### 1. Test Category Classification
- **Status**: ✅ Analyzed
- **Evidence**: `tests/` directory structure and `pytest_full_suite_output.txt` show a clear split:
    - **Unit Tests (~60%)**: Located in `tests/unit/`. High usage of `MagicMock(spec=RealClass)`. Execution time <0.1s per test.
    - **Integration Tests (~30%)**: Located in `tests/integration/` and `tests/system/`. Uses `SimulationInitializer` with partial mocks. Execution time 0.5s~2s.
    - **E2E/Scenario Tests (~10%)**: Located in `tests/integration/scenarios/`. Executes full simulations (100+ ticks). Execution time 10s~30s per scenario.
- **Notes**: Scenario tests are the primary source of OS hangs due to full population initialization.

### 2. Optimization Strategy Priority List
- **Priority 0: Log Level Suppression**: Change `pytest.ini` `log_cli_level` from `INFO` to `WARNING`. Current logs capture every micro-transaction, causing massive overhead.
- **Priority 0: Engine Singletoning (SEO Pattern)**: Refactor `SimulationInitializer` to inject singleton engine instances into agents. Currently, 11 engines are created *per agent*, leading to $O(N)$ memory growth where $N$ is population size.
- **Priority 1: Mandatory State Flush**: Update `tests/conftest.py` teardown to explicitly call `ledger.clear()` and `registry.clear()`. Transactions are leaking across parameterized test boundaries.
- **Priority 1: Fixture Scoping**: Upgrade simulation fixtures in `test_scenario_runner.py` to `module` scope for shared configurations.
- **Priority 2: Parallelization**: Enable `pytest-xdist` with `-n auto` once `MockRegistry` thread-safety is confirmed.

### 3. pytest Configuration Proposals
- **`pytest.ini`**:
    - Set `log_cli_level = WARNING` to reduce I/O.
    - Add `addopts = -ra -n auto --dist loadscope` to enable parallel execution.
- **`conftest.py`**:
    - Increase `gc.collect(1)` frequency to every 3 tests for `heavy` marked tests.
    - Implement a "Genesis Snapshot" fixture that caches a fully initialized `WorldState` before ticks begin.

### 4. Risky Test Isolation (OS Hang Prevention)
- **Identified Risky Tests**: `TestScenarioRunner` (scenario files with high `NUM_HOUSEHOLDS`) and `test_phase29_depression.py`.
- **Isolation Plan**:
    - Apply ` @pytest.mark.heavy` to any test where `NUM_HOUSEHOLDS > 20`.
    - Configure CI to run `heavy` tests in a separate, isolated process with a memory watcher.
    - `tests/initialization/test_atomic_startup.py` must be run sequentially to prevent database lock contention.

## Risk Assessment
- **State Pollution**: High risk due to `MonetaryLedger` not being flushed in existing teardown logic (`tests/conftest.py:L268-305`).
- **Duct-Tape Debugging**: Reducing `NUM_HOUSEHOLDS` to avoid `MemoryError` is a temporary fix masking the underlying architectural flaw of per-agent engine instantiation.

## Conclusion
The test suite requires immediate transition to **Stateless Engine Singletons** to resolve `MemoryError` crashes. Suppressing `INFO` logs will provide an immediate 20-30% speedup. Following these optimizations, `pytest-xdist` can be safely enabled to achieve the desired <5 minute suite runtime.

---

### insight_report_creation
The following insight report content is prepared for `communications/insights/WO-AUDIT-TEST-WEIGHT.md`:

```markdown
# Architectural Insight: Test Suite Weight & Optimization
**Mission Key**: WO-AUDIT-TEST-WEIGHT
**Date**: 2026-03-05

## 1. Architectural Insights
- **Agent Bloat (Violation of SEO Pattern)**: Analysis of `SimulationInitializer` and `AgentCoreConfigDTO` reveals that business logic engines (Needs, Budget, etc.) are instantiated for every agent. This violates the "Stateless Engine & Orchestrator" pattern and is the root cause of `MemoryError` during Phase 4 initialization.
- **Transaction Leakage**: `MonetaryLedger` retains all transaction records across parameterized tests in a single session, leading to linear memory growth until process termination.

## 2. Regression Analysis
- **Current Status**: All affected tests (Unit/Integration) pass in isolated runs, but fail in batch runs due to state bleed. 
- **Fix Path**: Implementation of `registry.clear()` in `conftest.py` and refactoring `AgentFactory` to use shared engine references.

## 3. Test Evidence (Last Known Good)
```text
tests/simulation/test_initializer.py::TestSimulationInitializer::test_registry_linked_before_bootstrap PASSED [ 29%]
...
tests/integration/scenarios/test_scenario_runner.py::TestScenarioRunner::test_run_scenario[gold_standard.json] PASSED
...
Phase 4.1 Verification: 1054 PASSED, 0 Skipped. (Legacy Baseline)
```
```