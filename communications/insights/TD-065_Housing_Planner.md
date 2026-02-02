# Insight: Housing Planner Implementation (TD-065)

## Technical Debt & Risks

### 1. Configuration Object Structure
The `HousingPlanner.evaluate_and_decide` method accepts a `config` object of type `Any`. The implementation assumes this object has a nested structure (e.g., `config.finance.MORTGAGE_INTEREST_RATE`, `config.housing.RENT_TO_INCOME_RATIO_MAX`). This structure does not strictly align with the existing `HouseholdConfigDTO` which is flat.
**Risk**: If the orchestrator passes the flat `HouseholdConfigDTO` directly, the planner will crash with `AttributeError`.
**Recommendation**: Create a specific `HousingPlannerConfigDTO` or ensure the orchestrator wraps the flat config into the expected nested structure.

### 2. Mortgage Calculation Logic duplication
A `_calculate_mortgage_payment` helper was implemented directly within `HousingPlanner`.
**Debt**: This logic likely belongs in `modules.finance` or a shared utility to ensure consistency across the simulation (e.g., if banks use a different formula).
**Action**: Future refactoring should extract this into a shared financial utility.

### 3. Dynamic Interest Rates vs Static Config
The legacy `DecisionUnit` logic accessed dynamic interest rates from the Loan Market snapshot (`market_snapshot["loan"]["interest_rate"]`). The new `HousingPlanner` spec only provides `HousingMarketStateDTO` and `config`.
**Impact**: The current implementation uses `config.finance.MORTGAGE_INTEREST_RATE`, which implies a static rate or a rate passed via config update. If the simulation relies on dynamic rates fluctuating tick-by-tick, this planner will not react to them unless the `config` object is updated every tick to reflect current market rates.
**Recommendation**: Update `IHousingPlanner.evaluate_and_decide` to accept `LoanMarketStateDTO` or include interest rate data in `HousingMarketStateDTO`.

### 4. Market Data Completeness
The spec assumes `HousingMarketStateDTO` contains all units. In a large-scale simulation, passing *all* units might be performance-heavy.
**Future Optimization**: The planner might need to receive a filtered list or summary statistics instead of raw unit lists.
