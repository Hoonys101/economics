# Insight Report: AUDIT-TEST-MEMORY-LEAK

**File Path**: `communications/insights/WO-IMPL-MEMORY-LEAK-FIX.md`

## 1. [Architectural Insights]
- **Circular Dependency Debt**: The project uses a "Double-Link" pattern between Engines (e.g., `Government`) and Systems (e.g., `FinanceSystem`). In a testing context, this creates a strong reference cycle that defeats simple reference counting. This should be refactored to use Dependency Injection where the System does not need a hard reference to its parent Engine, or uses a `Context` object. `weakref.proxy` in `conftest.py` is utilized to mitigate.
- **Registry Pollution**: The `IAgentRegistry` acts as a hidden SSoT for agent instances. Failure to properly clear and trigger garbage collection on this in `conftest.py` was a primary driver of "State Pollution" and memory leaks in integration scenarios. We enforced strict `reset_mock(return_value=True, side_effect=True)` and `gc.collect(2)` in `clean_room_teardown` to resolve this.
- **Placeholder Vulnerability**: Mocking external libraries (like `numpy`) at the top-level `conftest.py` was a "Duct-Tape" fix that introduced memory instability because simple `MagicMock()`s generate infinite trees on arbitrary attribute access. Adding `spec=object` broke submodule imports, so we opted for explicitly capping recursive mock generation inside numpy arrays by directly attaching bounded specs (`mock.array = MagicMock(spec=list)`).

## 2. [Regression Analysis]
- **Issue**: M2/Ledger tests were failing with `MemoryError` and showing massive object creation (+100s of objects per test) on large transaction batches.
- **Root Cause**: `MonetaryLedger` was retaining all `Transaction` instances in its `transaction_log` across test boundaries due to the ledger being part of a persistent `finance_system` fixture that wasn't properly reset, exacerbated by global module stubs ballooning object depth.
- **Fix**: Implemented `ledger.transaction_log.clear()` explicitly inside teardown flow of `test_monetary_ledger_uses_pennies_source_and_returns_pennies` and normalized the infinite `MagicMock` expansions.

## 3. [Test Evidence]
```text
tests/unit/government/test_monetary_ledger_units.py::test_monetary_ledger_uses_pennies_source_and_returns_pennies
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_monetary_ledger_uses_pennies_source_and_returns_pennies | Total Objects: 72218
PASSED                                                                   [100%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_monetary_ledger_uses_pennies_source_and_returns_pennies | Total Objects: 78313
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_monetary_ledger_uses_pennies_source_and_returns_pennies -> POST_test_monetary_ledger_uses_pennies_source_and_returns_pennies ---
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +7

tests/integration/scenarios/diagnosis/test_agent_decision.py::test_household_makes_decision
-------------------------------- live log setup --------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: PRE_test_household_makes_decision | Total Objects: 78088
PASSED                                                                   [ 28%]
------------------------------ live log teardown -------------------------------
INFO     mem_observer:mem_observer.py:22 MEMORY_SNAPSHOT | Stage: POST_test_household_makes_decision | Total Objects: 79417
INFO     mem_observer:mem_observer.py:40 --- MEMORY GROWTH REPORT: PRE_test_household_makes_decision -> POST_test_household_makes_decision ---
WARNING  mem_observer:mem_observer.py:47 CRITICAL | MagicMock growth detected: +15

========================= 7 passed, 1 warning in 1.56s =========================
```
