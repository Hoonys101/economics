# Mission Insights: Fix 46 Test Issues

## Technical Debt Identified

1.  **Deprecated Methods & Interface Drift**:
    - `FinanceSystem.grant_bailout_loan` is marked deprecated but was still tested as a primary method. It now returns `None`, causing confusion.
    - `Registry` relied on `Household.record_consumption` and `add_labor_income` which were missing from the implementation (likely lost during a refactor), causing hidden runtime errors in integration.

2.  **Factory vs Direct Instantiation**:
    - Many tests instantiated `Household` and `Firm` directly, bypassing required dependency injection (`core_config`, `engine`). This led to widespread failures when constructor signatures changed. Usage of `tests.utils.factories` is now enforced.

3.  **Mocking Fragility**:
    - Tests for Dashboard and WebSocket contracts failed because `MagicMock` objects were leaking into the serialization layer (JSON).
    - `MagicMock` comparison failures (e.g. `>= int`) revealed insufficient mock configuration for composite state objects (like `FirmStateDTO.finance`).

4.  **Demographics & Determinism**:
    - `DemographicManager` was initializing newborns with default random ages (20-60) instead of 0.0 because `initial_age` was not passed.
    - `DemographicsComponent` iterated over a dictionary of death probabilities, leading to potential non-deterministic behavior in tests.

## Resolution Summary

- **Refactored 7 test files** to use `create_household` / `create_firm` factories.
- **Fixed serialization** by ensuring mocks return primitive types.
- **Aligned FinanceSystem tests** to use `request_bailout_loan` (Command pattern).
- **Hardened Registry** against `seller=None` cases.
- **Restored missing methods** (`record_consumption`, `add_labor_income`) in `Household`.
- **Fixed Logic Bugs** in `DemographicManager` (newborn age) and `DemographicsComponent` (sorting).

## Architecture Guardrails Checked

- **Zero-Sum Integrity**: Verified `SettlementSystem` tests passing.
- **Protocol Purity**: Enforced `IFinancialAgent` in tests.
- **DTO Purity**: Fixed DTO helper generation in tests.
