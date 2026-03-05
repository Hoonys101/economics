# Architectural Insights: WO-MYPY-CONTRACT-ALIGNMENT

**Date**: 2026-02-24
**Author**: Jules
**Scope**: Simulation Core, Finance, System Modules

## 1. Architectural Insights

### Penny Standard Hardening
The transition to a strict "Penny Standard" (using `int` for all currency values) revealed several areas where `float` was implicitly assumed or tolerated.
- **Central Bank Operations**: The OMO logic (`conduct_open_market_operation`) was accepting floats, which risked precision errors in large-scale monetary injections. This has been strictly typed to `int`.
- **Transaction Processing**: The `TransactionProcessor` now explicitly casts `total_pennies` to `float` when interacting with legacy DTOs that still expect floats, ensuring type safety at the boundary while maintaining the integer truth in the ledger. This highlights a need for a future "Phase 33" refactor to fully eliminate floats from `SettlementResultDTO`.

### Protocol & DTO Alignment
- **Government Policy Interface**: The `IGovernmentPolicy` interface was outdated (using `market_data` instead of `sensory_data`) and inconsistent with its implementations (`TaylorRulePolicy`, `SmartLeviathanPolicy`). We unified the signature to `decide(government, sensory_data, current_tick, central_bank)`, ensuring polymorphism works correctly.
- **DTO Drift**: `GovernmentStateDTO` and `GovernmentSensoryDTO` were being conflated in type hints. We corrected the type hints to reflect that the policy engine receives `GovernmentSensoryDTO`, preventing confusion about available attributes (like `inflation_sma`).

### Liskov Substitution Principle (LSP)
- **Inventory Manager**: The `InventoryManager` implementation lacked the `slot` argument required by the `IInventoryHandler` protocol. This latent LSP violation would have caused runtime errors if a caller used the full protocol capability.
- **Abstract Class Instantiation**: Several core classes (`CentralBank`, `EscrowAgent`, `PublicManager`) were technically abstract because they failed to implement `get_liquid_assets` and `get_total_debt` from `IFinancialAgent`. Implementing these methods fixed instantiation errors and ensures all financial agents behave consistently.

## 2. Regression Analysis

### Protocol Strictness
The `IMarket` protocol defined `buy_orders` and `sell_orders` as attributes, but implementations used properties (or vice versa). We standardized on `@property` in the Protocol to enforce read-only access safety. This broke the `DummyMarket` mock in integration tests, which initialized these as fields.
**Fix**: Updated `DummyMarket` to implement these fields as properties, aligning it with the strict protocol definition.

### Initialization Sequence
Initialization logic in `initializer.py` relied on implicit `None` checks for `GlobalRegistry`. Explicitly asserting `is not None` satisfied MyPy's strict optional checking and made the startup sequence more robust against configuration failures.

## 3. Test Evidence

All tests passed, confirming no functional regressions.

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
================= 1033 passed, 11 skipped, 1 warning in 11.27s =================
```
