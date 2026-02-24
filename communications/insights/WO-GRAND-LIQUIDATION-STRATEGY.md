# Grand Liquidation Strategy: Wave 1 (Startup & Foundation) Insights

## Architectural Insights
1.  **Atomic Firm Creation**: The `FirmFactory` in `simulation/factories/firm_factory.py` has been refactored to enforce an atomic initialization sequence: Instantiation -> Bank Account Registration -> Liquidity Injection. This eliminates the "Ghost Firm" issue where firms could exist without financial accounts. Logic for liquidity injection was extracted to `Bootstrapper.inject_liquidity_for_firm`.
2.  **Initialization Order**: `SimulationInitializer` was restructured to ensure `PublicManager` and `CentralBank` are instantiated and registered in `sim.agents` *before* the `AgentRegistry` state snapshot is taken. This resolves `TD-FIN-INVISIBLE-HAND` where system agents were missing from the registry during initial settlement operations.
3.  **Government Singleton**: The `SimulationState` DTO (`simulation/dtos/api.py`) and `TickOrchestrator` (`simulation/orchestration/tick_orchestrator.py`) were updated to remove the legacy `governments` list field (`TD-ARCH-GOV-MISMATCH`). The system now strictly adheres to a Singleton `primary_government` (or `government`) pattern, removing ambiguity.
4.  **Testing Infrastructure**: The `SimulationStateBuilder` in `modules/testing/utils.py` was updated to reflect the DTO changes (removing `governments`) and include new mandatory fields (`public_manager`, `politics_system`), preventing Mock Drift in governance tests.

## Regression Analysis
During the implementation, several regressions were identified and fixed:

1.  **`TypeError: SimulationState.__init__() got an unexpected keyword argument 'governments'`**:
    *   **Cause**: `tests/system/test_engine.py` and `simulation/action_processor.py` were manually instantiating `SimulationState` with the now-removed `governments` argument.
    *   **Fix**: Updated all instantiation sites to remove the argument.

2.  **`ValueError: SimulationStateBuilder is missing required fields`**:
    *   **Cause**: `tests/modules/governance/test_cockpit_flow.py` failed because the `SimulationStateBuilder` did not include `public_manager` and `politics_system`, which are now required fields in `SimulationState`.
    *   **Fix**: Updated `SimulationStateBuilder` defaults to include these fields.

3.  **Firm Factory Signature Change**:
    *   **Risk**: `FirmFactory.create_firm` signature was updated to require `settlement_system` and `central_bank`.
    *   **Mitigation**: Verified that `FirmFactory.create_firm` is not widely used in the codebase (mostly via `MockFactory` in tests or `create_and_register_firm` in `modules`), and the refactor targeted the `simulation` layer factory intended for Genesis usage. Note: `FirmSystem` uses a different factory path (`modules.firm.services`), so runtime spawning was not affected by this specific change, ensuring safe isolation.

## Test Evidence
All 1033 tests passed successfully.

```
=========================== short test summary info ============================
SKIPPED [1] tests/integration/test_server_integration.py:16: websockets is mocked
SKIPPED [1] tests/security/test_god_mode_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/security/test_server_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/security/test_websocket_auth.py:13: websockets is mocked
SKIPPED [1] tests/system/test_server_auth.py:11: websockets is mocked, skipping server auth tests
SKIPPED [1] tests/test_server_auth.py:8: fastapi is mocked, skipping server auth tests
SKIPPED [1] tests/test_ws.py:11: fastapi is mocked
SKIPPED [1] tests/market/test_dto_purity.py:26: Pydantic is mocked
SKIPPED [1] tests/market/test_dto_purity.py:54: Pydantic is mocked
SKIPPED [1] tests/modules/system/test_global_registry.py:101: Pydantic is mocked
SKIPPED [1] tests/modules/system/test_global_registry.py:132: Pydantic is mocked
================= 1033 passed, 11 skipped, 1 warning in 11.58s =================
```
