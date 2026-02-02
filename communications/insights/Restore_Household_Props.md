# Technical Debt & Insights Report: Restore Household Properties & Fix FiscalPolicyManager

## Phenomenon
During the verification of `Household` property restoration using `scripts/trace_leak.py`, a cascade of `AttributeError` failures occurred in `ConsumptionManager`, `LaborManager`, `AssetManager`, and `DemographicManager`.
Specifically, these managers were attempting to access `_bio_state` and `_econ_state` attributes on the `household` object, which in the context of the decision engine (`AIDrivenHouseholdDecisionEngine`), is actually a `HouseholdStateDTO`.

## Cause
The `Household` class was refactored to delegate state to `BioStateDTO` and `EconStateDTO`, and the decision engine was updated to pass `HouseholdStateDTO` to managers. However, the managers (`simulation/decisions/household/*`) were seemingly written or left in a state where they expected the full `Household` agent object (or an object with `_bio_state`/`_econ_state` structure), whereas `HouseholdStateDTO` provides a flattened view of these properties (e.g., `assets` directly, not `_econ_state.assets`).

Additionally, unit tests (e.g., `test_household_engine_refactor.py`) were mocking `HouseholdStateDTO` but incorrectly setting up `_econ_state` on the mock, masking the issue in tests until integration/system tests (`trace_leak.py`) ran.

## Solution
1.  **Restored Properties on `Household`:** Added getter/setter bridges for `is_active`, `is_homeless`, `age`, `children_ids`, `inventory_quality`, and `employer_id` on the `Household` class to maintain backward compatibility and ensure it acts as a proper facade for its state components.
2.  **Updated Managers:** Modified `ConsumptionManager`, `LaborManager`, and `AssetManager` to access properties directly from the `household` object (which is a `HouseholdStateDTO` in the decision context), aligning with the DTO's flattened structure (e.g., changed `household._econ_state.assets` to `household.assets`).
3.  **Fixed `FiscalPolicyManager`:** Updated `determine_fiscal_stance` to robustly handle Mock objects for price data by attempting float conversion instead of strictly checking for `int`/`float` types. Updated corresponding unit tests to use the correct `MarketSnapshotDTO` constructor.

## Lesson Learned
*   **DTO vs Agent Interface:** When refactoring agents to use DTOs for decision contexts, strictly verify that all downstream consumers (Managers, Strategies) are updated to consume the DTO interface, not the Agent's internal structure.
*   **Mock Fidelity:** Unit tests should mock the *interface* of the DTO, not the implementation details of the Agent. Mocks that simulate internal state structures (`_econ_state`) on a DTO that doesn't have them create a false sense of security.
*   **System Verification:** `trace_leak.py` proved invaluable as a system-level integration test, revealing interface mismatches that isolated unit tests missed.
