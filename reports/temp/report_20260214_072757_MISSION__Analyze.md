I will begin by listing the files in `modules/system` and `config` to locate the implementations of the registry and config bridge, and then search for DTO definitions to identify any missing arguments.
I will examine the implementation of `GlobalRegistry` in `modules/system/registry.py` and the config bridge in `config/__init__.py` to address the regressions in `test_phase29_depression.py`, `test_config_bridge.py`, and `test_registry.py`.
In `config/__init__.py`, a `GlobalRegistry` is initialized, moving uppercase constants to it and using `__getattr__` for access. I need to investigate three regressions: "DTO 인자 누락" in `test_phase29_depression.py` (possibly a changed `SimulationInitializer` signature), a value mismatch in `test_config_bridge.py` where `config.TAX_RATE_BASE` might not be returning the updated registry value, and a "priority error" in `test_registry.py`. I'll start by checking the `OriginType` definition in `modules/system/api.py` and the `SimulationInitializer` signature in `simulation/initialization/initializer.py`.
`SimulationInitializer.__init__`'s signature matches its usage in `test_phase29_depression.py`, but the "DTO 인자 누락" error suggests a possible change in the `Firm` or `Household` constructors. In `test_config_bridge.py`, the value mismatch and "priority error" arise because `OriginType.CONFIG` (0) is lower than `OriginType.SYSTEM` (10), causing the registry to reject updates to `TAX_RATE_BASE` initially set with `SYSTEM` origin. This hierarchy—CONFIG < SYSTEM < USER < GOD_MODE—conflicts with the test's assumption that `CONFIG` is higher priority. I'll now check the `Household` and `Firm` constructors to resolve the DTO issue.
The `Household` and `Firm` constructors in `simulation/core_agents.py` and `simulation/firms.py` are complex, but since they're mocked in `test_phase29_depression.py`, the "DTO 인자 누락" error likely stems from how `DecisionInputDTO` is used or created, possibly within `Simulation.run_tick()`. In `test_config_bridge.py`, the mismatch occurs because `config/__init__.py` sets defaults with `OriginType.SYSTEM` (10), blocking the test's `OriginType.CONFIG` (0) updates; changing the default to `CONFIG` might be the fix. Similarly, `test_registry.py` fails because it incorrectly assumes `CONFIG` is higher priority than `SYSTEM`. I'll now examine `simulation/engine.py` to pinpoint the `DecisionInputDTO` issue.
`Simulation` hands off tick logic to `TickOrchestrator`, so I'll check `simulation/orchestration/tick_orchestrator.py` next.
`Phase1_Decision` is where agents decide, so I'll check `simulation/orchestration/phases/decision.py`.
Checking `simulation/orchestration/phases/decision.py`.
`DecisionInputFactory.create_decision_input` builds the `DecisionInputDTO`, so I'll check `simulation/orchestration/factories.py`.
`DecisionInputFactory.create_decision_input` creates a `DecisionInputDTO` with several fields, including `goods_data`, `market_data`, and `stress_scenario_config`. I'll now check the `DecisionInputDTO` definition in `simulation/dtos/api.py`.
`DecisionInputDTO` and `MacroFinancialContext` in `simulation/dtos/api.py` seem fine, and `Phase1_Decision` handles decision outputs correctly. The "DTO 인자 누락" error in `test_phase29_depression.py` doesn't appear to be in `SimulationInitializer` or the `Simulation` constructor. I'm now suspicious that a mandatory field was added to a DTO like `HouseholdStateDTO`, which `Household.create_state_dto()` might be missing. I'll check `modules/household/dtos.py` next.
`HouseholdSnapshotDTO` in `modules/household/dtos.py` has default values for its new fields, so that's likely not the cause of the "DTO 인자 누락" error. I've re-verified the `SimulationInitializer` signature, and it seems correct. To stop guessing, I'll run the tests using `run_shell_command` to see the actual error message.
I don't see `run_shell_command` in my tool set, even though the system instructions mention it. This is unexpected. I'll use `cli_help` to investigate the available tools.
Since I can't run shell commands, I'll use static analysis. I've re-verified `SimulationInitializer` in `simulation/initialization/initializer.py` and it lacks DTO arguments in `__init__`. I'll now check `simulation/initialization/api.py` to see if `SimulationInitializerInterface` has changed.
`SimulationInitializerInterface` and the `Simulation` constructor appear unchanged. I noticed `AgentRegistry` and `CommandService` are instantiated in `SimulationInitializer.build_simulation`, so I'll check the `CommandService` constructor in `modules/system/services/command_service.py` next.
`CommandService` constructor matches. I'll check the `PublicManager` constructor in `SimulationInitializer.build_simulation` next.
`CommandService`'s constructor is correct, and `HouseholdFactoryContext` appears properly instantiated in `SimulationInitializer`. I've verified the `Simulation` and `SimulationState` structures, yet the "DTO 인자 누락" error persists. I suspect a missing argument in a `DecisionInputDTO` call, so I'll search the codebase for all its usage to identify the discrepancy.
`DecisionInputDTO` isn't called in `test_phase29_depression.py`, so the error lies elsewhere. `SimulationInitializer` and `PublicManager` constructors are correct. I'll now check the `JudicialSystem` constructor in `modules/governance/judicial/system.py`.
`JudicialSystem` constructor matches. In `test_phase29_depression.py`, `sim.stress_scenario_config` is an instance of `ScenarioStrategy`. I'll now check the `ScenarioStrategy` definition in `simulation/dtos/strategy.py`.
`ScenarioStrategy` has defaults, so that's likely not the issue. `test_phase29_depression.py` mocks `config_module`, which might cause problems if `Simulation` or its components expect a specific structure. The "DTO 인자 누락" error is puzzling; I'll check `create_config_dto` in `simulation/utils/config_factory.py` to see if `HouseholdConfigDTO` is missing an argument.
`create_config_dto` raises an `AttributeError` if a required field is missing in `config_module`, which might be what's meant by "DTO 인자 누락." If `config_values` lacks a required argument for `dto_class.__init__`, a `TypeError` would result. I'll now examine `HouseholdConfigDTO` and `FirmConfigDTO` in `simulation/dtos/config_dtos.py` to identify any missing required fields.
`HouseholdConfigDTO` is missing several required fields in the `test_phase29_depression.py` mock, which likely causes the "DTO 인자 누락" error. I'll add these missing fields to the mock. To fix the priority issues in `test_config_bridge.py` and `test_registry.py`, I'll swap the values of `SYSTEM` and `CONFIG` in `OriginType` so that `CONFIG` has higher priority (SYSTEM=0, CONFIG=10). I'll also update `config/__init__.py` to use `OriginType.CONFIG`. I'm now checking for other code that might be affected by this change.
`OriginType.SYSTEM` currently overrides `OriginType.CONFIG`, which prevents user config files from overriding hardcoded defaults—a clear bug. Swapping them (`SYSTEM=0`, `CONFIG=10`) aligns with `test_registry.py` and fixes the mismatch in `test_config_bridge.py`. Additionally, `test_phase29_depression.py` is missing dozens of required fields for `HouseholdConfigDTO` and `FirmConfigDTO` in its mock setup, causing the "DTO 인자 누락" error. I'll swap the priorities in `modules/system/api.py`, update `config/__init__.py`, and then address the extensive mock updates needed in `test_phase29_depression.py`. I'll start by formalizing this plan with `sequentialthinking`.
`sequentialthinking` was denied, so I'll try `server-sequential-thinking__sequentialthinking` instead. If that fails, I'll proceed without the MCP.
I can't use `sequentialthinking`, and strangely, my toolset lacks `replace`, `write_file`, and `run_shell_command`, despite the instructions mentioning them. `desktop-commander` is listed in `GEMINI.md` but missing from my declarations. I'm stuck without the ability to modify files or run commands, so I'll consult `cli_help` again.
I now realize my role is **Technical Reporter**, strictly limited to auditing and reporting, with no authority to modify files or execute code. My analysis confirms that the "DTO 인자 누락" in `test_phase29_depression.py` stems from the `config_module` mock missing numerous mandatory attributes required by `HouseholdConfigDTO` and `FirmConfigDTO`, such as `TARGET_FOOD_BUFFER_QUANTITY` and `SURVIVAL_CRITICAL_TURNS`. The value mismatch and priority errors in `test_config_bridge.py` and `test_registry.py` are due to an incorrect `OriginType` hierarchy where `SYSTEM (10)` currently overrides `CONFIG (0)`. `config/__init__.py` uses `SYSTEM` for defaults, which blocks `CONFIG`-origin updates from tests and user files. I recommend swapping these priorities (`SYSTEM=0`, `CONFIG=10`) and updating the `test_phase29_depression.py` mock to align with the current DTO schemas.

