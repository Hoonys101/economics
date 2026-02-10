# Technical Insight Report: Infrastructure Cleanup

## 1. Problem Phenomenon
During the Unit Test Cleanup Campaign for Infrastructure modules, several issues were encountered:
1.  **Environment Instability**: `tests/unit/test_config_parity.py` failed to collect due to `ImportError: No module named 'yaml'` and `ImportError: No module named 'joblib'`.
2.  **Broken Tests**: `tests/unit/test_repository.py::test_save_and_get_transaction` failed with `TypeError: TransactionData.__init__() missing 1 required positional argument: 'currency'`.
3.  **Code Quality Warning**: `tests/unit/test_ledger_manager.py` emitted a `SyntaxWarning: invalid escape sequence '\|'`.
4.  **Hardcoded Constants**: Multiple verification scripts (`scripts/verification/verify_integrity_v2.py`, `scripts/audit_zero_sum.py`, `scripts/trace_tick.py`) contained hardcoded `"USD"` strings, violating the `TD-INT-CONST` directive.

## 2. Root Cause Analysis
1.  **Environment**: The testing environment lacked necessary dependencies (`PyYAML`, `joblib`) which are required by `simulation.ai.model_wrapper` and configuration managers. This suggests a drift between `requirements.txt` and the active environment or insufficient pre-run checks.
2.  **DTO Evolution**: The `TransactionData` DTO was updated in Phase 33 to include a `currency` field (Multi-Polar WorldState), but the corresponding unit test `test_repository.py` was not updated to reflect this change.
3.  **Regex Syntax**: Python 3.12+ is stricter about escape sequences in strings. The regex pattern `\|` in a normal string caused a warning.
4.  **Legacy Patterns**: Scripts were written assuming a single-currency world ("USD") and did not import the canonical `DEFAULT_CURRENCY` from `modules.system.api`.

## 3. Solution Implementation Details
1.  **Dependencies**: Installed `joblib`, `PyYAML`, and other dependencies from `requirements.txt`.
2.  **Test Fixes**:
    *   Updated `tests/unit/test_repository.py` to import `DEFAULT_CURRENCY` from `modules.system.api` and pass `currency=DEFAULT_CURRENCY` when instantiating `TransactionData`.
    *   Updated `tests/unit/test_ledger_manager.py` to use a raw string (`r"..."`) for the regex assertion, resolving the `SyntaxWarning`.
3.  **Refactoring**:
    *   Refactored `scripts/verification/verify_integrity_v2.py`, `scripts/audit_zero_sum.py`, and `scripts/trace_tick.py` to import and use `DEFAULT_CURRENCY` instead of hardcoded `"USD"`.

## 4. Lessons Learned & Technical Debt
-   **TD-INFRA-ENV**: The environment setup process needs to strictly enforce `requirements.txt` installation before running tests to avoid "works on my machine" issues.
-   **TD-TEST-SYNC**: When DTOs are modified (e.g., adding fields), a grep or search for usages in `tests/` should be mandatory to prevent regression in unit tests.
-   **TD-SCRIPT-DEBT**: Scripts in `scripts/` often lag behind the main codebase in terms of best practices (imports, constants). They should be treated as part of the codebase and linted/refactored regularly.

## 5. Verification
-   All unit tests in the scope (`tests/unit/test_repository.py`, `tests/unit/test_ledger_manager.py`, etc.) passed (33/33).
-   Scripts were verified for syntax correctness (`py_compile`).
