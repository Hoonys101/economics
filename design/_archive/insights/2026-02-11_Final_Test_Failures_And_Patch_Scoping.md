# Mission Insights: The Final Seven (Test Restoration)

## Technical Debt Identified

1.  **Implicit Type Expectations (Mock Drift)**:
    -   **Symptom**: `TypeError: an integer is required`.
    -   **Cause**: `numpy.shape` or `MagicMock` objects returned from mocked config values (like `profit_history_ticks`) were being passed to functions that strictly require `int` (e.g., `deque(maxlen=...)` or `random.randint`).
    -   **Resolution**: Applied explicit `int()` casting in `technology_manager.py` and ensured Mock configurations provide proper integer values.

2.  **Pathing and Isolation in Mocks**:
    -   **Symptom**: `AssertionError: True is not false` in demographics tests.
    -   **Cause**: `random.random` was being patched in the wrong module scope, causing the actual production code to use the real random generator instead of the controlled mock.
    -   **Resolution**: Corrected the patch path to target the module where `random` is consumed.

3.  **Currency Key Mismatches**:
    -   **Symptom**: `0.0 != 1000.0` in liquidation and portfolio tests.
    -   **Cause**: Recent Multi-Currency refactoring required `SettlementSystem` to handle dict-based balances. Some tests were still using legacy `assets` properties or had mismatched currency keys (e.g., 'USD' vs 'default').
    -   **Resolution**: Aligned test setup to use `DEFAULT_CURRENCY` and verified the `WorldState.currency_holders` integration.

## Architectural Lessons

-   **Explicit Casting for Resilience**: While `numpy` usually returns integers, when working with heavily mocked objects, explicit casting to `int()` at critical junctions (like `deque` initialization) prevents cascading failures during testing.
-   **Patch Scope Awareness**: Always verify the import path of mocked utilities. Patching `random` in `tests.conftest` versus `simulation.agents.demographics` can lead to non-deterministic test failures.

## Guardrails Checked

-   **Zero-Sum Integrity**: Funds are now correctly tracked across multi-currency settlement.
-   **Protocol Purity**: `HousingHandler` now correctly identifies protocol-compatible agents.
-   **DTO Purity**: Aligned DTO serialization for WebSocket/Dashboard snapshots.
