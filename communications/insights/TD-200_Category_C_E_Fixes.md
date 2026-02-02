# Technical Debt & Insights Report: Category C & E Fixes

## Mission: TD-200 (Fix Logic Failures)

### 1. Phenomenon: Missing Default Values in Mock Configs
- **Observation**: `MonetaryPolicyManager` crashed with `TypeError: '>' not supported between instances of 'MagicMock' and 'float'` because it tried to access `getattr(config_module, "CB_NEUTRAL_RATE", 0.02)`. Since `config_module` was a `MagicMock`, it returned a new Mock instead of raising `AttributeError` (which would trigger the default) or returning the default.
- **Cause**: `MagicMock` by default creates attributes on access. `getattr(mock, "attr", default)` returns `mock.attr` (which is a Mock), ignoring `default`.
- **Solution**: Explicitly set attributes in `configure_mock` (e.g., `CB_NEUTRAL_RATE=0.02`).
- **Lesson Learned**: When mocking configuration objects that use `getattr` with defaults, ALWAYS explicitly set the attribute on the mock, or use `spec` carefully. `MagicMock` behaves differently than standard objects regarding `getattr` defaults.

### 2. Phenomenon: Test/Code mismatch in Household Attributes
- **Observation**: `test_indicator_aggregation` failed because it set `household.current_consumption`, but the `EconomicIndicatorTracker` read `household._econ_state.current_consumption`.
- **Cause**: The `Household` refactor moved state to DTOs (`_econ_state`), removing facade properties. The test was not updated to reflect this structural change.
- **Solution**: Updated test to write directly to `_econ_state`.
- **Lesson Learned**: Unit tests must be strictly synchronized with architectural refactors. When removing facade properties, grep for test usages to ensure no "silent writes" (setting a new attribute on the object) occur.

### 3. Phenomenon: Testing Deprecated Interfaces
- **Observation**: `test_collect_tax_legacy` verified that `government.tax_agency.collect_tax` was called. However, `Government.collect_tax` (itself deprecated) had been refactored to bypass `TaxAgency` and call `SettlementSystem` directly.
- **Cause**: The test was verifying an implementation detail (collaboration with TaxAgency) that had been removed, rather than the outcome (money collection) or the new collaborator (SettlementSystem).
- **Solution**: Updated the test to verify `settlement_system.transfer` is called.
- **Lesson Learned**: When components are deprecated or removed (like `TaxAgency`), associated tests should either be removed or updated to test the new path immediately to avoid "zombie tests".

### 4. Phenomenon: Missing Mock Attributes in System Tests
- **Observation**: `test_depression_scenario_triggers` failed with `AttributeError: Mock object has no attribute 'agents'` because `PersistenceManager` accessed `repository.agents`, which wasn't mocked in the system test setup.
- **Cause**: Integration/System tests mocking complex dependencies (`SimulationRepository`) often miss deeply nested attributes used by specific subsystems (`PersistenceManager`).
- **Solution**: Added `repository.agents = MagicMock()` to the test setup.
- **Lesson Learned**: Use `spec=RealClass` and possibly recursive specs (or better, real stub objects) for complex repositories to catch missing attribute errors earlier or provide better error messages.
