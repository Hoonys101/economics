# Penny Hardening Reporting DTOs - Architectural Insight Report

## Architectural Insights

### 1. DTO Hardening (Penny Standard)
We have successfully hardened the Reporting DTOs to strictly use integer pennies for all monetary values, aligning with the "Integer Pennies" architectural guardrail. This eliminates floating-point drift in persisted data and analytics.

*   **`AgentTickAnalyticsDTO`**: `labor_income_this_tick` and `capital_income_this_tick` are now `Optional[int]`.
*   **`WatchtowerSnapshotDTO`**: All nested monetary fields (`gdp`, `m0`, `m1`, `m2`, `revenue`, `welfare`, `debt`, `m2_leak`) are now `int`.
*   **`AgentStateData`**: `assets` is now `Dict[CurrencyCode, int]`.
*   **`TransactionData`**: Added `total_pennies: int` as the Single Source of Truth (SSoT) for transaction value.
*   **`EconomicIndicatorData`**: Monetary aggregates (`total_household_assets`, `total_firm_assets`, `total_labor_income`, `total_capital_income`) are now `int`.

### 2. Database Schema Alignment
The SQLite schema has been updated to reflect these changes:
*   `REAL` columns for monetary values have been changed to `INTEGER`.
*   `transactions` table now includes `total_pennies` column.

### 3. Analytics System Update
`AnalyticsSystem.aggregate_tick_data` now correctly casts monetary values to `int` before populating DTOs. It also populates the new `total_pennies` field in `TransactionData`.

### 4. Test Modernization
Existing tests (`test_persistence_purity.py`, `test_watchtower_hardening.py`, `test_repository.py`) have been updated to mock and assert integer values, ensuring the test suite remains valid and robust against the new schema.

## Test Evidence

All relevant tests passed successfully.

```
tests/unit/test_repository.py::test_save_and_get_simulation_run
-------------------------------- live log call ---------------------------------
INFO     simulation.db.run_repository:run_repository.py:26 Started new simulation run with ID: 1
PASSED                                                                   [ 20%]
tests/unit/test_repository.py::test_save_and_get_agent_state PASSED      [ 40%]
tests/unit/test_repository.py::test_save_and_get_transaction PASSED      [ 60%]
tests/unit/test_repository.py::test_save_and_get_economic_indicators PASSED [ 80%]
tests/unit/test_repository.py::test_indexes_created PASSED               [100%]
```

```
tests/unit/test_watchtower_hardening.py::TestWatchtowerHardening::test_repo_birth_counts PASSED [ 50%]
tests/unit/test_watchtower_hardening.py::TestWatchtowerHardening::test_tracker_sma_logic PASSED [100%]
```

```
Analytics System Purity Verified
```
