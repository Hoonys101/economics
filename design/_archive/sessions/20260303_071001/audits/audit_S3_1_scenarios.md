# Forensic Audit: Scenario Runner Memory Leak & God DTO Cycle Analysis

## Executive Summary
The critical `gc.collect()` hang in `tests/integration/scenarios/test_scenario_runner.py` is the result of memory exhaustion and garbage collection thrashing. This is caused by unbounded reference expansion in circular graphs where the `SimulationState` "God DTO" links to `MagicMock` entities that retain exhaustive call histories. The leak is compounded by the lack of explicit simulation finalization in the test loop and self-referential structures in mocking utilities.

## Detailed Analysis

### 1. SimulationState (God DTO) Circularity
- **Status**: ⚠️ Partial / High Risk
- **Evidence**: `simulation/dtos/api.py:L231-285` defines `SimulationState` as a container for all core entities (`households`, `firms`, `bank`, `central_bank`, `registry`).
- **Notes**: Bidirectional cycles are formed when `SimulationState` is passed to agents (e.g., via `DecisionInputDTO` or `DecisionContext`) or system services whose internal engines are `MagicMocks`. The mocks record the `SimulationState` in their `call_args` or `method_calls` history. Since `SimulationState` holds the entire population of agents (L237-238), a single recorded call pins the entire simulation graph, leading to exponential memory growth during the tick loop.

### 2. MockRepository Self-Reference
- **Status**: ❌ Missing (Self-Referential Implementation Found)
- **Evidence**: `tests/integration/scenarios/test_scenario_runner.py:L43-51` shows `self.runs = self`, `self.agents = self`, etc.
- **Notes**: The `MockRepository` implementation uses an explicit self-referential cycle. While functional for simple lookups, this pattern complicates GC traversal when these objects are swept into the larger `SimulationState` graph, contributing to the "hang" during `gc.collect()`.

### 3. Lifecycle Cleanup Failure
- **Status**: ⚠️ Partial
- **Evidence**: `simulation/engine.py:L110` defines `finalize_simulation()`, but `tests/integration/scenarios/test_scenario_runner.py` never invokes it.
- **Notes**: Failure to call `finalize_simulation()` leaves `SimulationLogger` file handles and `DBManager` buffers active. This pins the `Simulation` and its associated `WorldState` in memory. In parametrized tests, each scenario adds a new layer of uncollected objects, eventually stalling the garbage collector.

## Risk Assessment
- **State Pollution**: `current_pytest_output.txt` reports `XFAIL` status due to `TD-ARCH-MOCK-POLLUTION`. This confirms that `MagicMock` attributes are leaking into vectorized production logic (e.g., `VectorizedHouseholdPlanner`), indicating a breach in the DTO "Purity Gate."
- **Duct-Tape Debugging**: The use of `XFAIL` to bypass mock-induced crashes rather than addressing the root circularity represents a significant architectural risk.

## Conclusion
The `gc.collect()` hang is a symptom of a bloated object graph that the Python garbage collector cannot traverse efficiently. **Resolution requires three steps**: (1) partitioning `SimulationState` into granular, domain-specific DTOs, (2) enforcing the use of `sim.finalize_simulation()` in test teardown via pytest fixtures, and (3) replacing self-referential mocks in `test_scenario_runner.py` with stateless protocol-compliant builders.

---

### Insight Report: communications/insights/audit-mock-leak-scenarios.md

```markdown
# Insight Report: Forensic Audit - Mock Leak in Scenarios

## 1. [Architectural Insights]
- **God DTO Pattern**: `SimulationState` acts as a central sink for the entire world state, violating the Principle of Least Privilege. This DTO makes components untestable in isolation without dragging in the entire object graph.
- **Mock Accumulation**: `MagicMock` objects in integration tests are "trapping" the `SimulationState` DTO in their call history. Because the DTO is a "God Object," a single trapped reference pins the entire simulation memory.

## 2. [Regression Analysis]
- **TD-ARCH-MOCK-POLLUTION**: Existing tests in `test_scenario_runner.py` are failing (XFAIL) because `MagicMock` objects are leaking into `VectorizedHouseholdPlanner`. The planner attempts to perform `numpy` operations on these mocks, which fail, demonstrating that the "Purity Gate" for DTOs is not strictly enforced.

## 3. [Test Evidence]
- **Current Status**: `tests/integration/scenarios/test_scenario_runner.py::TestScenarioRunner::test_run_scenario` -> **XFAIL**
- **Log Source**: `current_pytest_output.txt`
- **Error Note**: `TD-ARCH-MOCK-POLLUTION: VectorizedHouseholdPlanner uses numpy ops which fail with MagicMocks from tests.`
- **Audit Observation**: `MockRepository` in `test_scenario_runner.py` contains explicit `self = self` cycles, further increasing GC complexity.
```