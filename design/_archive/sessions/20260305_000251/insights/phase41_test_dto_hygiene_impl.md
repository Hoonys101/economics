# Phase 4.1: DTO Test Hygiene Implementation Report

## Architectural Insights
1.  **DTO Drift Identified**: `MarketContextDTO` (modules/system/api.py) was missing fields `benchmark_rates` and `fiscal_policy` used by consumers (`Firm.generate_transactions`, `FinanceEngine`).
2.  **SimulationState Gaps**: `SimulationState` DTO (simulation/dtos/api.py) was missing `public_manager`, leading to tests inventing attributes on mocks (Mock Drift) and potential runtime `AttributeError` if accessed dynamically.
3.  **Strict Mocking Exposed Hidden Bugs**: Enforcing `spec=SimulationState` in `TransactionProcessor` tests revealed that the DTO definition was incomplete compared to actual usage.
4.  **Configuration Isolation Issues**: `tests/system/test_labor_config_migration.py` failed because it relied on `yaml` loading in an environment where `yaml` is mocked to return empty data. Fixed by injecting configuration override via fixture.
5.  **Test Hygiene**: `TestSettlementPurity` was failing because it mocked `fs.ledger` (masking the real `BankRegistry`) but didn't mock `fs.bank_registry` access in `process_loan_application`. Fixed by mocking the registry.

## Regression Analysis
*   **Test Failures in `FinanceEngine`**: Refactoring `MarketContextDTO` to a dataclass caused `AttributeError: object has no attribute 'get'` in legacy code using it as a dictionary.
    *   **Fix**: Updated `FinanceEngine` and `Firm` to use dot notation (`market_context.exchange_rates`) and updated `MarketContextDTO` to include required fields with defaults.
*   **Test Failures in `test_labor_config_migration.py`**: The test suite environment mocks `yaml`, preventing `config.LABOR_MARKET` from loading.
    *   **Fix**: Added a fixture to explicitly populate `config.LABOR_MARKET` for the test.

## Test Evidence
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
================= 982 passed, 11 skipped, 2 warnings in 8.71s ==================
```
