# Insight Report: Fix Stability Tests DI Refactoring

## 1. Architectural Insights
- **Simulation Facade vs. Component Logic**: The `Simulation` class acts as a facade. The refactoring correctly delegated command processing to `CommandService` (logic) while keeping the loop control (`PAUSE`, `STEP`) in `Simulation` (facade). This separation of concerns was partially broken by the removal of `pop_commands` without a direct replacement.
- **Dependency Injection for WorldState**: `ActionProcessor` and `TransactionProcessor` rely on `WorldState` having access to system components like `SettlementSystem`. However, `SimulationInitializer` injected these into `Simulation` but `Simulation` did not propagate them to `WorldState` consistently. I enforced explicit injection in `Simulation.__init__` to ensure `WorldState` acts as the single source of truth for system components during transaction processing.
- **DTO Purity in Tests**: Integration tests were using `CockpitCommand` (deprecated) instead of `GodCommandDTO`. Updating the tests to use the strict DTO ensures that the test environment mirrors the actual runtime contract of `CommandService`.

## 2. Test Evidence
```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.2.2, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
testpaths: tests/unit, tests/integration, tests/system, tests
plugins: anyio-4.4.0
collected 17 items

tests/integration/test_cockpit_integration.py ...                        [ 17%]
tests/integration/test_fiscal_policy.py .....                            [ 47%]
tests/system/test_engine.py .........                                    [100%]

============================== 17 passed in 0.40s ==============================
```
