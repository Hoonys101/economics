# Mission Insight: Household Test Fixes

## Overview
Addressed failures in Household-related unit tests caused by the migration to integer-based currency (pennies) and DTO field renaming.

## Technical Debt Discovered

1.  **Currency Unit Mismatch (Config vs State)**:
    -   `HouseholdConfigDTO` and `FirmConfigDTO` mostly use `float` values representing "dollars" (e.g., `household_min_wage_demand = 7.0`).
    -   `EconStateDTO` and `Wallet` use `int` values representing "pennies".
    -   **Impact**: Logic layers (like `DecisionUnit`) must perform ad-hoc conversions (e.g., `min_wage_pennies = int(config.min_wage * 100)`), leading to potential precision errors or "magic number" heuristics.
    -   **Recommendation**: Migrate ConfigDTOs to use integer pennies or introduce a standardized `CurrencyConverter` service available to all engines.

2.  **Test Fixture Fragmentation**:
    -   `tests/utils/factories.py` instantiates `Household` classes directly.
    -   `tests/unit/factories.py` uses `MockFactory` to create DTOs.
    -   **Impact**: Inconsistent test setup behavior. Updates to DTO structure require changes in multiple factory files.

3.  **Stale Test Data**:
    -   Numerous unit tests (`test_consumption_manager.py`, `test_decision_unit.py`, etc.) were manually constructing `EconStateDTO` with `float` values for fields that are now `int` (e.g., `current_wage=0.0`).
    -   Tests were calling `wallet.add(float)`, violating the strict type check in `Wallet` implementation.

## Fixes Applied
-   Updated `tests/unit/modules/household/*` to use `int` for wallet operations and DTO fields.
-   Renamed `EconStateDTO` fields in tests to match the new `_pennies` suffix convention.
-   Updated `DecisionUnit` logic to use integer math and `_pennies` fields, aligning source code with the DTO definition.
