# Mission Insight: Fix Integration Tests (Category C/E)

## Overview
This mission focused on resolving persistent failures in integration tests (Category C and E), specifically targeting `test_fiscal_integrity`, `test_generational_wealth_audit`, `test_government_fiscal_policy`, `test_wo048_breeding`, and `test_wo058_production`.

## Phenomena & Analysis

### 1. Mock Attribute Access Failures
- **Phenomenon:** `AttributeError: Mock object has no attribute '_econ_state'` in `test_fiscal_integrity.py`.
- **Cause:** Using `MagicMock(spec=Household)` restricts attribute access to those present in the `Household` class, but does not automatically instantiate complex nested objects like `_econ_state` unless they are explicitly created or the mock is configured to do so. Accessing `household._econ_state` raised an error because the mock didn't have it.
- **Solution:** Explicitly initialize nested mock attributes (e.g., `household._econ_state = MagicMock()`) before setting their properties.

### 2. MagicMock Formatting TypeErrors
- **Phenomenon:** `TypeError: unsupported format string passed to MagicMock.__format__` in `test_generational_wealth_audit.py`.
- **Cause:** The `GenerationalWealthAudit` system logs wealth using f-strings with formatting (e.g., `{total_wealth:.2f}`). In the test, agent assets were mocked. When `sum()` was called on these mocks, it returned a `MagicMock` (or similar), which threw a `TypeError` when the f-string attempted to format it as a float.
- **Solution:** Ensure that mocked agents return actual numerical values (e.g., `float` or `int`) for their `assets` property, rather than `MagicMock` objects, so arithmetic operations and formatting work as expected.

### 3. Configuration Mock Type Mismatches
- **Phenomenon:** `TypeError: float() argument must be a string or a real number, not 'Mock'` in `test_government_fiscal_policy.py`.
- **Cause:** The `FiscalPolicyManager` retrieves configuration values using `getattr(config, "KEY", default)`. When `config` is a `Mock` object, `getattr` returns a new `Mock` for missing attributes instead of the default value (unless `spec` is strict or `get` is properly side-effected). This caused `float(Mock)` to fail.
- **Solution:** Explicitly set configuration attributes on the Mock object (e.g., `config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0`) or use a concrete configuration class/dict for testing.

### 4. Database Path Mocking Failure
- **Phenomenon:** `TypeError: expected str, bytes or os.PathLike object, not Mock` in `test_wo058_production.py`.
- **Cause:** The `Simulation` constructor calls `sqlite3.connect(db_path)`. `db_path` is retrieved via `config_manager.get("simulation.database_name")`. Since `config_manager` was a generic `Mock`, `get()` returned a `Mock` object, which `sqlite3.connect` rejected.
- **Solution:** Configure the `config_manager` mock to return a valid string (e.g., `":memory:"`) for the database path key using `side_effect` or `return_value`.

### 5. Logic Parity in Breeding Tests
- **Phenomenon:** `AssertionError` in `test_wo048_breeding.py` (High Income Scenario).
- **Cause:** The agent decided to reproduce despite high income (high opportunity cost). This suggests that the default `OPPORTUNITY_COST_FACTOR` in the environment or the patched config was effectively zero or insufficient to outweigh the benefits in the NPV calculation.
- **Solution:** Explicitly patch `OPPORTUNITY_COST_FACTOR` in the test setup to a known value (e.g., 0.5) to guarantee deterministic NPV calculation results that match the test expectation.

## Lessons Learned
- **Mock Configuration:** When using Mocks for configuration objects or DTOs, strictly define their attributes. Relying on `getattr` with defaults on a `Mock` is dangerous because the Mock will intercept the call and return a child Mock instead of triggering the default value.
- **Nested Mocks:** `spec=Class` is useful for interface validation but requires manual setup for nested state containers like `_econ_state`.
- **Integration Test Isolation:** Integration tests interacting with DBs or File I/O must ensure that file paths and connection strings are mocked to valid in-memory or temporary locations to avoid TypeErrors in low-level libraries (like `sqlite3`).
