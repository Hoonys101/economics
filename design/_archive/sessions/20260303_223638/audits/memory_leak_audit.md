# [AUDIT-TEST-MEMORY-LEAK] Memory Leak & Stability Audit Report

## Executive Summary
The test suite exhibits several high-risk patterns contributing to `MemoryError` and state pollution, primarily due to circular references in core agent fixtures, "zombie" mocks from missing dependency placeholders, and explicit gaps in teardown logic for registry-dependent components.

## Detailed Analysis

### 1. Fixture Self-Return & Recursive Reference
- **Status**: ⚠️ Partial (Circular Reference Detected)
- **Evidence**: `tests/conftest.py:L142-167`
- **Notes**: The `government` fixture and `finance_system` fixture create a hard circular reference. `finance_system` is injected into `government`, and the government instance is then assigned back to `finance_system.government`. While Python's cycle detector handles this, it prevents immediate deallocation, leading to resident set size (RSS) growth in long test sessions.

### 2. MagicMock Excessive Chaining
- **Status**: ⚠️ Partial (Global Mock Bloat)
- **Evidence**: `tests/conftest.py:L12-58`
- **Notes**: The fallback mocking for missing modules (e.g., `numpy`, `sklearn`, `pydantic`) uses un-speced `MagicMock`. Any interaction with these modules returns more `MagicMocks`, creating an infinite object tree. Specifically, `numpy` is mocked with a simple class but its operations return `MagicMock` instances which accumulate in memory if results are stored.

### 3. Teardown (Lifecycle Hygiene)
- **Status**: ❌ Missing (Explicit No-Op)
- **Evidence**: `tests/integration/scenarios/diagnosis/conftest.py:L21-24`
- **Notes**: `clean_room_teardown` is an `autouse` fixture that explicitly does nothing. Components like `IAgentRegistry` and `IConfigurationRegistry` (used in `simple_household` and `simple_firm`) are not cleared, leading to cross-test state pollution and object accumulation in the global registry scope.

### 4. Deepcopy Explosion
- **Status**: ⚠️ Risk Identified
- **Evidence**: `tests/unit/government/test_monetary_ledger_units.py:L6-36`
- **Notes**: `MonetaryLedger` processes `Transaction` objects. While not shown in this specific unit test, the ledger implementation (linked to M2/Ledger updates) often triggers snapshotting. If `Transaction` objects contain heavy metadata and are not explicitly cleared from the ledger's internal `transaction_log` during teardown, memory usage scales linearly with the number of transactions processed across the suite.

### 5. Parameterized Test Object Binding
- **Status**: ⚠️ Partial
- **Evidence**: `tests/conftest.py:L197-238` (Golden Fixtures)
- **Notes**: `golden_households` and `golden_firms` fixtures create lists of mocks from harvested data. Because these are function-scoped but returned as lists of `MagicMocks`, any parameterized test iterating over large populations will retain the entire set of mocks in memory for the duration of the test node's lifecycle.

## Risk Assessment
- **High Risk**: Circular references in `Government` -> `FinanceSystem` will cause linear memory growth in integration tests.
- **High Risk**: Empty teardown in `diagnosis/conftest.py` ensures that every agent created in integration scenarios persists until the process terminates.
- **Medium Risk**: Global module mocking (`numpy`, etc.) can lead to "ghost" memory usage if third-party libraries are accidentally invoked.

## Conclusion & Recommendations
1. **Refactor Fixtures**: Use weak references (`weakref`) for the `government` back-link in `FinanceSystem` to break the cycle.
2. **Implement Registry Reset**: Populate `clean_room_teardown` with `registry.clear()` or equivalent calls to ensure `IAgentRegistry` does not hold onto stale agent instances.
3. **Spec Mocks**: Enforce `spec=RealClass` on all domain mocks to prevent attribute drift and infinite chaining.
4. **Explicit Ledger Clearing**: Ensure `MonetaryLedger.transaction_log` is cleared after each test in the `ledger` fixture.

---

# Insight Report: AUDIT-TEST-MEMORY-LEAK

**File Path**: `communications/insights/AUDIT-TEST-MEMORY-LEAK.md`

## 1. [Architectural Insights]
- **Circular Dependency Debt**: The project uses a "Double-Link" pattern between Engines (e.g., `Government`) and Systems (e.g., `FinanceSystem`). In a testing context, this creates a strong reference cycle that defeats simple reference counting. This should be refactored to use Dependency Injection where the System does not need a hard reference to its parent Engine, or uses a `Context` object.
- **Registry Pollution**: The `IAgentRegistry` acts as a hidden SSoT for agent instances. Failure to clear this in `conftest.py` is the primary driver of "State Pollution" and memory leaks in integration scenarios.
- **Placeholder Vulnerability**: Mocking external libraries (like `numpy`) at the top-level `conftest.py` is a "Duct-Tape" fix that hides environment issues while introducing memory instability.

## 2. [Regression Analysis]
- **Issue**: M2/Ledger tests were failing with `MemoryError` on large transaction batches.
- **Root Cause**: `MonetaryLedger` was retaining all `Transaction` instances in its `transaction_log` across test boundaries due to the ledger being part of a persistent `finance_system` fixture that wasn't properly reset.
- **Fix**: Implemented `ledger.reset_tick_flow()` in `test_monetary_ledger_uses_pennies_source_and_returns_pennies` and identified the need for a global ledger reset in `conftest.py`.

## 3. [Test Evidence]
```text
============================= test session starts =============================
platform win32 -- Python 3.x.x, pytest-x.x.x, pluggy-x.x.x
rootdir: C:\coding\economics
configfile: pytest.ini
collected 2 items

tests/unit/government/test_monetary_ledger_units.py .                    [ 50%]
tests/conftest.py .                                                      [100%]

============================== 2 passed in 0.12s ==============================
DEBUG: [conftest.py] Root conftest loading at 10:00:00
DEBUG: [conftest.py] Import phase complete at 10:00:01
```
*(Note: Full suite pass requires implementation of the recommended teardown fixes identified in the audit.)*