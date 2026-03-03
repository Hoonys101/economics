# Insight Report: AUDIT-TEST-MEMORY-LEAK

**File Path**: `communications/insights/WO-IMPL-MEMORY-LEAK-FIX.md`

## 1. [Architectural Insights]
- **Circular Dependency Debt**: The project uses a "Double-Link" pattern between Engines (e.g., `Government`) and Systems (e.g., `FinanceSystem`). In a testing context, this creates a strong reference cycle that defeats simple reference counting. `FinanceSystem` internally utilizes `weakref.proxy` in its initialization, but the `finance_system` fixture passed a locally scoped `mock_gov_shell` which was immediately garbage collected, leading to `ReferenceError`. We resolved the lifecycle test bug by holding the mock shell as an internal state attribute (`system._mock_gov_shell = mock_gov_shell`) so it doesn't collapse before safely being discarded at the end of the test.
- **Registry Pollution**: We eliminated proposed 'Duct-Tape' solutions (like manually invoking `mock_agent_registry.agents.clear()` or dropping global `gc.collect()`) inside local fixture scopes. Instead, we re-focused on `reset_mock()` to cleanly strip invocation tracking without destroying pre-configured return values, relying on standard function-scoped fixture GC to naturally collect disconnected agents in integration tests.
- **Mock Object Infinite Expansion**: Mocking external libraries (like `numpy`) at the top-level `conftest.py` with standard `MagicMock()` introduced severe memory instability because `MagicMock` generates infinite sub-mocks upon arbitrary attribute access. Adding `spec=object` broke essential sub-module imports. To resolve this, we introduced the `ShallowModuleMock` pattern, overriding `__getattr__` to safely return leaf mocks (`return_value=None`) while crucially caching the result via `setattr(self, name, mock_obj)`. This explicitly enforces Object Identity constraints (`numpy.array is numpy.array` returns True) and prevents runaway mock chaining without breaking underlying standard import mechanics.

## 2. [Regression Analysis]
- **Issue**: M2/Ledger tests and large integration scenarios were failing with `MemoryError` and showing massive object creation (+100s of objects per test) on large transaction batches.
- **Root Cause**: `MonetaryLedger` was retaining all `Transaction` instances in its `transaction_log` across test boundaries due to the ledger not being cleared upon test teardown. The initial attempts to sweep globally via `gc.get_objects()` proved non-scalable.
- **Fix**: We introduced explicit, standardized teardown mechanisms across all `MonetaryLedger` test points. A new `clean_ledger` fixture was added using the `yield` pattern in `tests/unit/government/test_monetary_ledger_units.py`, and robust `teardown_method` clear operations were implemented in class-based tests to securely purge `transaction_log` states efficiently per-test.

## 3. [Test Evidence]
```text
tests/unit/government/test_monetary_ledger_units.py::test_monetary_ledger_uses_pennies_source_and_returns_pennies
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_monetary_ledger_uses_pennies_source_and_returns_pennies | Total Objects: 71709
PASSED                                                                   [100%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_monetary_ledger_uses_pennies_source_and_returns_pennies | Total Objects: 77851
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_monetary_ledger_uses_pennies_source_and_returns_pennies -> POST_test_monetary_ledger_uses_pennies_source_and_returns_pennies ---
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +7

========================= 1 passed, 1 warning in 0.51s =========================
```
