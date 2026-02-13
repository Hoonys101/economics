# Fix: [STABILITY-2-4] Pytest Infra & Asyncio Issues

## 1. Architectural Insights
*   **DI Violation**: `Simulation` engine was missing critical dependencies (`settlement_system`, `agent_registry`) in its `WorldState` initialization, causing `NoneType` errors in `TransactionProcessor`. Fixed by explicitly injecting them in `Simulation.__init__`.
*   **Command Service API**: `Simulation` relied on a deprecated `pop_commands()` method. Refactored `Simulation._process_commands` to use `WorldState` queues (`command_queue` -> `god_command_queue`) and handle control commands (`PAUSE`, `RESUME`, `STEP`) locally via `GodCommandDTO`. Added `pop_commands()` to `CommandService` for backward compatibility.
*   **Async Testing**: `pytest-asyncio` was missing from `requirements.txt` and `pytest.ini` lacked loop scope configuration, causing async tests to fail.
*   **Test Infrastructure**: Several integration tests (`test_cockpit_integration.py`, `test_wo058_production.py`) were manually instantiating `Simulation` with missing arguments. Updated these tests to inject required Mocks and adapt to the queue-based Command API.

## 2. Test Evidence
### System Tests (`tests/system/test_engine.py`)
```
tests/system/test_engine.py::TestSimulation::test_simulation_initialization PASSED [ 11%]
...
tests/system/test_engine.py::test_handle_agent_lifecycle_removes_inactive_agents PASSED [100%]
```

### Integration Tests (`tests/integration/test_server_integration.py`)
```
tests/integration/test_server_integration.py::test_command_injection PASSED [ 50%]
tests/integration/test_server_integration.py::test_telemetry_broadcast PASSED [100%]
```

### Fiscal Policy Tests (`tests/integration/test_fiscal_policy.py`)
```
tests/integration/test_fiscal_policy.py::test_debt_ceiling_enforcement PASSED [ 80%]
...
```

### Cockpit Integration & Production (`tests/integration/test_cockpit_integration.py`, `tests/integration/test_wo058_production.py`)
```
tests/integration/test_cockpit_integration.py::test_simulation_processes_pause_resume PASSED [ 20%]
tests/integration/test_cockpit_integration.py::test_simulation_processes_set_base_rate PASSED [ 40%]
tests/integration/test_cockpit_integration.py::test_simulation_processes_set_tax_rate PASSED [ 60%]
tests/integration/test_wo058_production.py::test_bootstrapper_injection PASSED [ 80%]
tests/integration/test_wo058_production.py::test_production_kickstart PASSED [100%]
```
