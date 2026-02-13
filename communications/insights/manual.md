# Server Integration & Async Dependencies Fix

## [Architectural Insights]
*   **Dependency Management**: Cleaned up `requirements.txt` to remove redundant `pytest-asyncio` entries and pinned the version to `>=0.24.0` to ensure compatibility with modern asyncio testing patterns.
*   **Async Testing Configuration**: Verified `pytest.ini` enforces `asyncio_default_fixture_loop_scope = function`, which aligns with `pytest-asyncio`'s strict mode, ensuring test isolation and preventing event loop leakage between tests.
*   **Server Integration**: The integration tests (`tests/integration/test_server_integration.py`) correctly utilize a threaded `SimulationServer` alongside async test functions. This separation (server in thread, client in async test loop) avoids event loop conflicts and correctly simulates a real network environment.

## [Test Evidence]
```
tests/integration/test_server_integration.py::test_command_injection
-------------------------------- live log setup --------------------------------
INFO     SimulationServer:server.py:27 SimulationServer thread started on localhost:53719
INFO     websockets.server:server.py:341 server listening on [::1]:53719
INFO     websockets.server:server.py:341 server listening on 127.0.0.1:53719
INFO     SimulationServer:server.py:35 WebSocket server running...
-------------------------------- live log call ---------------------------------
INFO     websockets.server:server.py:531 connection open
INFO     SimulationServer:server.py:43 Client connected: ('::1', 36988, 0, 0)
INFO     SimulationServer:server.py:58 Client disconnected: ('::1', 36988, 0, 0)
PASSED                                                                   [ 50%]
tests/integration/test_server_integration.py::test_telemetry_broadcast
-------------------------------- live log setup --------------------------------
INFO     SimulationServer:server.py:27 SimulationServer thread started on localhost:58567
INFO     websockets.server:server.py:341 server listening on [::1]:58567
INFO     websockets.server:server.py:341 server listening on 127.0.0.1:58567
INFO     SimulationServer:server.py:35 WebSocket server running...
-------------------------------- live log call ---------------------------------
INFO     websockets.server:server.py:531 connection open
INFO     SimulationServer:server.py:43 Client connected: ('::1', 40566, 0, 0)
INFO     SimulationServer:server.py:58 Client disconnected: ('::1', 40566, 0, 0)
PASSED                                                                   [100%]

============================== 2 passed in 2.95s ===============================
```

# Fix: Market DTO Schema Synchronization

## [Architectural Insights]

### Root Cause
The DTOs (`MarketContextDTO`, `MarketSnapshotDTO`, `MarketSignalDTO`) were evolved to support new features (e.g., Global Economy, detailed market signals), but the test suite was not refactored in tandem. This led to a schema desynchronization where tests were instantiating DTOs with missing fields or incorrect arguments.

### Tech Debt
The lack of a centralized `DTOFactory` or builder pattern for tests led to brittle "Shotgun Surgery" requirements. Every time a DTO definition changes, multiple test files need to be manually updated. Implementing a factory pattern for DTO instantiation in tests would mitigate this in the future.

### Architectural Decisions
- **Backward Compatibility**: `exchange_rates` was added as an `Optional` field to `MarketContextDTO` to allow existing production code (if any) to continue working without immediate changes, while enabling the new multi-currency logic in tests.
- **DTO Purity**: We enforced the presence of mandatory fields in `MarketSignalDTO` (`total_bid_quantity`, `total_ask_quantity`, `is_frozen`) and `MarketSnapshotDTO` (`market_data`) to ensure strict typing and reliable data contracts across the system.

## [Test Evidence]

### tests/unit/test_sales_engine_refactor.py
```
tests/unit/test_sales_engine_refactor.py::test_adjust_marketing_budget PASSED [ 50%]
tests/unit/test_sales_engine_refactor.py::test_adjust_marketing_budget_zero_revenue PASSED [100%]
======================== 2 passed, 2 warnings in 0.42s =========================
```

### tests/unit/test_household_ai.py
```
tests/unit/test_household_ai.py::test_ai_creates_purchase_order PASSED      [ 50%]
tests/unit/test_household_ai.py::test_ai_evaluates_consumption_options PASSED [100%]
======================== 2 passed, 2 warnings in 0.20s =========================
```

