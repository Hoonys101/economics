# Insight Report: Fix Core Simulation Initialization

## Architectural Insights

### 1. Command Processing Strategy
A critical architectural decision was made regarding `Simulation._process_commands`. Initially, there was a risk of "Double Execution" where commands were executed in `_process_commands` and then re-enqueued for `Phase0_Intercept` to execute again.

To resolve this while adhering to the specification that `Simulation` must use the injected `CommandService`, the following strategy was implemented:
- **Immediate Execution**: `Simulation._process_commands` now drains both the external `command_queue` and internal `god_command_queue`.
- **Atomic Batching**: It aggregates these commands and executes them via `self.command_service.execute_command_batch`.
- **Baseline Integrity**: The result of the batch execution (specifically `m2_delta`) is used to immediately update `self.world_state.baseline_money_supply`.
- **No Re-enqueue**: Executed commands are **NOT** put back into `god_command_queue`. This prevents `Phase0_Intercept` (which runs later in `TickOrchestrator`) from re-executing them. `Phase0_Intercept` will simply find an empty queue and pass.

This approach satisfies strict causality (commands happen before tick logic) and financial integrity (M2 baseline is updated), while fixing the `NameError` and "Dead Dependency" issues.

### 2. Dependency Injection
`CommandService` is now treated as a core system component, instantiated early in `SimulationInitializer` and injected into `Simulation`. This follows the pattern used for `GlobalRegistry` and `SettlementSystem`.

### 3. Test Alignment
Integration tests (`test_cockpit_integration.py`) were updated to reflect the new behavior. Previously, they asserted that commands were *forwarded* to the queue. Now, they assert that commands are *executed* (by verifying calls to the mocked `CommandService`).

## Test Evidence

### `tests/integration/test_wo058_production.py`
```
tests/integration/test_wo058_production.py::test_bootstrapper_injection
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.bootstrapper:bootstrapper.py:97 BOOTSTRAPPER | Injected 50.0 units to Firm 100
INFO     simulation.systems.bootstrapper:bootstrapper.py:107 BOOTSTRAPPER | Injected 9999500 capital to Firm 100 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:97 BOOTSTRAPPER | Injected 50.0 units to Firm 101
INFO     simulation.systems.bootstrapper:bootstrapper.py:107 BOOTSTRAPPER | Injected 9997500 capital to Firm 101 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:113 BOOTSTRAPPER | Injected resources into 1 firms.
INFO     simulation.systems.bootstrapper:bootstrapper.py:55 BOOTSTRAPPER | Force-assigned 1 workers to Firm 100
INFO     simulation.systems.bootstrapper:bootstrapper.py:55 BOOTSTRAPPER | Force-assigned 0 workers to Firm 101
INFO     simulation.systems.bootstrapper:bootstrapper.py:57 BOOTSTRAPPER | Total force-assigned workers: 1
PASSED                                                                   [ 50%]
tests/integration/test_wo058_production.py::test_production_kickstart
-------------------------------- live log call ---------------------------------
INFO     simulation.systems.bootstrapper:bootstrapper.py:97 BOOTSTRAPPER | Injected 50.0 units to Firm 100
INFO     simulation.systems.bootstrapper:bootstrapper.py:107 BOOTSTRAPPER | Injected 9997000 capital to Firm 100 via Settlement.
INFO     simulation.systems.bootstrapper:bootstrapper.py:113 BOOTSTRAPPER | Injected resources into 1 firms.
INFO     simulation.systems.bootstrapper:bootstrapper.py:55 BOOTSTRAPPER | Force-assigned 1 workers to Firm 100
INFO     simulation.systems.bootstrapper:bootstrapper.py:57 BOOTSTRAPPER | Total force-assigned workers: 1
PASSED                                                                   [100%]
```

### `tests/integration/test_cockpit_integration.py`
```
tests/integration/test_cockpit_integration.py::test_simulation_processes_pause_resume
-------------------------------- live log call ---------------------------------
INFO     simulation.engine:engine.py:121 Simulation PAUSED by command.
INFO     simulation.engine:engine.py:121 Simulation RESUMED by command.
PASSED                                                                   [ 33%]
tests/integration/test_cockpit_integration.py::test_simulation_processes_set_base_rate PASSED [ 66%]
tests/integration/test_cockpit_integration.py::test_simulation_processes_set_tax_rate PASSED [100%]
```

### `tests/unit/test_tax_incidence.py`
```
tests/unit/test_tax_incidence.py::TestTaxIncidence::test_firm_payer_scenario
-------------------------------- live log call ---------------------------------
INFO     simulation.agents.government:government.py:163 Government 999 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
PASSED                                                                   [ 50%]
tests/unit/test_tax_incidence.py::TestTaxIncidence::test_household_payer_scenario
-------------------------------- live log call ---------------------------------
INFO     simulation.agents.government:government.py:163 Government 999 initialized with assets: defaultdict(<class 'int'>, {'USD': 0})
PASSED                                                                   [100%]
```