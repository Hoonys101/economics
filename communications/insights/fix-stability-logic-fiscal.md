# [ARCHITECTURAL INSIGHTS] Fix Stability Logic & Fiscal Policy

## 1. Dependency Injection Mismatch in Simulation Engine
**Issue:** `Simulation` engine initialization evolved to strictly require `IGlobalRegistry`, `ISettlementSystem`, and `IAgentRegistry`, but legacy tests were instantiating `Simulation` with old signatures.
**Resolution:** Updated `tests/system/test_engine.py` and `tests/integration/test_cockpit_integration.py` to inject required mocks.
**Insight:** Future changes to `Simulation` constructor MUST be accompanied by updates to `tests/conftest.py` or relevant test fixtures to prevent widespread test failures. `SimulationInitializer` pattern is robust, but direct instantiation in tests bypasses it.

## 2. CommandService API & Control Flow
**Issue:** `Simulation` engine relied on `pop_commands()` which was removed from `CommandService` during a refactor towards `execute_command_batch`.
**Resolution:** Re-introduced an internal `_command_queue` and `pop_commands()` to `CommandService` to bridge the gap between legacy polling-based engine logic and the new batch execution model.
**Insight:** The "Engine Control" commands (PAUSE, RESUME) and "God Mode" commands (SET_PARAM) are currently mixed. A cleaner separation might be needed where `Simulation` handles controls and delegates state mutation to `CommandService` completely.

## 3. Fiscal Policy & Mock Synchronization
**Issue:** `test_debt_ceiling_enforcement` failed because a side-effect mock for `issue_bonds` updated the `wallet` but not the `settlement_system` mock balance, leading to a discrepancy where the agent had cash but the spending logic (checking settlement) saw zero funds.
**Resolution:** Updated the side-effect to synchronize both mocks.
**Insight:** When mocking complex interactions between `Wallet` and `SettlementSystem`, ensure consistency. If `SettlementSystem` is the source of truth for funds, mocks must reflect transfers immediately.

## 4. Asyncio Testing Infrastructure
**Issue:** `pytest-asyncio` was missing from the environment, causing async tests to fail or be ignored.
**Resolution:** Installed `pytest-asyncio` and `websockets`, and updated `pytest.ini` with `asyncio_default_fixture_loop_scope = function` to comply with recent library versions.
**Insight:** `pytest.ini` markers are insufficient if the underlying plugin is not installed. Explicit dependency management is crucial for test stability.

[TEST EVIDENCE]
============================== 9 passed in 0.77s ===============================
============================== 3 passed in 0.21s ===============================
============================== 5 passed in 0.18s ===============================
============================== 2 passed in 2.99s ===============================
