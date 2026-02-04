# Insight Report: TD-197 HousingManager Cleanup

## Summary
The legacy `HousingManager` class (`simulation/decisions/household/housing_manager.py` and `simulation/decisions/housing_manager.py`) has been removed. This class was responsible for generating `Order` objects for housing purchases based on System 1 logic (including "Personality Bias" and "Mimicry").

The system has transitioned to a Saga-based approach (`HousingSystem.initiate_purchase` via `DecisionUnit` and `HousingPlanner`), rendering the `Order`-based approach obsolete and ineffective (as there is no active OrderBookMarket for housing).

## Changes
1.  **Removed `HousingManager`**: Both the legacy and the "active" versions were deleted.
2.  **Refactored `AIDrivenHouseholdDecisionEngine`**: Removed the call to `HousingManager.decide_housing`. This engine no longer produces housing orders.
3.  **Refactored `SocialSystem`**: Removed dependency on `HousingManager`. Inlined simple logic for `get_housing_tier` (checking `residing_property_id`).
4.  **Refactored Tests**:
    *   `tests/integration/scenarios/verify_real_estate_sales.py`: Deleted as it tested dead code.
    *   `tests/integration/scenarios/verify_vanity_society.py`: Heavily refactored to remove dependencies on `HousingManager` and fix breakage caused by recent `AIDrivenHouseholdDecisionEngine` and `ConsumptionManager` changes (DTOs, Config Aliases).
    *   `tests/unit/systems/test_social_system.py`: Updated to match `SocialSystem` refactor.

## Functional Impact / Feature Loss
*   **Mimicry / Vanity Housing**: The logic that triggered panic buying of housing based on "Social Rank Gap" (Mimicry) is **removed**. `HousingPlanner` does not currently implement this feature. If this feature is critical, it must be re-implemented within `HousingPlanner` or `DecisionUnit`.
*   **Personality Bias in Housing**: The `should_buy` logic in `HousingManager` included biases for Optimism (appreciation rate) and Ambition (prestige bonus). This logic is **removed**. `HousingPlanner` uses a simpler Value-for-Money score.

## Technical Debt Resolved
*   **TD-197**: HousingManager Legacy | Architectural confusion.
*   Reduced code duplication and confusion regarding which component decides housing purchases.
*   Clarified that `DecisionUnit` -> `HousingPlanner` -> `HousingSystem` (Saga) is the single source of truth for housing transactions.
