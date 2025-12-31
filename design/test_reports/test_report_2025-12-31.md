# Test Report - 2025-12-31 (Updated)

## Summary
- **Date**: 2025-12-31
- **Executor**: Jules
- **Total Unit Tests**: 166 (Estimated based on previous runs)
- **Passed**: 128 (Partial run of fixed tests + others)
- **Failed**: 4 (Remaining logic assertions in `test_firm_decision_engine.py` and `test_e2e_playwright.py`)

## Improvements
Significant improvements were made by refactoring the tests to align with the V2 Decision Engine Architecture:
1.  **Mock Objects Updated**: Tests now mock `decide_action_vector` to return `FirmActionVector` and `HouseholdActionVector` dataclasses instead of the deprecated `(Tactic, Aggressiveness)` tuples.
2.  **Database Query Fixed**: The `SimulationRepository.save_agent_states_batch` method was corrected to include the missing `generation` column in the SQL query, resolving `sqlite3.ProgrammingError`.
3.  **Household Decision Engine Tests**: Refactored `tests/test_household_decision_engine_new.py` to use V2 logic (Action Vectors), resolving 7 failures.
4.  **Firm Decision Engine Tests (New)**: Refactored `tests/test_firm_decision_engine_new.py` to use V2 logic, resolving 20 failures.

## Remaining Failures
1.  **Legacy Firm Tests (`tests/test_firm_decision_engine.py`)**:
    *   3 tests failed with `AssertionError`.
    *   These tests verify specific order generation (BUY labor, SELL goods).
    *   The failures indicate that even with the correct Mock objects, the V2 engine logic (inventory gap vs. vector aggressiveness) isn't producing the exact orders expected by the legacy test logic (e.g., V2 might require a larger inventory gap or higher aggressiveness to trigger an order than V1).
2.  **E2E Test (`tests/test_e2e_playwright.py`)**:
    *   `TimeoutError` waiting for "Stop Simulation" button.
    *   Likely a frontend state synchronization issue or slow startup in the test container.

## Recommendations
1.  **Deprecate/Rewrite Legacy Tests**: `tests/test_firm_decision_engine.py` seems to be checking V1 behaviors. It should either be fully rewritten to test V2 logic (like `test_firm_decision_engine_new.py`) or deprecated if coverage is sufficient in the `_new` file.
2.  **Investigate Firm V2 Logic**: Review `AIDrivenFirmDecisionEngine.make_decisions` to ensure that `hiring_aggressiveness` and `sales_aggressiveness` correctly translate to orders when inventory gaps exist.
3.  **Frontend Debugging**: Add screenshots or more granular logging to the E2E test to diagnose the UI state during the timeout.
