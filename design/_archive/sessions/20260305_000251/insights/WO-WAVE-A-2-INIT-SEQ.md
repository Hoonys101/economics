# WO-WAVE-A-2-INIT-SEQ: 5-Phase Atomic Initialization Sequence

## 1. Architectural Insights
The `SimulationInitializer.build_simulation` method has been successfully refactored from a monolithic "God Function" into a strictly ordered 5-Phase sequence. This decomposition addresses critical technical debt and enhances system stability.

### Technical Debt Resolved
*   **TD-INIT-RACE (Registry Race Condition)**: Previously, agents could be instantiated and attempt to access the `GlobalRegistry` or `AgentRegistry` before they were fully initialized or linked to the `WorldState`. By explicitly separating `_init_phase1_infrastructure` (where registries are created) from subsequent phases, we ensure that the infrastructure is ready before any agent logic is executed.
*   **TD-FIN-INVISIBLE-HAND (Cyclic Dependencies)**: The circular dependency between `Government`, `FinanceSystem`, and `Bank` was a major source of fragility. In `_init_phase2_system_agents`, we now instantiate these singletons first and then use property setter injection to wire them together. This eliminates the need for complex "partial initialization" hacks.
*   **Implicit Initialization Order**: The previous implementation relied on implicit ordering within a single massive function. The new structure enforces a strict topological sort:
    1.  **Infrastructure**: Locks, Registries, EventBus, Ledger.
    2.  **Sovereign Layer**: `Government`, `Bank`, `CentralBank`, `PublicManager`.
    3.  **Market & Systems Layer**: `OrderBookMarket`, `LoanMarket`, `LaborMarket`, `TaxationSystem`, etc.
    4.  **Agent Layer**: `Household`, `Firm`.
    5.  **Genesis**: Money creation and wealth distribution.

### Architectural Decisions
*   **Atomic Phases**: Each phase is a distinct method that modifies the `Simulation` object in place or returns it (Phase 1). This makes the initialization flow readable and testable.
*   **Penny Standard Enforcement**: In Phase 5 (`_init_phase5_genesis`), we strictly enforce the Penny Standard for `initial_bank_assets`, converting potential config floats to integers. This prevents `FloatIncursionError` at the very start of the simulation.
*   **System Agent Registry**: We explicitly re-merge System Agents into the main `sim.agents` dictionary in Phase 4. This ensures that lookups for ID 0 (Government), ID 1 (Central Bank), etc., resolve correctly during population setup and genesis.
*   **Dependency Injection Fixes**:
    *   `AITrainingManager` (Phase 3) now correctly uses `self.households` and `self.firms` instead of accessing them via `sim`, preventing runtime `AttributeError` as `sim` attributes are set in Phase 4.
    *   `sim.agents` update in Phase 4 now uses `.update()` to preserve System Agents added in Phase 2.

## 2. Regression Analysis
The refactoring involved moving a significant amount of code. To ensure no functionality was lost or broken:

*   **Mocking Strategy**: The existing `test_initializer.py` relied heavily on mocking. The refactoring maintained the dependency structure such that existing mocks (patched at `simulation.initialization.initializer`) continue to work. We verified this by running `pytest tests/simulation/test_initializer.py`.
*   **Phase Validation**: We introduced `tests/initialization/test_atomic_startup.py` to explicitly verify that:
    *   The lock is acquired first (Phase 1).
    *   The registry is linked (Phase 2).
    *   Bootstrapping happens last (Phase 5).
*   **System Integrity**: We ran the full test suite (`pytest tests/`) to catch any subtle integration issues. All 1039 tests passed, confirming that the new initialization sequence produces a valid `Simulation` object compatible with all downstream systems.

## 3. Test Evidence

### New Test: `tests/initialization/test_atomic_startup.py`
```
tests/initialization/test_atomic_startup.py::TestAtomicStartup::test_atomic_startup_phase_validation PASSED [100%]
```

### Regression Test: `tests/simulation/test_initializer.py`
```
tests/simulation/test_initializer.py::TestSimulationInitializer::test_registry_linked_before_bootstrap PASSED [100%]
```

### Full Suite: `tests/`
```
================= 1039 passed, 11 skipped, 1 warning in 15.16s =================
```
