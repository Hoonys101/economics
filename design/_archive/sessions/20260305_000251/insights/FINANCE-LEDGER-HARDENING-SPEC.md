# Finance & Ledger Architecture Hardening Insights

## [Architectural Insights]
- **M2 Calculation Segregation (`MoneySupplyDTO`)**: Instead of relying on a monolithic iteration over all agents to extract `total_money` as a simple scalar float, the system now returns a `MoneySupplyDTO`. This ensures that negative balances (system debt) and positive balances (M2) are strictly separated. The calculation in `MonetaryLedger` strictly looks at registered `ICurrencyHolder` objects, decoupling `WorldState` from being a God Class.
- **Dust Settlement Logic (`IDustReceiver`)**: During the pro-rata allocation in asset liquidation, truncated pennies were previously orphaned, causing a leakage of value. A mechanism was introduced to sweep these remaining pennies to the `PublicManager` via the `IDustReceiver` interface, ensuring zero-sum integrity is perfectly maintained.
- **Reserve Crunch Limitation**: The bond issuance mechanism in `FinanceSystem` was modified to explicitly restrict issuance bounds to the actual reserves of the buyer agent. If the buyer lacks the funds, the requested bond issuance amount is adjusted downward.
- **Base Rate Injection**: Central Bank's interest rate strategy relies on injecting the configurable base rate dynamically via the `IGlobalRegistry`.
- **Ledger Unification**: We consolidated dual `MonetaryLedger` implementations by removing the legacy `modules/government/components/monetary_ledger.py` entirely and refactoring its specific tracking logic (such as identifying credit expansion based on System Agent IDs) directly into the unified SSoT `modules/finance/kernel/ledger.py`.

## [Regression Analysis]
- Tests across the test suite invoking the `MonetaryLedger` were expecting a zero-parameter constructor `MonetaryLedger()`, which had to be updated to pass dummy or real dependencies like `transaction_log=[]` and `time_provider=MagicMock()`.
- Explicit reliance on `calculate_total_money` producing a scalar float required updating assertions or extracting properties from the returned `MoneySupplyDTO` instance (`total_m2_pennies`).
- `test_m2_non_negative_anomaly` failed because `get_expected_m2_pennies` wasn't taking the updated delta variables (`total_money_issued` and `total_money_destroyed`) into account. This was resolved by restoring the dynamic computation step inside `get_expected_m2_pennies` instead of just returning the static base.

## [Test Evidence]
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
XFAIL tests/integration/scenarios/test_scenario_runner.py::TestScenarioRunner::test_run_scenario[/app/tests/integration/scenarios/definitions/gold_standard.json] - TD-ARCH-MOCK-POLLUTION: VectorizedHouseholdPlanner uses numpy ops which fail with MagicMocks from tests.
XFAIL tests/integration/scenarios/test_scenario_runner.py::TestScenarioRunner::test_run_scenario[/app/tests/integration/scenarios/definitions/industrial_revolution.json] - TD-ARCH-MOCK-POLLUTION: VectorizedHouseholdPlanner uses numpy ops which fail with MagicMocks from tests.
=========== 1137 passed, 11 skipped, 2 xfailed, 1 warning in 12.26s ============
```
