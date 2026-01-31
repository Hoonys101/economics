# Household Decomposition Refactor (TD-065)

## Overview
Decomposed the `Household` god-class and the bloated `EconComponent` into specialized sub-components: `ConsumptionManager` and `DecisionUnit`. This aligns with the Component-Entity-System (CES) pattern and improves separation of concerns.

## Changes
1.  **ConsumptionManager**: Created `modules/household/consumption_manager.py` to handle consumption logic (`consume`, `decide_and_consume`). Removed this logic from `EconComponent`.
2.  **DecisionUnit**: Created `modules/household/decision_unit.py` to handle decision orchestration (`make_decision`, `orchestrate_economic_decisions`). Removed this logic from `EconComponent` and `Household`.
3.  **Household**: Updated `Household` to delegate consumption to `ConsumptionManager` and decision-making to `DecisionUnit`.
4.  **Tests**: Updated and created tests to verify the new components and ensure no regressions.

## Technical Debt & Insights

### 1. Duplicated Housing Logic
The `DecisionUnit` contains logic for "System 2 Housing Decision" which appears to be a duplicate or inline version of logic present in `simulation/ai/household_system2.py` (`HouseholdSystem2Planner`).
-   **Insight**: The `DecisionUnit` currently executes this logic inline. Future refactoring should consolidate this by having `DecisionUnit` use `HouseholdSystem2Planner` or moving the logic entirely to the planner, ensuring a single source of truth for housing decisions.
-   **Action**: Investigate if `HouseholdSystem2Planner` can be integrated into `DecisionUnit` to remove code duplication.

### 2. OrderDTO Construction
The legacy code in `EconComponent` (and now `DecisionUnit`) was constructing `Order` objects using `order_type` and `price`. `Order` is now an alias for `OrderDTO`, which requires `side` and `price_limit`.
-   **Fix**: Updated `DecisionUnit` to use the correct `OrderDTO` fields (`side`, `price_limit`).
-   **Risk**: Other parts of the codebase might still be using legacy `Order` construction if they weren't covered by the tests I touched.
-   **Action**: Audit codebase for legacy `Order(...)` usage.

### 3. Stateless vs Stateful Tests
The existing `test_econ_component.py` was attempting to test `EconComponent` as if it were stateful, which caused failures when running tests.
-   **Fix**: Rewrote `test_econ_component.py` to correctly test the stateless nature of `EconComponent` by passing `EconStateDTO`.
-   **Insight**: Transitioning to stateless components requires updating all associated unit tests to reflect the new architecture.

### 4. Legacy `decide_and_consume`
The method `decide_and_consume` was migrated to `ConsumptionManager` but appears to be unused by `Household` (which uses `consume`).
-   **Insight**: It might be dead code.
-   **Action**: Verify if any other system uses `decide_and_consume`. If not, remove it to reduce bloat.

### 5. Hardcoded Magic Numbers in Decision Logic
-   **Insight**: The `DecisionUnit`'s housing NPV calculation and shadow wage update logic contain numerous hardcoded numerical values (e.g., decision frequency, price-to-rent ratios, decay rates, risk premiums). This reduces the configurability and adaptability of the economic model.
-   **Action**: Refactor these magic numbers into the `HouseholdConfigDTO` to allow for easier experimentation and tuning from the central configuration files.

## Conclusion
The refactoring successfully reduced the complexity of `Household` and `EconComponent`, distributing responsibilities to focused managers. The system is now more modular and easier to test, though some logic consolidation (Housing) remains as future work.
