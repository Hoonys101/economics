# Post-Merge Import & Path Stabilization Report

## Architectural Insights
1. **DTO Strictness vs Legacy Aliases**: The `CanonicalOrderDTO` enforces strict types (`price_pennies: int`), but the codebase relies heavily on the `Order` alias which was used with legacy arguments (`price_limit: float`). This mismatch caused widespread `TypeError`s. The solution involved mass refactoring to inject `price_pennies` calculated from the legacy price.
2. **Mocking Integrity**: Tests mocking `Transaction` objects often failed to set `total_pennies`, causing `Mock > int` comparison errors in handlers that prioritize the SSoT (`total_pennies`). Tests must mock data objects comprehensively, especially when strict protocols are involved.
3. **Integer Migration Semantic Drift**: In some cases (e.g., `RealEstateUnit.estimated_value`), the value was already an integer (pennies), but was passed to `price_limit` (expected dollars/float). This required manual correction to ensure `price_pennies` received the raw integer and `price_limit` received the scaled-down float.
4. **Environment Discrepancies**: `pytest` running via `pipx` lacked dependencies (`websockets`, `fastapi`) installed in the local environment. Using `python3 -m pytest` ensures the correct environment is used.

## Test Evidence
```
=========================== short test summary info ============================
SKIPPED [1] tests/unit/decisions/test_household_integration_new.py:13: TODO: Fix integration test setup. BudgetEngine/ConsumptionEngine interaction results in empty orders.
================= 822 passed, 1 skipped, 10 warnings in 17.42s =================
```
