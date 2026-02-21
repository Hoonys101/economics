# Wave 7: Automate Mission Registration and Optimize Death System

## 1. [Architectural Insights]

### TD-DX-AUTO-CRYSTAL: Automated Mission Registration
- **Decision**: Migrated the static `GEMINI_MISSIONS` dictionary in `_internal/registry/gemini_manifest.py` to a dynamic registration system using the `@gemini_mission` decorator.
- **Implementation**: Created `_internal/registry/missions.py` to house the mission definitions using the decorator. `gemini_manifest.py` now imports this module and uses `mission_registry.to_manifest()` to populate `GEMINI_MISSIONS`.
- **Benefit**: This eliminates the need for manual JSON editing and allows mission definitions to be co-located with their logic or in dedicated modules, improving discoverability and maintainability.

### TD-SYS-PERF-DEATH: Optimized Death System
- **Decision**: Refactored `DeathSystem._handle_agent_liquidation` to eliminate the O(N) rebuilding of the `state.agents` dictionary.
- **Implementation**: Replaced `state.agents.clear()` and full rebuild with localized deletion (`del state.agents[agent_id]`) for only the agents that died.
- **Benefit**: This changes the complexity of death processing from O(N) (where N is total agents) to O(M) (where M is dead agents), which is significantly more efficient during mass liquidation events. It also preserves "System Agents" or other entities in `state.agents` that are not part of `state.households` or `state.firms`.

## 2. [Regression Analysis]

- **Existing Tests**: `tests/internal/test_mission_registry.py` and `tests/unit/systems/lifecycle/test_death_system.py` passed without modification, indicating that the changes are backward compatible.
- **New Tests**: `tests/unit/systems/lifecycle/test_death_system_performance.py` was added to verify the optimization. It specifically checks that unrelated agents ("ghost agents") are preserved in `state.agents`, proving that the dictionary is not being rebuilt from scratch.

## 3. [Test Evidence]

```
tests/internal/test_mission_registry.py::test_manual_registration PASSED [ 12%]
tests/internal/test_mission_registry.py::test_decorator_registration PASSED [ 25%]
tests/internal/test_mission_registry.py::test_decorator_static_instruction PASSED [ 37%]
tests/internal/test_mission_registry.py::test_scan_packages PASSED       [ 50%]
tests/internal/test_mission_registry.py::test_to_manifest PASSED         [ 62%]
tests/unit/systems/lifecycle/test_death_system.py::TestDeathSystem::test_firm_liquidation PASSED [ 75%]
tests/unit/systems/lifecycle/test_death_system.py::TestDeathSystem::test_firm_liquidation_cancels_orders PASSED [ 87%]
tests/unit/systems/lifecycle/test_death_system_performance.py::TestDeathSystemPerformance::test_localized_agent_removal PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 8 passed, 2 warnings in 0.36s =========================
```
