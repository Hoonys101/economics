# WO-STABILIZE-POST-MERGE Insight Report

## 1. Architectural Insights
*   **Command Service & Protocol Flexibility:** The `CommandService` rollback logic was previously overly strict, requiring the `registry` to implement `IRestorableRegistry`. This tight coupling prevented valid rollbacks for commands that don't depend on the registry (like `INJECT_ASSET`, which interacts with the `SettlementSystem`) or for simple registry implementations (like Mocks in unit tests). The solution was to decouple the check, allowing `INJECT_ASSET` to proceed regardless of registry type, and implementing a graceful fallback to `set()` for `SET_PARAM` commands when `IRestorableRegistry` is unavailable. This maintains system stability while supporting legacy and test environments.
*   **Strict Integer Math in Matching:** The `OrderBookMatchingEngine` and `StockMatchingEngine` had drifted to using `int(round(...))` for price calculations to "prevent deflationary bias". However, this introduced inconsistency with strict integer math expectations ("Penny Standard") and caused Zero-Sum/Precision failures in tests expecting standard integer division (truncation). The decision was made to revert to `//` (integer division) to prioritize deterministic, strict integer arithmetic over bias mitigation, aligning with the core financial integrity rules of the simulation.
*   **Initializer Robustness:** The `SimulationInitializer` was prone to `TypeError` when handling Mock objects during testing because it compared `MagicMock` directly to integers. Adding an explicit `int()` cast ensures robustness against non-integer inputs (including Mocks and strings) during the critical startup phase.

## 2. Regression Analysis
*   **Initializer Type Error:** The regression was caused by `MagicMock` objects being passed as initial balances in tests. Previously, implicit comparison might have worked or been mocked differently. The fix `int(amount)` forces the Mock to resolve to an integer (usually 1 or specified `return_value`), preventing the crash.
*   **CommandService Rollback Failures:** New strict type checking `isinstance(registry, IRestorableRegistry)` blocked execution of rollback logic in unit tests where the registry was a simple `MagicMock` (which defaults to `IGlobalRegistry`). This broke existing tests that expected `set()` to be called as a fallback. The fix restores the fallback path, ensuring backward compatibility with simpler registry implementations and test mocks.
*   **Market Precision Mismatch (`100 != 99`):** A previous change introduced `round()` logic to the matching engine, likely to address economic bias. However, this broke the `test_market_zero_sum_integer` test which expects integer truncation (floor) behavior typical of integer math (`(100+99)//2 = 99`). Reverting to `//` fixed the regression and restored strict integer compliance.

## 3. Test Evidence
The following output demonstrates that all affected tests (Command Service Rollback, Market Precision, and Hardening) now pass successfully.

```
tests/unit/modules/system/test_command_service_unit.py::test_dispatch_set_param PASSED [  7%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_set_param_restorable
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:339 ROLLBACK: Restored test_param to 50 (Origin: 0)
PASSED                                                                   [ 15%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_set_param_fallback
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:344 ROLLBACK: Restored test_param via set() fallback
PASSED                                                                   [ 23%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_creation_restorable
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:332 ROLLBACK: Deleted new_param
PASSED                                                                   [ 30%]
tests/unit/modules/system/test_command_service_unit.py::test_dispatch_inject_money PASSED [ 38%]
tests/unit/modules/system/test_command_service_unit.py::test_rollback_inject_money
-------------------------------- live log call ---------------------------------
INFO     modules.system.services.command_service:command_service.py:391 ROLLBACK: Burned 1000 from 1
PASSED                                                                   [ 46%]
tests/unit/modules/system/test_command_service_unit.py::test_commit_last_tick_clears_stack PASSED [ 53%]
tests/market/test_precision_matching.py::TestPrecisionMatching::test_labor_market_pricing PASSED [ 61%]
tests/market/test_precision_matching.py::TestPrecisionMatching::test_market_fractional_qty_rounding PASSED [ 69%]
tests/market/test_precision_matching.py::TestPrecisionMatching::test_market_zero_sum_integer PASSED [ 76%]
tests/market/test_matching_engine_hardening.py::TestMatchingEngineHardening::test_order_book_matching_integer_math PASSED [ 84%]
tests/market/test_matching_engine_hardening.py::TestMatchingEngineHardening::test_stock_matching_mid_price_rounding PASSED [ 92%]
tests/market/test_matching_engine_hardening.py::TestMatchingEngineHardening::test_small_quantity_zero_pennies PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 13 passed, 1 warning in 0.36s =========================
```
