--- SOURCE INFO ---
Branch: origin/fix-economic-integrity-audit-10441277727287694437
Score: 150
File Date: 2026-02-19 16:17:53
Harvested: 2026-02-20 07:18:26
---

I will begin by searching for occurrences of the deprecated `system_command_queue` attribute within the `tests/` directory to identify mock setups that require updating.
I will examine the `test_failure.txt` and `last_failure.txt` files to identify any `AttributeError` related to the `WorldState` mock regressions.
I will now check `last_failure.txt` to see if it contains any information regarding the `system_command_queue` issue.
I will examine `modules/system/services/command_service.py` to determine if `_system_command_queue` has been deprecated.
I will now read `modules/system/services/command_service.py` to check for the presence of `_system_command_queue`.
I have confirmed that `WorldState.system_commands` is the new attribute name, replacing the deprecated `system_command_queue`. I will now re-examine `tests/orchestration/test_state_synchronization.py` to address the instances where `system_command_queue` is still being used.
I have confirmed that `ws.system_command_queue = []` at line 31 of `tests/orchestration/test_state_synchronization.py` is incorrect and must be updated to `ws.system_commands = []`. I will now proceed to verify `tests/integration/test_tick_normalization.py`.
In `tests/integration/test_tick_normalization.py`, `state.system_command_queue = deque()` at line 65 is incorrect and should be updated to `state.system_commands = []`. While `state.system_commands` being a `MagicMock` might avoid a crash in `TickOrchestrator.run_tick()`, it remains technically incorrect. I've also confirmed that `god_command_queue` and `command_queue` setups in this file are correct. I will now proceed to review `tests/integration/test_cockpit_integration.py`.
In `tests/integration/test_cockpit_integration.py`, `world_state.god_command_queue` is correctly set as a `deque()`. However, `system_commands` is missing from `mock_simulation_deps`, which could cause issues if `Simulation.run_tick()` or `_process_commands` tries to access it. I'll now examine `Simulation.run_tick()` in `simulation/engine.py` to confirm.
In `Simulation._process_commands`, I've noted that while `MagicMock` might prevent crashes, tests verifying `system_commands` should explicitly check `world_state.system_commands`. I've already identified two incorrect usages of `system_command_queue` in `tests/orchestration/test_state_synchronization.py` and `tests/integration/test_tick_normalization.py`. Now, I'll examine `SimulationState` mocks and use `grep_search` to check for any `god_command_queue` mismatches.
I'll now examine `system_commands` usage in the `tests/` directory to check for any inconsistencies.
`tests/integration/test_tick_normalization.py` and `tests/orchestration/test_state_synchronization.py` are using the deprecated `system_command_queue`, while `test_cockpit_flow.py` and `test_lifecycle_cycle.py` are updated to `system_commands`. I've noted that `SimulationState` in `test_engine.py` is missing these attributes, though they have default factories. I'll now search for any remaining `system_command_queue` references in the codebase.
`CommandService` correctly uses `_system_command_queue` internally, but `WorldState` has been renamed to `system_commands`, leaving `tests/orchestration/test_state_synchronization.py` and `tests/integration/test_tick_normalization.py` outdated. I've also noted that `WorldState` uses `god_command_queue` while the `SimulationState` DTO uses `god_commands`. I'll now examine the `SimulationState` DTO in `api.py`.
I have verified that `WorldState` uses `system_commands` and `god_command_queue`, while `SimulationState` uses `system_commands` and `god_commands`. I've identified two instances in `tests/` where `system_command_queue` is incorrectly used on `WorldState` mocks. Now, I'll search for `god_commands` in `tests/` to check for any mismatches between `WorldState` and `SimulationState` usage.
I'll check `tests/unit/simulation/orchestration/phases/test_intercept.py` to determine if `state` is a `WorldState` or `SimulationState` instance.
In `test_intercept.py`, `state.god_commands` correctly mocks `SimulationState`. However, `WorldState` uses `god_command_queue` (a deque) and `system_commands` (a list), while `SimulationState` uses `god_commands` and `system_commands`. I've confirmed that `tests/orchestration/test_state_synchronization.py` and `tests/integration/test_tick_normalization.py` incorrectly use `system_command_queue` for `WorldState` mocks. Notably, `test_tick_normalization.py` also uses the wrong type (deque instead of list) for what should be `system_commands`. I'll now search for `command_queue` in `tests/` to identify any further inconsistencies.
`command_queue` is for external commands and is present in `WorldState` but not in the `SimulationState` DTO, which correctly only has drained commands. I've confirmed that `test_intercept.py` correctly omits `command_queue` when mocking `SimulationState`. I found an `AttributeError` in `test_engine.py`, but it's unrelated to `system_command_queue`. I'll now check `diagnostic_output.txt` for any other relevant error patterns.
The `diagnostic_output.txt` file indicates money leaks, which are unrelated to the `system_command_queue` attribute regression. My audit confirms that `WorldState` correctly uses `system_commands` (list) and `god_command_queue` (deque), while the `SimulationState` DTO uses `system_commands` and `god_commands`. I've identified two files, `tests/orchestration/test_state_synchronization.py` and `tests/integration/test_tick_normalization.py`, that use the deprecated `system_command_queue` name and, in the latter case, the wrong type (deque). I've also noted that while `MagicMock` might prevent immediate crashes, these tests are essentially bypassing the intended logic. I'll now proceed to create the insight report.
I've noted the mismatch between `system_command_queue` and `system_commands` and identified the specific lines in the test files that need updating. I also observed the naming difference for "god" commands between `WorldState` and `SimulationState`. While I can't modify the filesystem directly, I'll provide the content for the required insight report and the final technical report in my response. I've also noted an unrelated `AttributeError` in `test_engine.py` and will now locate `AgentLifecycleManager` to investigate it further.
`AgentLifecycleManager` has been decomposed into `AgingSystem`, `BirthSystem`, and `DeathSystem`. Despite a specification mentioning `_handle_agent_liquidation` within `AgentLifecycleManager.execute`, a test reports an `AttributeError` for that same attribute. I'll now examine `simulation/systems/lifecycle_manager.py` to clarify its current structure.
`AgentLifecycleManager` no longer contains `_handle_agent_liquidation`, as its functionality has been refactored into `DeathSystem` and `LiquidationManager`. This has caused an `AttributeError` in `test_engine.py`. Furthermore, `WorldState` now uses `governments` (plural), but the `SimulationState` DTO and `TickOrchestrator` still refer to `government` (singular). This discrepancy suggests a stale reference or a bug in `TickOrchestrator`. I'll now re-examine `world_state.py` to see if a `government` property exists.
`WorldState` lacks a `government` property, yet `TickOrchestrator` and `SimulationState` still use the singular `government`. This is a clear mismatch since `WorldState` now uses `governments` (plural). I'll now examine `simulation/orchestration/tick_orchestrator.py` to see how it addresses this discrepancy.
`TickOrchestrator` frequently accesses `state.government`, which is problematic if `WorldState` only contains `governments` (plural). This mismatch could mean `WorldState` is missing a backward-compatibility property, or it could simply be a bug. Given that `Simulation.__getattr__` delegates to `world_state`, any missing attribute will cause a failure. I'll re-examine `world_state.py` specifically for any dynamic attribute handling or properties that might resolve this.
`WorldState` lacks a `government` attribute, yet `TickOrchestrator` uses it. This suggests that `Simulation.__setattr__` might be dynamically adding `government` to `world_state` when `sim.government` is set. I'll now examine `SimulationInitializer` to confirm if and how it initializes `government`.
I'm going to read `simulation/initialization/initializer.py`.
`SimulationInitializer.build_simulation` sets `sim.government`, which, via `Simulation.__setattr__`, also sets `sim.world_state.government`. This means `WorldState` dynamically acquires a singular `government` attribute alongside its plural `governments` list. I'll now check `initializer.py` for where the `governments` list is populated.
`WorldState.governments` appears to be initialized as an empty list and may remain so, potentially breaking `resolve_agent_id`. Meanwhile, `SimulationState` continues to use the singular `government`. My primary focus remains the `Cockpit 2.0` refactor, specifically the `system_command_queue` to `system_commands` transition. I've noted an unrelated `AttributeError` in `test_engine.py` and will now check `test_results.txt` for any other relevant error patterns.
The failures in `test_transaction_handlers.py` stem from the deprecation of `collect_tax` in favor of `settle_atomic`, not the `system_command_queue` issue. My audit identified `system_command_queue` regressions in `tests/orchestration/test_state_synchronization.py` and `tests/integration/test_tick_normalization.py`, along with inconsistencies in `government`/`governments` naming and `god_commands`/`god_command_queue` usage. I also noted an `AttributeError` in `test_engine.py` related to the `AgentLifecycleManager` refactor. I'm now ready to generate the final report.