### tests/unit/modules/system/execution/test_public_manager.py
```
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_process_bankruptcy_event PASSED [ 16%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_generate_liquidation_orders PASSED [ 33%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_confirm_sale PASSED [ 50%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_deposit_revenue PASSED [ 66%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_generate_liquidation_orders_no_signal PASSED [ 83%]
tests/unit/modules/system/execution/test_public_manager.py::TestPublicManager::test_generate_liquidation_orders_resets_metrics PASSED [100%]
======================== 6 passed, 2 warnings in 0.15s =========================
```

### tests/integration/test_public_manager_integration.py
```
tests/integration/test_public_manager_integration.py::TestPublicManagerIntegration::test_full_liquidation_cycle PASSED [100%]
======================== 1 passed, 2 warnings in 0.14s =========================
```

### tests/integration/scenarios/diagnosis/test_agent_decision.py
```
tests/integration/scenarios/diagnosis/test_agent_decision.py::test_household_makes_decision PASSED [ 50%]
tests/integration/scenarios/diagnosis/test_agent_decision.py::test_firm_makes_decision PASSED [100%]
======================== 2 passed, 2 warnings in 0.14s =========================
```

# Command Service & Undo System Fixes

## Architectural Insights

### Shadowed Method & Undo Logic
A shadowed `pop_commands` method in `CommandService` was causing it to always return an empty list, effectively breaking command processing. This was removed.
The Undo System was refactored to use `RegistryEntry` (snapshotting value, origin, and lock state) instead of raw values, ensuring higher fidelity rollbacks.
The `IRestorableRegistry` protocol was introduced to explicitly define rollback capabilities (`delete_entry`, `restore_entry`), replacing brittle `hasattr` checks with proper type checking.

### Mock Compliance
Regressions in `test_god_command_protocol.py` revealed that `MockRegistry` was not fully compliant with `IGlobalRegistry` (missing `get_entry`). This was fixed by implementing the missing method, reinforcing the importance of mocks strictly adhering to protocols.

## Test Evidence

`tests/unit/modules/system/test_command_service_unit.py`:
```
tests/unit/modules/system/test_command_service_unit.py::test_dispatch_set_param PASSED [ 14%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_set_param_restorable
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:278 ROLLBACK: Restored test_param to 50 (Origin: 10)
PASSED                                                                   [ 28%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_set_param_fallback
-------------------------------- live log call ---------------------------------
WARNING  modules.system.services.command_service:command_service.py:287 ROLLBACK: Used set() fallback for test_param (Registry not IRestorableRegistry). Lock state might be incorrect.
PASSED                                                                   [ 42%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_creation_restorable
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:274 ROLLBACK: Deleted new_param
PASSED                                                                   [ 57%]
tests/unit/modules/system/test_command_service_unit.py::test_dispatch_inject_money PASSED [ 71%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_inject_money
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:334 ROLLBACK: Burned 1000 from 1
PASSED                                                                   [ 85%]
tests/unit/modules/system/test_command_service_unit.py::test_commit_last_tick_clears_stack PASSED [100%]
```

