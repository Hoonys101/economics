# [Architectural Insights] WO-IMPL-CONFIG-SCALING

## 1. Summary of Findings
- **Zero-Sum Violation Resolved**: The rebalancing of `INITIAL_HOUSEHOLD_ASSETS_MEAN` (200k) and `INITIAL_FIRM_CAPITAL_MEAN` (5M) ensures the total initial economy matches the 100M penny supply, preventing initial liquidity traps.
- **Config Purity Enforced**: The introduction of `FiscalConfigDTO` removes the dependency on loose `getattr` calls in `FiscalEngine`, enforcing explicit configuration injection.
- **Test Integrity**: Several integration tests were relying on `MagicMock` defaults for configuration. These were updated to explicitly provide the new `FiscalConfigDTO` parameters, ensuring tests align with the new schema validation.

## 2. Technical Debt Identified
- **Mock Fragility**: Tests using `MagicMock(spec=config)` without setting attributes were causing `FiscalEngine` to compare `float` with `MagicMock` objects. This highlights the risk of "Mock Drift" where mocks do not accurately represent DTOs.
- **DTO Backward Compatibility**: `FiscalEngine` was refactored to support both `FiscalConfigDTO` (new) and legacy configuration objects (via `getattr` fallback) to ease migration, but tests revealed that `MagicMock` complicates this by returning Mocks for missing attributes.

## 3. Recommended Architectural Adjustments
- **Constraint**: Future engine implementations MUST use DTOs for configuration. The pattern `engine = Engine(config_module)` is deprecated in favor of `engine = Engine(ConfigDTO(...))`.
- **Validation**: The explicit casting of config values in `Government.__init__` ensures type safety before passing to engines.

## 4. Regression Analysis
- **Fixed Regressions**:
    - `tests/integration/test_government_refactor_behavior.py`: Updated mock config to include `FISCAL_TAX_RATE_MIN` and other new constants.
    - `tests/modules/government/engines/test_fiscal_guardrails.py`: Updated to use `FiscalConfigDTO` in fixtures.
    - `tests/test_firm_surgical_separation.py`: Increased mock firm wallet balance to `10,000,000` to satisfy new maintenance fee thresholds during initialization logic.
- **Verification**:
    - `verify_m2_integrity.py` confirmed Initial M2 starts at 100,000,000 pennies.
    - `diagnose_runtime.py` ran for 80 ticks without solvency crashes.
    - `pytest` suite passed 1078 tests (100%).

## 5. Test Evidence
```
============================ 1078 passed in 21.47s =============================
```