# Systemic Audit: Mock Attribute Regressions (Cockpit 2.0)

## Executive Summary
A systemic audit of the `tests/` directory revealed multiple regressions where `MagicMock` setups for `WorldState` still utilize deprecated attribute names from the Cockpit 1.0 era. Specifically, `system_command_queue` is used instead of the new `system_commands` list, leading to "silent" test failures where cockpit interventions are ignored by the `TickOrchestrator`.

## Detailed Analysis

### 1. [System Command Pipeline]
- **Status**: ❌ Missing / Stale in Mocks
- **Evidence**: 
    - `tests\orchestration\test_state_synchronization.py:L31`: `ws.system_command_queue = []`
    - `tests\integration\test_tick_normalization.py:L65`: `state.system_command_queue = deque()`
- **Notes**: Production code in `world_state.py:L116` renamed this to `self.system_commands`. The use of `deque` in mocks also mismatches the production `List` type.

### 2. [God Command Pipeline]
- **Status**: ⚠️ Partial / Naming Mismatch
- **Evidence**: 
    - `world_state.py:L117`: `self.god_command_queue: deque`
    - `simulation\dtos\api.py:L268`: `god_commands: List[GodCommandDTO]`
- **Notes**: While correct on `WorldState` mocks, the mismatch between `god_command_queue` (State) and `god_commands` (DTO) causes confusion during `SimulationState` construction in `TickOrchestrator`.

### 3. [Government Reference]
- **Status**: ⚠️ Inconsistent
- **Evidence**: `world_state.py:L89` shows `self.governments: List[Government]`, but `TickOrchestrator` and many tests still access `state.government` (singular).
- **Notes**: This currently relies on dynamic attribute setting during initialization, which is fragile for unit tests.

## Risk Assessment
- **Silent Coverage Loss**: Since `TickOrchestrator` drains `system_commands` (New), it ignores the `system_command_queue` (Old) defined in mocks. Tests pass but do not actually verify command processing.
- **Type Mismatches**: `TickOrchestrator` expects `system_commands` to be a `List`. Mocks providing `deque` may cause issues if `list.extend()` logic is bypassed or if specific list methods are expected.

## Conclusion
The test suite requires immediate modernization of `WorldState` mocks. The primary focus should be renaming `system_command_queue` to `system_commands` and ensuring `god_command_queue` is properly initialized as a `deque` to support atomic `popleft()` operations.

---
**Technical Reporter Note**: An unrelated regression was identified in `tests\system\test_engine.py:L823` where `AgentLifecycleManager` is accessed via the stale private method `_handle_agent_liquidation`, which has been refactored into `DeathSystem`.