```markdown
# System & Registry Regression Analysis Report

## Executive Summary
This report analyzes regressions in `test_phase29_depression.py`, `test_config_bridge.py`, and `test_registry.py`. The investigation identified a significant schema mismatch in test mocks and a fundamental priority inversion in the `OriginType` system that blocks configuration overrides.

## Detailed Analysis

### 1. [test_phase29_depression.py] DTO Argument Mismatch
- **Status**: ❌ Regression (Missing mandatory attributes)
- **Evidence**: `simulation/utils/config_factory.py:L21-25` raises `AttributeError` if mandatory DTO fields are missing in the config module.
- **Notes**: 
    - `test_phase29_depression.py` uses a `MagicMock` for `config_module` but only configures a subset of the fields required by the modern `HouseholdConfigDTO` and `FirmConfigDTO`.
    - Mandatory fields such as `TARGET_FOOD_BUFFER_QUANTITY`, `WAGE_DECAY_RATE`, `RESERVATION_WAGE_FLOOR`, and `PRIMARY_SURVIVAL_GOOD_ID` are missing from the mock setup (`L45-125`).
    - This causes `SimulationInitializer.build_simulation` to fail during DTO instantiation.

### 2. [test_config_bridge.py] Value Mismatch (0.1 vs 0.55)
- **Status**: ⚠️ Partial (Logic Rejection)
- **Evidence**: `modules/system/registry.py:L86-87` rejects updates if the new origin has lower priority than the current one.
- **Notes**: 
    - `config/__init__.py:L500-510` initializes parameters with `OriginType.SYSTEM` (Value 10).
    - `test_config_bridge.py:L23` attempts to update `TAX_RATE_BASE` using `OriginType.CONFIG` (Value 0).
    - Because `CONFIG (0) < SYSTEM (10)`, the registry rejects the update, causing the assertion `config.TAX_RATE_BASE == 0.55` to fail as it retains the original `0.1`.

### 3. [test_registry.py] Priority Logic Error
- **Status**: ❌ Missing (Implementation Mismatch)
- **Evidence**: `modules/system/api.py:L87-92` defines `CONFIG=0` and `SYSTEM=10`.
- **Notes**: 
    - The test `test_registry.py:L24-25` explicitly asserts that `CONFIG` is higher priority than `SYSTEM`: `# 2. Overwrite with CONFIG (Higher)`.
    - The actual implementation in `api.py` defines `SYSTEM` as higher than `CONFIG`, which directly contradicts the test's architectural assumption and the requirements for user-driven configuration overrides.

## Risk Assessment
- **Priority Inversion**: Currently, internal system defaults (`SYSTEM`) cannot be overridden by file-based configurations (`CONFIG`). This prevents users from tuning the simulation via YAML files if the registry is initialized with `SYSTEM` origin.
- **Test Maintenance**: Extensive growth of `HouseholdConfigDTO` and `FirmConfigDTO` without corresponding updates to system-level test mocks has rendered several critical tests unrunnable.

## Conclusion
The regressions are primarily due to **Architectural Priority Inversion** in the Registry and **Schema Drift** in the test suites. 

**Action Items:**
1.  **Swap Priorities**: Update `modules/system/api.py` to set `SYSTEM = 0` and `CONFIG = 10` to allow configuration files to override internal defaults.
2.  **Schema Alignment**: Update `test_phase29_depression.py` to include all mandatory fields identified in `simulation/dtos/config_dtos.py`.
3.  **Registry Initialization**: Change `config/__init__.py` to use `OriginType.SYSTEM` (the new lowest priority) for initial constant loading.
```