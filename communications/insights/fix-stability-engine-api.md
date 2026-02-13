# Fix: [STABILITY-2-1] Simulation & CommandService API Alignment

## 1. Architectural Insights

### Dependency Injection Gaps
The primary cause of the `AttributeError: 'NoneType' object has no attribute 'settle_atomic'` in `test_engine.py` was a missing injection of `SettlementSystem` into `WorldState` within the `Simulation` constructor. While `Simulation` received the dependency, it failed to propagate it to `WorldState`, leaving `TransactionProcessor` (which relies on `WorldState.settlement_system` for its context) with a `None` reference. This highlights the fragility of manual dependency injection in the `Simulation` facade and suggests a need for a more robust container or builder pattern that ensures `WorldState` is fully populated before usage.

### Command Processing Refactoring
The `Simulation._process_commands` method was attempting to call `self.command_service.pop_commands()`, a method that no longer exists in the new `CommandService` architecture (which is stateless regarding the queue). I refactored `Simulation` to:
1.  Directly drain the thread-safe `WorldState.command_queue`.
2.  Handle "System Control" commands (`PAUSE`, `RESUME`, `STEP`) locally.
3.  Forward "God Mode" commands (`SET_PARAM`, `INJECT_ASSET`) to `WorldState.god_command_queue` for processing by `TickOrchestrator` (Phase 0).
This separation of concerns ensures that the `Simulation` loop handles lifecycle (Time) while the `TickOrchestrator` handles mutations (State), respecting the architectural boundary.

### Test Suite Alignment
Several integration tests were out of sync with the codebase:
-   `test_cockpit_integration.py`: Instantiated `Simulation` with missing arguments and used legacy `CommandService` methods.
-   `test_fiscal_policy.py`: Mocked `SettlementSystem` inconsistent with `Wallet` state, causing valid spending logic to fail checks.
-   `pytest-asyncio`: Missing from environment, causing async tests to be skipped or fail.

## 2. Test Evidence

```text
============================= test session starts ==============================
platform linux -- Python 3.12.9, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
testpaths: tests/unit, tests/integration, tests/system, tests
plugins: anyio-4.8.0, asyncio-0.25.1, mock-3.14.0
asyncio: mode=Mode.AUTO, default_loop_scope=None
collected 19 items

tests/integration/test_cockpit_integration.py ...                        [ 15%]
tests/integration/test_fiscal_policy.py ....                             [ 36%]
tests/integration/test_server_integration.py ..                          [ 47%]
tests/system/test_engine.py ..........                                   [100%]

============================== 19 passed in 3.37s ==============================
```
