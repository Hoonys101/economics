# RECOVER_DEATH_SYSTEM_PERF_HANG & CRITICAL DEBT FIXES

## 1. Architectural Insights
* **Test Isolation via Protocols:** The root cause of the test collection hang was the heavy transitive dependency chain triggered by importing `Firm` and `Household` classes directly in unit tests. Replacing these concrete classes with local `Protocol` definitions (`IFirm`, `IHousehold`) or strict `MagicMock` specs decoupled the tests from the massive simulation model imports.
* **Transitive Dependency Management**: `simulation/systems/inheritance_manager.py` now imports `Household` and `Government` strictly within a `TYPE_CHECKING` block to prevent the recursive loop `DeathSystem -> InheritanceManager -> Household -> DeathSystem`.
* **Financial System Hardening**: `simulation/systems/central_bank_system.py` was refactored to remove Transaction Injection (State Purity Violation). It now **returns** transactions ("Bubble-up") instead of appending to an injected list.
* **Test Hygiene**: `tests/unit/test_tax_collection.py` fixed "Mock Purity Violation" by returning a real `Transaction` object instead of `MagicMock`.

## 2. Regression Analysis
* **Broken Tests:** None.
* **Fixed Tests:** `tests/unit/systems/lifecycle/test_death_system_performance.py` now collects instantly (< 3s).
* **Side Effects:** `test_death_system.py`, `test_birth_system.py`, and `test_aging_system.py` were refactored to use the lightweight Protocol pattern.

## 3. Test Evidence

### Performance Test Collection (Fix Verification)
```
DEBUG: [conftest.py] Root conftest loading at 03:54:54
...
DEBUG: [conftest.py] Import phase complete at 03:54:54
============================= test session starts ==============================
collected 1 item

tests/unit/systems/lifecycle/test_death_system_performance.py .          [100%]

============================== 1 passed in 0.01s ===============================
```

### Full Lifecycle Verification
```
============================= test session starts ==============================
collected 152 items

tests/unit/systems/lifecycle/test_death_system.py ..                     [  1%]
...
=========================== 152 passed in 14.22s ============================
```
