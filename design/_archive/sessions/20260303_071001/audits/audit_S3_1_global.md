# Forensic Audit Report: Global Test Setup [audit-mock-leak-global]

## Executive Summary
The forensic audit of `tests/conftest.py` reveals significant architectural risks primarily centered around global `sys.modules` poisoning and persistent singleton registries. While most fixtures are appropriately function-scoped, the import-time manipulation of the Python module cache and the lack of teardown for global registries (e.g., `GeminiMissionRegistry`) create a "Mock Pollution" environment that forces dependency-heavy tests (like those using `numpy`) into `XFAIL` states.

## Detailed Analysis

### 1. Persistent MagicMock References & Side-Effects
- **Status**: ⚠️ Partial (Fixture-level isolation exists, but module-level side-effects persist)
- **Evidence**: `tests/conftest.py:L15-56`
- **Findings**: 
    - The `sys.modules` loop at the top of `conftest.py` globally replaces 17+ libraries (including `numpy`, `yaml`, `pydantic`) with `MagicMock` instances if the real libraries are not found. 
    - **Risk**: This is a permanent side-effect for the entire test session. It prevents any test from selectively opting into real library behavior once the mock is injected into `sys.modules`.
    - **Observed Impact**: Existing `XFAIL` tests (e.g., `tests/integration/scenarios/test_scenario_runner.py`) explicitly cite `TD-ARCH-MOCK-POLLUTION` as the reason for failure because real math operations (Numpy) are replaced by non-functional mocks.

### 2. Global Registries and State Accumulation
- **Status**: ❌ Missing Reset Logic
- **Findings**:
    - **Gemini Mission Registry**: Located in `_internal/registry/api.py`, the `mission_registry` is a global singleton. Missions registered via decorators in one test file persist throughout the session.
    - **Fixed Command Registry**: Similarly, `fixed_registry` in `_internal/registry/fixed_commands.py` accumulates state at import time and is never cleared.
    - **Agent Registry**: Trace logs (`verification_output_3.txt:L384`) indicate a "Finalizing AgentRegistry state snapshot," suggesting that agents might be registered in a global list that is not explicitly reset in `conftest.py`.

### 3. 'Government' and 'Mock_Config' Interaction
- **Status**: ✅ Isolated but ⚠️ Mock Drift
- **Evidence**: `tests/conftest.py:L104-142` and `L175-190`
- **Findings**:
    - `government` and `mock_config` are function-scoped fixtures, ensuring fresh instances per test.
    - **Fixture Interaction**: `government` correctly injects `mock_config` into the `Government` constructor, and circular references (`gov.finance_system.government = gov`) are handled within the function scope.
    - **Mock Drift**: `mock_config` defines several attributes (e.g., `WEALTH_TAX_BRACKETS`, `DEBT_RISK_PREMIUM_TIERS`) that are labeled as "Legacy/Hidden" or "likely not in config.py". This creates a discrepancy between the test environment and production configuration.

## Risk Assessment
- **High Risk**: **Global Module Poisoning**. The `sys.modules` manipulation is the most severe technical debt. It violates the "Protocol Purity" guardrail by forcing mocks into the global namespace where `isinstance` checks against real types will fail.
- **Medium Risk**: **Registry Bloat**. The lack of a `pytest_runtest_teardown` hook to clear `mission_registry` and `AgentRegistry` means test order can affect results (flakiness).

## Regression Analysis
Existing tests (1160 passed) demonstrate that the current "Duct-Tape" mocking allows a majority of the suite to run, but at the cost of excluding high-fidelity simulation tests. The `XFAIL` markers on scenario tests are a direct consequence of the global mock leaks identified in this audit.

## Test Evidence
```text
tests/benchmarks/test_demographic_perf.py::test_demographic_manager_perf PASSED [  0%]
tests/common/test_protocol.py::TestProtocolShield::test_authorized_call PASSED [  0%]
...
tests/integration/scenarios/test_scenario_runner.py::TestScenarioRunner::test_run_scenario[/app/tests/integration/scenarios/definitions/gold_standard.json] XFAIL [  4%]
tests/integration/scenarios/test_scenario_runner.py::TestScenarioRunner::test_run_scenario[/app/tests/integration/scenarios/definitions/industrial_revolution.json] XFAIL [  4%]
...
tests/unit/utils/test_config_factory.py::test_create_config_dto_success PASSED [ 99%]
tests/unit/utils/test_config_factory.py::test_create_config_dto_missing_field PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

=========== 1160 passed, 11 skipped, 2 xfailed, 1 warning in 12.01s ============
```

## Conclusion
The global test setup is currently "poisoned" by design to support environment flexibility (missing libraries), but this has reached a point of diminishing returns where it blocks architectural integrity. 

**Recommended Action Items**:
1. Move `sys.modules` patching from global scope in `conftest.py` to a context-managed fixture that can be opted out of.
2. Implement a `pytest_sessionfinish` or `pytest_runtest_teardown` hook to clear `GeminiMissionRegistry` and `AgentRegistry`.
3. Synchronize `mock_config` with the actual `config.py` to prevent "Mock Drift".