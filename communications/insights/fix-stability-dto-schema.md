# Fix: [STABILITY-2-2] GodCommandDTO Schema Compatibility & Command Service Refactoring

## 1. Architectural Insights

### 1.1 Command Processing Separation (Engine Purity)
The `Simulation` engine previously contained a direct reference to `CommandService` and executed `_process_commands()` within its `run_tick()` loop. This violated the **Stateless Engine Purity** principle, as the Engine should primarily focus on the physical/economic state transition based on inputs, rather than managing external command lifecycles directly.

We have removed `CommandService` from the `Simulation` class entirely. Command processing is now explicitly handled by `TickOrchestrator` via `Phase0_Intercept`. This ensures:
- **Separation of Concerns:** The Engine focuses on the simulation loop, while the Orchestrator manages the phase execution pipeline.
- **Explicit Causality:** God-Mode commands are guaranteed to execute *before* any simulation logic (Phase 0), ensuring that parameter changes take effect immediately for the current tick.

### 1.2 Registry Encapsulation & Atomic Rollback
The `CommandService`'s rollback mechanism for `SET_PARAM` was previously flawed. It only restored the parameter's `value`, but failed to restore its metadata (`OriginType` and `is_locked` status). This could lead to a state where a `GOD_MODE` lock was inadvertently cleared during a rollback, or a `SYSTEM` origin parameter was left with a `GOD_MODE` origin.

We introduced `delete_entry(key)` and `restore_entry(key, entry)` to the `IGlobalRegistry` protocol and `GlobalRegistry` implementation. This allows `CommandService` to perform a **True State Restore**:
- If a key was created by the command, rollback now deletes it completely.
- If a key existed, rollback restores the entire `RegistryEntry` object, preserving its original `OriginType` and lock status.

This change adheres to the **Zero-Sum Integrity** and **Protocol Purity** mandates by treating the Registry state as an atomic unit during rollback operations.

## 2. Test Evidence

### 2.1 Rollback Integrity (New Test)
We created `tests/system/test_command_service_rollback.py` to verify the enhanced rollback logic.

```
$ pytest tests/system/test_command_service_rollback.py
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
testpaths: tests/unit, tests/integration, tests/system, tests
plugins: asyncio-0.21.0, mock-3.15.1
asyncio: mode=Mode.STRICT
collected 3 items

tests/system/test_command_service_rollback.py ...                        [100%]

============================== 3 passed in 0.05s ===============================
```

### 2.2 System Stability (Regression Test)
We verified that the core engine and fiscal policy integrations remain stable after the refactoring.

```
$ pytest tests/system/test_engine.py tests/integration/test_fiscal_policy.py
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pytest.ini
testpaths: tests/unit, tests/integration, tests/system, tests
plugins: asyncio-0.21.0, mock-3.15.1
asyncio: mode=Mode.STRICT
collected 14 items

tests/system/test_engine.py .........                                    [ 64%]
tests/integration/test_fiscal_policy.py .....                            [100%]

============================= 14 passed in 0.92s ===============================
```

## 3. Technical Debt Resolution
- **Encapsulation Breach Fixed:** `CommandService` no longer accesses private `_storage` of `GlobalRegistry`. It uses the new public interface methods.
- **Dynamic Assignment Fixed:** `WorldState` now explicitly defines `agent_registry` as an optional attribute, resolving potential type checking issues.
