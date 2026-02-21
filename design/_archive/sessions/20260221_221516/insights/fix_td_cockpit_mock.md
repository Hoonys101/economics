# Insight Report: TD-TEST-COCKPIT-MOCK Resolution

## 1. Architectural Insights

The resolution of `TD-TEST-COCKPIT-MOCK` involved modernizing the test infrastructure to align with the "Stateless Engine Orchestration" pattern and strict DTO compliance.

### Key Decisions:
*   **SimulationStateBuilder**: A strict builder pattern (`modules/testing/utils.py`) was introduced to construct `SimulationState` instances. This enforces DTO purity by requiring valid inputs for all fields defined in `simulation/dtos/api.py`. This prevents "Mock Drift" where tests rely on ad-hoc attributes that do not exist in the actual DTO.
*   **Strict Mocking (spec=WorldState)**: Tests orchestrating the simulation tick (`TickOrchestrator`) were updated to use `MagicMock(spec=WorldState)`. This ensures that any attempt by the production code to access non-existent attributes on the `WorldState` mock raises an `AttributeError`, exposing potential bugs or out-of-sync tests immediately.
*   **Command Pipeline Alignment**: The deprecated `system_command_queue` attribute was definitively replaced with `system_commands` (List) and `god_command_queue` (deque) in all verified test mocks, reflecting the current architecture of `TickOrchestrator`.

### Technical Debt Retired:
*   Tests in `tests/modules/governance/test_cockpit_flow.py` no longer construct `SimulationState` using loose `MagicMock`, preventing silent failures if the DTO structure changes.
*   Tests in `tests/integration/test_tick_normalization.py` and `tests/orchestration/test_state_synchronization.py` now strictly validate the `WorldState` interface, ensuring that the orchestrator's dependencies are correctly modeled.

## 2. Regression Analysis

### Issues Identified & Fixed:
*   **Mock Drift in Tick Normalization**: `tests/integration/test_tick_normalization.py` previously disabled strict mocking (`# Remove spec=WorldState`). Re-enabling `spec=WorldState` revealed multiple missing dependencies in the mock setup (`stock_tracker`, `lifecycle_manager`, `global_registry`, etc.), which were causing silent assumptions in `TickOrchestrator` logic. These were explicitly added to the mock setup.
*   **Global Registry Dependency**: `Phase0_Intercept` enforces the presence of `global_registry` on `WorldState` (FOUND-03). The legacy mock in `test_tick_normalization.py` missed this, which would have caused runtime failures in a real environment. This was fixed by adding `state.global_registry = MagicMock()`.

### Alignment Verification:
*   The refactored tests now accurately reflect the `TickOrchestrator`'s expectation of `WorldState` structure, ensuring that future changes to `WorldState` will break these tests if not properly updated, rather than failing silently.

## 3. Test Evidence

```
tests/modules/governance/test_cockpit_flow.py::test_cockpit_command_flow_tax_rate
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:74 CommandService received CockpitCommand: SET_TAX_RATE
INFO     simulation.engine:engine.py:163 System Commands Queued for Tick 1: 1
INFO     simulation.orchestration.phases.system_commands:system_commands.py:29 SYSTEM_COMMANDS_PHASE | Processing 1 commands.
INFO     modules.governance.processor:processor.py:28 SYSTEM_COMMAND | Executing SET_TAX_RATE
INFO     modules.governance.processor:processor.py:66 SYSTEM_COMMAND | Corporate Tax Rate: 0.2 -> 0.35
PASSED                                                                   [ 20%]
tests/modules/governance/test_cockpit_flow.py::test_cockpit_command_flow_pause
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:74 CommandService received CockpitCommand: PAUSE
INFO     simulation.engine:engine.py:147 Simulation PAUSED by CommandService.
PASSED                                                                   [ 40%]
tests/orchestration/test_state_synchronization.py::TestStateSynchronization::test_transient_queue_accumulation PASSED [ 60%]
tests/orchestration/test_state_synchronization.py::TestStateSynchronization::test_reassignment_guardrail PASSED [ 80%]
tests/integration/test_tick_normalization.py::TestTickNormalization::test_run_tick_executes_phases PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 5 passed, 2 warnings in 0.30s =========================
```
