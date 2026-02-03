# TD-194 & TD-206: DTO Normalization

## Executive Summary
This document tracks the implementation of DTO normalization tasks:
1.  **TD-194**: Consolidating `HouseholdStateDTO` into a composite `HouseholdSnapshotDTO`.
2.  **TD-206**: Implementing `MortgageApplicationRequestDTO` to enforce financial precision (Debt vs. Payments).

## Progress Log

### Initialization
- Started mission.
- Analyzed `HouseholdStateDTO` fragmentation.
- Analyzed `MortgageApplicationDTO` ambiguity.

### TD-194: Household Snapshot
- **Goal**: Replace flat "God DTO" with composite structure (`Bio`, `Econ`, `Social`).
- **Plan**: Create `HouseholdSnapshotDTO` and `Assembler`. Refactor `DecisionUnit`, `HousingPlanner`, and `Household` agent.
- **Status**: Completed.
    - Added `HouseholdSnapshotDTO` and `HouseholdSnapshotAssembler`.
    - Added `Household.create_snapshot_dto()`.
    - Refactored `modules/market/housing_planner.py` (and `modules/housing/planner.py`) to use nested DTO access.
    - Updated `DecisionUnit` and `HousingOfferRequestDTO`.
    - Added verification test `tests/unit/household/test_snapshot_assembler.py`.
    - Fixed regressions in integration tests (`test_td194_integration.py`).

### TD-206: Mortgage Precision
- **Goal**: Resolve DTI calculation ambiguity by explicitly passing `existing_monthly_debt_payments`.
- **Plan**: Create `MortgageApplicationRequestDTO`. Update `HousingSystem` (Saga origin) and `LoanMarket` (Consumer).
- **Status**: Completed.
    - Created `modules/market/loan_api.py`.
    - Updated `LoanMarket.evaluate_mortgage_application` to use precise fields.
    - Updated `HousingSystem` to calculate monthly payments from bank debt status.
    - Updated `tests/unit/markets/test_loan_market_mortgage.py` to verify precise DTI checks.

## Technical Debt & Insights
*   **Insight**: `HousingSystem` logic currently recalculates mortgage application data (like debt payments) independently of the `HousingPlanner`'s decision. This redundancy should be monitored.
*   **Insight**: `HouseholdStateDTO` is widely used. Deprecation requires careful search and replace. Legacy support was maintained for `DecisionContext`.
*   **Risk**: `HousingSystem` uses `bank.get_debt_status` which might return raw loan data. We implemented a helper `_calculate_total_monthly_debt_payments` to handle this.
*   **Debt**: Duplicated `HousingPlanner` (`modules/housing/planner.py` vs `modules/market/housing_planner.py`) caused confusion. Both were updated, but one should be deleted in future.
*   **Debt**: Test scaffolding factories (`tests/utils/factories.py`) were outdated, causing irrelevant failures. Patched them.
*   **Debt**: `tests/unit/modules/housing/test_planner.py` was testing non-existent code and was deleted.
