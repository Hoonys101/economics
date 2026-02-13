# Insight Report: Manual Fixes for Integration & Stress Test Regressions

## Architectural Insights

### 1. Protocol Purity and Zero-Sum Integrity
To adhere to the "Protocol Purity" guardrail and avoid using `hasattr`, we introduced a new `@runtime_checkable` Protocol `IMintingSystem` in `simulation/finance/api.py`. This protocol defines the `mint_and_distribute` method, which is used for "God Mode" operations like hyperinflation scenarios.

The `EventSystem` now explicitly checks if the `settlement_system` implements this protocol using `isinstance(settlement_system, IMintingSystem)` before attempting to mint currency. This ensures type safety and clarity about which systems support monetary injection, aligning with the "Zero-Sum Integrity" principle where money creation is a privileged operation.

### 2. DTO Strictness
The `MarketSnapshotDTO` now strictly requires `market_data` to be initialized. This change caused regressions in integration tests where DTOs were instantiated with missing fields. We updated all affected tests to provide `market_data={}`, ensuring compliance with the updated DTO schema.

### 3. Integer Currency
We observed that `SettlementSystem` operations require integer amounts (pennies) to prevent floating-point errors. The stress scenarios were updated to cast calculated injection amounts to `int` before calling settlement methods, reinforcing the system's financial integrity.

## Test Evidence

```bash
$ pytest tests/integration/test_decision_engine_integration.py tests/integration/scenarios/test_stress_scenarios.py
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: asyncio-0.25.3, cov-6.0.0, anyio-4.8.0, html-4.1.1, metadata-3.1.1, json-report-1.5.0, timeout-2.3.1, xdist-3.6.1
collected 13 items

tests/integration/test_decision_engine_integration.py ......             [ 46%]
tests/integration/scenarios/test_stress_scenarios.py .......             [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 13 passed, 2 warnings in 0.26s ========================
```
