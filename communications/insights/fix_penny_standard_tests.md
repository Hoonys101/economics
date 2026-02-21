# Insight Report: Fix Penny Standard Migration Test Failures

## Architectural Insights

1.  **Strict Penny/Dollar Separation:** The codebase is moving towards a strict separation where internal value tracking uses integer pennies (`total_pennies`), and floating-point dollars (`price`) are primarily for display or derived representation. The `Transaction` object enforces this, but legacy tests and some engine components (`DebtServicingEngine`) were inconsistent.
2.  **Stateless Engine Consistency:** The `DebtServicingEngine` was incorrectly assigning penny values to the `price` field in `Transaction` objects. This violated the protocol that `price` should be `total_pennies / 100.0`. Fixing this required updates to both the engine and the corresponding unit tests.
3.  **Mock Fidelity:** Integration tests mocking complex systems like `FinanceSystem` must account for new methods like `issue_treasury_bonds_synchronous`. The failure in `test_infrastructure_investment` highlighted the need for mocks to keep pace with API evolution (fallback logic exists but was bypassed by partial mocking).

## Regression Analysis

### 1. `tests/integration/test_government_fiscal_policy.py`
*   **Failure:** `TypeError: cannot unpack non-iterable Mock object`
*   **Cause:** The test mocked `FinanceSystem` but did not provide a return value for `issue_treasury_bonds_synchronous`, which is now preferred by `InfrastructureManager`.
*   **Fix:** Added `issue_treasury_bonds_synchronous` to the mock configuration.

### 2. `tests/unit/modules/finance/test_double_entry.py` & `test_sovereign_debt.py` & `test_system.py`
*   **Failure:** `AssertionError: X.0 != X00` (e.g., `20.0 != 2000`)
*   **Cause:** Tests were asserting that `Transaction.price` (dollars) equaled the input `amount` (pennies).
*   **Fix:** Updated assertions to verify `Transaction.total_pennies` matches the input amount, aligning with the "Penny Standard".

### 3. `tests/unit/finance/engines/test_finance_engines.py`
*   **Failure:** `AssertionError` on `price` check in `test_debt_servicing_engine`.
*   **Cause:** `DebtServicingEngine` was incorrectly setting `price` to the penny integer value.
*   **Fix:** Updated `DebtServicingEngine` to set `price = pennies / 100.0` and updated the test to assert against `total_pennies` for value correctness.

## Test Evidence

```
================= 942 passed, 11 skipped, 2 warnings in 7.40s ==================
```

(Full output truncated for brevity, see execution logs for detailed trace. All 942 tests passed, confirming 100% pass rate.)