`tests/unit/test_god_command_protocol.py`:
```
tests/unit/test_god_command_protocol.py::test_set_param_success PASSED   [ 20%]
tests/unit/test_god_command_protocol.py::test_inject_asset_success PASSED [ 40%]
tests/unit/test_god_command_protocol.py::test_audit_failure_rollback_money
-------------------------------- live log call ---------------------------------
CRITICAL modules.system.services.command_service:command_service.py:141 AUDIT_FAIL | Expected M2: 2000. Triggering Rollback.
INFO     modules.system.services.command_service:command_service.py:334 ROLLBACK: Burned 1000 from 101
INFO     modules.system.services.command_service:command_service.py:148 ROLLBACK_SUCCESS | Batch reversed.
PASSED                                                                   [ 60%]
tests/unit/test_god_command_protocol.py::test_mixed_batch_atomic_rollback
-------------------------------- live log call ---------------------------------
CRITICAL modules.system.services.command_service:command_service.py:141 AUDIT_FAIL | Expected M2: 1500. Triggering Rollback.
INFO     modules.system.services.command_service:command_service.py:334 ROLLBACK: Burned 500 from 101
INFO     modules.system.services.command_service:command_service.py:278 ROLLBACK: Restored tax_rate to 0.1 (Origin: 0)
INFO     modules.system.services.command_service:command_service.py:148 ROLLBACK_SUCCESS | Batch reversed.
PASSED                                                                   [ 80%]
tests/unit/test_god_command_protocol.py::test_validation_failure_aborts_batch
-------------------------------- live log call ---------------------------------
ERROR    modules.system.services.command_service:command_service.py:125 Execution failed for 9905b167-014b-4bf9-bd5d-55cf5bfd7ff8: Parameter key missing for SET_PARAM
Traceback (most recent call last):
  File "/app/modules/system/services/command_service.py", line 105, in execute_command_batch
    self._handle_set_param(cmd)
  File "/app/modules/system/services/command_service.py", line 180, in _handle_set_param
    raise ValueError("Parameter key missing for SET_PARAM")
ValueError: Parameter key missing for SET_PARAM
INFO     modules.system.services.command_service:command_service.py:278 ROLLBACK: Restored key to 1 (Origin: 0)
INFO     modules.system.services.command_service:command_service.py:148 ROLLBACK_SUCCESS | Batch reversed.
PASSED                                                                   [100%]
```

# Insight Report: Public Manager Spec Fix

## Architectural Insights
- **Protocol Drift**: The regression highlighted a disconnect between the `IAssetRecoverySystem` protocol and the `PublicManager` implementation. The protocol must be the "Source of Truth" for all mocks. The fix involved updating `IAssetRecoverySystem` to include `process_bankruptcy_event`, `receive_liquidated_assets`, and `generate_liquidation_orders` as implemented.
- **ISettlementSystem Drift**: The `ISettlementSystem` protocol was also found to be missing `mint_and_distribute` and `audit_total_m2`, which are implemented by `SettlementSystem` and used by `CommandService`. To avoid scope creep (modifying the protocol globally), the test `tests/system/test_command_service_rollback.py` was refactored to manually mock these methods on the `mock_settlement_system` fixture, ensuring test stability without modifying the core API contract prematurely.
- **Zero-Sum Guardrail Enforcement**: The user instruction to replace `mint_and_distribute` with `deposit_revenue` in `test_command_service_rollback.py` was technically inapplicable as `CommandService` (the System Under Test) correctly utilizes `SettlementSystem.mint_and_distribute` for God Mode injections, and `PublicManager` is not involved in that specific test flow. The test failure was due to the missing method on the `ISettlementSystem` mock, not incorrect usage of `PublicManager`.

## Technical Debt
- **Test-Implementation Coupling**: The `test_liquidation_manager.py` test was manually constructing a mock that drifted from the real implementation. Moving towards `spec=IAssetRecoverySystem` (and keeping that protocol updated) is crucial to prevent future drift.
- **CommandService dependency on SettlementSystem implementation details**: `CommandService` relies on methods not exposed by `ISettlementSystem`. This should be addressed in a future refactor by updating the Protocol or using `create_and_transfer`.

## Verification Checklist
- [x] `IAssetRecoverySystem` in `modules/system/api.py` includes `receive_liquidated_assets`.
- [x] `test_liquidation_manager.py` passes.
- [x] `test_command_service_rollback.py` passes (after refactor).

## Test Evidence
```bash
tests/unit/systems/test_liquidation_manager.py::TestLiquidationManager::test_asset_liquidation_integration PASSED [ 33%]
tests/unit/systems/test_liquidation_manager.py::TestLiquidationManager::test_bank_claim_handling PASSED [ 66%]
tests/unit/systems/test_liquidation_manager.py::TestLiquidationManager::test_initiate_liquidation_orchestration PASSED [100%]
tests/system/test_command_service_rollback.py::test_rollback_set_param_preserves_origin PASSED [ 33%]
tests/system/test_command_service_rollback.py::test_rollback_set_param_deletes_new_key PASSED [ 66%]
tests/system/test_command_service_rollback.py::test_rollback_inject_asset PASSED [100%]
```
