# [Architectural Insights] WO-IMPL-CONFIG-SCALING

## 1. Summary of Findings
- **Zero-Sum Violation Resolved**: The rebalancing of `INITIAL_HOUSEHOLD_ASSETS_MEAN` (200k) and `INITIAL_FIRM_CAPITAL_MEAN` (5M) ensures the total initial economy matches the 100M penny supply. Verified by `verify_m2_integrity.py`.
- **Config Purity Enforced**: `FiscalEngine` now strictly requires `FiscalConfigDTO` injection, removing legacy `getattr` fallbacks. `FiscalConfigDTO` was expanded to include `tax_adjustment_step` and `debt_ceiling_hard_limit_ratio`.
- **Dimensional Consistency**: `AgingSystem` now uses `defaults.DEFAULT_FALLBACK_PRICE` (1000 pennies) for inventory valuation, ensuring integer arithmetic throughout the lifecycle process.

## 2. Technical Debt Identified
- **Mock Drift in Tests**: Several integration tests (`test_government_refactor_behavior.py`, `test_fiscal_guardrails.py`) were using `MagicMock` for configuration without setting all required attributes (e.g., `debt_ceiling_hard_limit_ratio`). This caused `FiscalEngine` to crash when performing comparisons (`>`) against these mocks.
- **Penny vs Dollar Confusion in Tests**: Legacy tests `test_m2_integrity.py` and `test_omo_system.py` were asserting `get_monetary_delta()` returns Dollars (float), while the system has moved to Pennies (int). These assertions were updated to expect Pennies.

## 3. Recommended Architectural Adjustments
- **Standardize Monetary Units**: A global audit of all `get_monetary_delta` usages is recommended to ensure no other components expect Dollars.
- **Strict Config Typing**: Future engines should follow the `FiscalEngine` pattern of requiring a specific DTO in `__init__` rather than a generic config object.

## 4. Regression Analysis
- **Impact**:
    - `FiscalEngine` initialization signature changed. Callers in `government.py` and tests were updated.
    - `AgingSystem` dependency on `defaults` introduced.
- **Mitigation**:
    - Updated `simulation/agents/government.py` to construct full `FiscalConfigDTO`.
    - Updated `tests/unit/modules/government/test_fiscal_engine.py` and `tests/integration/test_government_refactor_behavior.py` to use correct DTO/Mock structure.
    - Verified `verify_m2_integrity.py` passes initialization check.

## 5. Test Evidence
```
tests/test_config_values.py::test_config_constants_rebalancing PASSED    [ 50%]
tests/test_config_values.py::test_config_pennies_integrity PASSED        [100%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_fiscal_engine_taylor_rule PASSED [  8%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_execution_engine_state_update PASSED [ 16%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_orchestrator_integration PASSED [ 25%]
tests/integration/test_government_refactor_behavior.py::TestGovernmentRefactor::test_social_policy_execution PASSED [ 33%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_credit_creation_expansion PASSED [ 41%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_credit_destruction_contraction PASSED [ 50%]
tests/integration/test_m2_integrity.py::TestM2Integrity::test_internal_transfers_are_neutral PASSED [ 58%]
tests/integration/test_omo_system.py::test_execute_omo_purchase_order_creation PASSED [ 66%]
tests/integration/test_omo_system.py::test_execute_omo_sale_order_creation PASSED [ 75%]
tests/integration/test_omo_system.py::test_process_omo_purchase_transaction PASSED [ 83%]
tests/integration/test_omo_system.py::test_process_omo_sale_transaction PASSED [ 91%]
tests/unit/modules/government/test_fiscal_engine.py::test_fiscal_engine_decide_structure PASSED [100%]
```
