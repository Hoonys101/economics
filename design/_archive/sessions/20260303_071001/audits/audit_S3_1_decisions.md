# [S3-1] Forensic Audit: Decisions Mocks

## Executive Summary
Audit of `tests/unit/decisions/conftest.py` identifies critical architectural risks including deep mock chains with incomplete spec enforcement and potential memory leaks via uncleaned bidirectional references. The cleanup logic in the `ai_decision_engine` fixture violates the "Protocol Purity" mandate by using `hasattr()` instead of a verified interface.

## Detailed Analysis

### 1. Deep Mock Chains & Spec Enforcement
- **Status**: ⚠️ Partial Compliance
- **Evidence**: `tests/unit/decisions/conftest.py:L61-105`
- **Findings**:
    - `base_mock_firm` utilizes `Mock(spec=Firm)`, adhering to the mandate to avoid "Mock Drift" at the top level.
    - However, secondary components such as `finance`, `production`, `sales`, and `hr` are instantiated as generic `Mock()` objects (L64-67) without specs.
    - **Risk**: This allows tests to pass even if they access methods or attributes that do not exist on the real `FirmFinance` or `FirmProduction` components, leading to "Spec Divergence".

### 2. Bidirectional References & Cycles
- **Status**: ⚠️ Risk Identified
- **Evidence**: `tests/unit/decisions/conftest.py:L117-123`
- **Findings**:
    - The `ai_decision_engine` fixture injects a `Mock()` into `engine.corporate_manager.system2_planner` (L119).
    - **Uncollectible Cycle**: If the mock planner captures the `engine` instance in its `call_args_list` (e.g., during a `project_future` call), a reference cycle is formed: `Engine -> CorporateManager -> MockPlanner -> call_args_list -> Engine`.
    - **Leak Vector**: Since the `base_mock_firm` (L61) is a function-scoped fixture that does not implement explicit teardown for its components, any bidirectional binding between the firm mock and the engine instance during a test will persist until the GC breaks the cycle.

### 3. Protocol Purity Violation
- **Status**: ❌ Non-Compliant
- **Evidence**: `tests/unit/decisions/conftest.py:L122`
- **Findings**:
    - The teardown logic uses `if hasattr(engine.corporate_manager, 'cleanup'):`.
    - **Violation**: This directly contradicts **Mandate 2 (Protocol Purity)** which demands the use of `@runtime_checkable` Protocols and `isinstance()` checks. 
    - **Requirement**: `AIDrivenFirmDecisionEngine` components should implement a `Lifecycle` or `Cleanable` protocol if they require teardown.

## Regression Analysis
- **Finding**: Recent test logs (from `final_pytest_output.txt`) show that decision unit tests are currently passing, but legacy logs in `fails.txt` indicate previous `TypeError` regressions related to `BorrowerProfileDTO` mismatch, highlighting the danger of "Mock Drift" when specs are not strictly enforced.
- **Fix Recommendation**: Update all sub-mocks in `conftest.py` to use `spec=RealClass` and implement a protocol-based cleanup for the `ai_decision_engine` fixture.

## Test Evidence
```text
tests/unit/decisions/test_animal_spirits_phase2.py::TestHouseholdSurvivalOverride::test_survival_override_triggered PASSED
tests/unit/decisions/test_animal_spirits_phase2.py::TestHouseholdSurvivalOverride::test_survival_override_insufficient_funds PASSED
tests/unit/decisions/test_animal_spirits_phase2.py::TestFirmPricingLogic::test_cost_plus_fallback PASSED
tests/unit/decisions/test_animal_spirits_phase2.py::TestFirmPricingLogic::test_fire_sale_trigger PASSED
tests/unit/decisions/test_finance_rules.py::TestFinanceRules::test_rd_investment PASSED
tests/unit/decisions/test_finance_rules.py::TestFinanceRules::test_capex_investment PASSED
tests/unit/decisions/test_finance_rules.py::TestFinanceRules::test_dividend_setting PASSED
tests/unit/decisions/test_household_engine_refactor.py::test_engine_execution_parity_smoke PASSED
tests/unit/decisions/test_household_integration_new.py::TestHouseholdIntegrationNew::test_make_decision_integration PASSED
tests/unit/decisions/test_hr_rules.py::TestHRRules::test_make_decisions_hires_labor PASSED
tests/unit/decisions/test_hr_rules.py::TestHRRules::test_make_decisions_does_not_hire_when_full PASSED
tests/unit/decisions/test_hr_rules.py::TestHRRules::test_make_decisions_fires_excess_labor PASSED
tests/unit/decisions/test_production_rules.py::TestProductionRules::test_initialization PASSED
tests/unit/decisions/test_production_rules.py::TestProductionRules::test_make_decisions_overstock_reduces_target PASSED
tests/unit/decisions/test_production_rules.py::TestProductionRules::test_make_decisions_understock_increases_target PASSED
tests/unit/decisions/test_production_rules.py::TestProductionRules::test_make_decisions_target_within_bounds_no_change PASSED
tests/unit/decisions/test_production_rules.py::TestProductionRules::test_make_decisions_target_min_max_bounds PASSED
tests/unit/decisions/test_sales_rules.py::TestSalesRules::test_sales_aggressiveness_impact_on_price PASSED
```

## Conclusion
The current mock architecture in `tests/unit/decisions/conftest.py` is a "High Risk" technical debt. While functional in the short term, it violates core protocol mandates and contains inherent memory leak vectors. Immediate refactoring to use strict specs and protocol-based lifecycle management is recommended.