# TD-024 Pytest Path Fix: Implementation Report

**Assignee:** Jules
**Date:** 2026-01-15
**Status:** ✅ COMPLETED

---

## 1. Summary of Work

This report details the resolution of the `pytest` collection errors as specified in `TD-024`. The primary issue was not related to `sys.path` hacks as initially suspected, but rather a missing dependency installation step in the test environment.

## 2. Resolution Steps

1.  **Investigation:** Initial investigation showed `pytest.ini` was correctly configured with `pythonpath = .` and `tests/conftest.py` was empty.
2.  **Error Reproduction:** Running `pytest --collect-only` revealed multiple `ModuleNotFoundError` exceptions for packages like `dotenv`, `numpy`, and `joblib`.
3.  **Dependency Installation:** The missing packages were installed by running `pip install -r requirements.txt`.
4.  **Pathing Anomaly:** After installation, `pytest --collect-only` still failed. The issue was resolved by running tests with `python -m pytest ...`, which correctly handles the python path.
5.  **Test Execution:** The full test suite was executed. While the collection errors are fixed, a significant number of tests failed for reasons unrelated to the environment setup.

## 3. Findings & Technical Debt

### 3.1 `sys.path` Hacks
- No `sys.path` modifications were found in `tests/conftest.py` or other inspected test files. The initial premise of the spec was incorrect.

### 3.2 Unrelated Test Failures
- The test suite is currently unstable, with **46 failed tests** and **30 errors**. A full list of failures can be found in the CI/CD logs. This represents significant technical debt and hinders reliable regression testing.
- Key failures include:
    - `TypeError` in multiple tests (e.g., `test_app.py`, `test_corporate_manager.py`), suggesting issues with data types or mock objects.
    - `AssertionError` in `test_bank.py` and `test_household_ai.py`, indicating logic flaws.
    - `playwright._impl._errors.Error` in `test_e2e_playwright.py` due to a missing browser binary, which could not be installed because of missing OS-level dependencies.

### 3.3 Recommendation
- A new technical debt ticket should be created to address the failing tests and stabilize the test suite. The project cannot rely on its automated testing until these issues are resolved.
- The standard operating procedure for running tests should be updated to use `python -m pytest` to avoid future pathing issues.

---
