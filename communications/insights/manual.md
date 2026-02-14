# Architectural Report: Protocol Normalization

## [Architectural Insights]
### Protocol Centralization
- **Technical Debt Addressed**: `TD-ARCH-PROTO-LOCATION`
- **Action**: Moved locally defined protocols `ISectorAgent` and `ICommandService` (Simulation/GodMode) from `modules/system/services/command_service.py` to a new centralized API module `modules/api/protocols.py`.
- **Reasoning**:
  - Reduced coupling between `command_service.py` and its consumers.
  - Established a clear location (`modules/api/protocols.py`) for core simulation protocols that don't fit into domain-specific APIs or need to be shared widely without circular dependencies.
  - `ISectorAgent` is a cross-cutting trait used by `CommandService` to filter agents, and should be available for agents to implement without importing `command_service`.
  - `ICommandService` is the primary interface for God Mode commands and should be importable by components that need to mock it or interact with it (like `Simulation`), without dragging in the implementation details.

## [Test Evidence]
```
tests/unit/modules/system/test_command_service_unit.py::test_dispatch_set_param PASSED [ 10%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_set_param_restorable
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:270 ROLLBACK: Restored test_param to 50 (Origin: 0)
PASSED                                                                   [ 20%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_set_param_fallback
-------------------------------- live log call ---------------------------------
WARNING  modules.system.services.command_service:command_service.py:279 ROLLBACK: Used set() fallback for test_param (Registry not IRestorableRegistry). Lock state might be incorrect.
PASSED                                                                   [ 30%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_creation_restorable
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:266 ROLLBACK: Deleted new_param
PASSED                                                                   [ 40%]
tests/unit/modules/system/test_command_service_unit.py::test_dispatch_inject_money PASSED [ 50%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_inject_money
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:326 ROLLBACK: Burned 1000 from 1
PASSED                                                                   [ 60%]
tests/unit/modules/system/test_command_service_unit.py::test_commit_last_tick_clears_stack PASSED [ 70%]
tests/system/test_command_service_rollback.py::test_rollback_set_param_preserves_origin
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:270 ROLLBACK: Restored test_param to 100 (Origin: 0)
PASSED                                                                   [ 80%]
tests/system/test_command_service_rollback.py::test_rollback_set_param_deletes_new_key
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:266 ROLLBACK: Deleted new_param
PASSED                                                                   [ 90%]
tests/system/test_command_service_rollback.py::test_rollback_inject_asset
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:326 ROLLBACK: Burned 1000 from 101
PASSED                                                                   [100%]

============================== 10 passed in 0.46s ==============================
```

```
tests/integration/test_cockpit_integration.py::test_simulation_processes_pause_resume
-------------------------------- live log call ---------------------------------
INFO     simulation.engine:engine.py:121 Simulation PAUSED by command.
INFO     simulation.engine:engine.py:121 Simulation RESUMED by command.
PASSED                                                                   [ 33%]
tests/integration/test_cockpit_integration.py::test_simulation_processes_set_base_rate PASSED [ 66%]
tests/integration/test_cockpit_integration.py::test_simulation_processes_set_tax_rate PASSED [100%]

============================== 3 passed in 0.19s ===============================
```
