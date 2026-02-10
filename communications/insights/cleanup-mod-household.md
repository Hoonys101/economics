# Technical Insight Report: Household Module Cleanup

**Mission Key:** `cleanup-mod-household`
**Date:** 2024-05-23
**Author:** Jules

## 1. Problem Phenomenon
The `household` module unit tests were failing due to significant architectural drift. Key symptoms included:
- `TypeError` during `Household` instantiation due to signature changes (missing `core_config`, `engine`).
- `AttributeError` on mocks (e.g., `_bio_state`) because tests mocked the class but didn't populate internal DTOs used by new Orchestrator logic.
- `TypeError` in `EconStateDTO` initialization (missing `wallet`, `employment_start_tick`).
- Tests referencing deprecated components (`DecisionUnit` housing logic, AI Tactics) that have been refactored or removed.
- Tests expecting `assets` (float) on `EconStateDTO` instead of `IWallet`.

## 2. Root Cause Analysis
1.  **Architecture Shift:** The transition to the Orchestrator-Engine pattern and `AIDrivenHouseholdDecisionEngine` (ActionVector based) rendered many tests obsolete. Tests were still verifying legacy AI Tactics (`decide_and_learn`) which are no longer used.
2.  **DTO Evolution:** `EconStateDTO` evolved to use `IWallet` and added fields like `employment_start_tick`, but tests were not updated.
3.  **Missing Mixin:** `Household` class in `simulation/core_agents.py` was missing inheritance from `HouseholdStateAccessMixin`, causing `HouseholdSnapshotAssembler` to fail when accessing `get_bio_state` etc.
4.  **Hardcoded Values:** Logic contained magic numbers (e.g., `0.95` smoothing factor, `30` tick check) scattered across engines.

## 3. Solution Implementation Details
1.  **Test Factory Update:**
    -   Updated `tests/utils/factories.py` with a robust `create_household` factory that handles dependency injection (`AgentCoreConfigDTO`, `IDecisionEngine`, `Wallet` hydration).
    -   This standardized test setup and eliminated boilerplate errors.

2.  **DTO & Logic Fixes:**
    -   Updated `EconStateDTO` initialization in tests to use `Wallet` and include all required fields.
    -   Updated `EconStateDTO.copy()` to perform a deep copy of `Wallet` to ensure snapshot isolation, fixing `TestHouseholdSnapshotAssembler` failures.
    -   Added `HouseholdStateAccessMixin` to the `Household` class to support snapshot services.

3.  **Legacy Test Cleanup:**
    -   Deleted/Skipped tests in `test_household_decision_engine_multi_good.py`, `test_household_marginal_utility.py`, and `test_household_ai_consumption.py` that verified deprecated AI Tactics (`decide_and_learn`) or removed internal methods (`_handle_specific_purchase`).
    -   Updated `test_decision_unit.py` to mock `HousingPlanner` and `HousingSystem` (Saga) interactions, as `DecisionUnit` now delegates housing actions instead of executing them directly.

4.  **Constant Refactoring:**
    -   Extracted magic numbers in `modules/household/engines/*.py` to module-level constants or `HouseholdConfigDTO` lookups.
    -   Replaced hardcoded `"USD"` with `modules.system.api.DEFAULT_CURRENCY`.

## 4. Lessons Learned & Technical Debt
-   **Technical Debt (Legacy Tests):** A significant portion of tests in `tests/unit/test_household_*.py` targets legacy logic (Tactics, old DecisionUnit). These tests were deleted/skipped to unblock the build but represent a gap in coverage for the new `ActionVector` logic. **Action:** Create new tests for `AIDrivenHouseholdDecisionEngine` focusing on `ActionVector` outputs.
-   **Technical Debt (DecisionUnit):** `DecisionUnit` class seems to be a legacy orchestrator co-existing with `BudgetEngine`. Its role is ambiguous. **Action:** Deprecate `DecisionUnit` fully in favor of `BudgetEngine` and `ConsumptionEngine`.
-   **Mocking Risks:** Tests relying on `MagicMock(spec=Household)` were fragile because they missed dynamic attributes initialized in `__init__`. **Insight:** Use factories (`create_household`) to instantiate real objects with mocked dependencies for more robust integration-like unit tests.
