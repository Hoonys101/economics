# Test Suite Analysis Report: Post-Merge of `restore-integration-tests` and `jules-fix-corporate-tests`

## Executive Summary
The test suite is in a critical state following the merge, with a high number of failures and errors indicating significant breaking changes. Out of 106 tests, 28 failed and 11 encountered errors during setup, revealing widespread issues related to agent state refactoring, mismatched data transfer objects (DTOs), and incorrect test mock configurations.

## Detailed Analysis

### 1. Systemic Setup Errors
- **Status**: ❌ Missing
- **Evidence**: A large number of tests in `tests/system/test_engine.py` and `tests/integration/test_tick_normalization.py` are failing during setup.
- **Notes**: The primary cause is an `OSError: [Errno 22] Invalid argument` when initializing `crisis_monitor`. The filename is being created from a `MagicMock` object instead of a string, preventing numerous system-level tests from running. Another setup error, `AttributeError: ... does not have the attribute 'Phase4_Lifecycle'`, also breaks `test_tick_normalization.py`. A third setup error, `AttributeError: Mock object has no attribute 'finance'`, affects `test_wo167_grace_protocol.py`.

### 2. Agent State Refactoring (`_econ_state` / `_bio_state`)
- **Status**: ❌ Missing
- **Evidence**: Multiple tests fail with `AttributeError: Mock object has no attribute '_econ_state'` or `'_bio_state'`.
    - `tests/integration/scenarios/test_stress_scenarios.py::TestPhase28StressScenarios::test_hyperinflation_trigger`
    - `tests/integration/scenarios/test_stress_scenarios.py::TestPhase28StressScenarios::test_consumption_pessimism`
    - `tests/integration/test_decision_engine_integration.py::TestDecisionEngineIntegration::test_household_places_buy_order_for_food`
    - `tests/integration/test_decision_engine_integration.py::TestDecisionEngineIntegration::test_household_sells_labor`
    - `tests/integration/test_decision_engine_integration.py::TestDecisionEngineIntegration::test_labor_market_matching_integration`
    - `tests/integration/test_fiscal_integrity.py::test_education_spending_generates_transactions_only`
    - `tests/integration/test_omo_system.py::test_process_omo_purchase_transaction`
- **Notes**: This indicates that agent properties previously accessed via `_econ_state` or `_bio_state` have been moved or refactored. Tests using mock agents have not been updated to reflect these changes.

### 3. DTO & Method Signature Mismatches
- **Status**: ❌ Missing
- **Evidence**: Several tests fail due to `TypeError` or `AttributeError` related to method calls and DTO initializations.
    - `TypeError: Household.make_decision() got an unexpected keyword argument 'markets'` in `test_agent_decision.py`.
    - `ValueError: FirmSystem2Planner requires firm_state (FirmStateDTO).` in `test_automation.py` and `test_firm_system2.py`.
    - `TypeError: FirmStateDTO.__init__() got an unexpected keyword argument 'assets'` in `test_purity_gate.py`.
    - `TypeError: HousingMarketSnapshotDTO.__init__() missing 1 required positional argument: 'units_for_rent'` in `test_td194_integration.py`.
    - `AttributeError: 'MarketSnapshotDTO' object has no attribute 'prices'` in `test_government_fiscal_integration.py`.
- **Notes**: These failures point to breaking changes in method signatures and DTO structures. The tests have not been updated to match the new contracts.

### 4. Logic & Assertion Failures
- **Status**: ⚠️ Partial
- **Evidence**: A number of tests are failing due to incorrect logic, mock configurations, or assertion errors.
    - `test_indicator_aggregation`: `assert 0.0 == 10.0`
    - `test_production_function_with_automation`: `assert 99.0 < 0.0`
    - `test_run_audit`: `TypeError: unsupported format string passed to MagicMock.__format__`
    - `test_collect_tax_legacy`: `AssertionError: Expected 'collect_tax' to be called once. Called 0 times.`
    - `test_scenario_b_high_income`: `AssertionError: True is not false`
    - `test_depression_scenario_triggers`: `TypeError: '>' not supported between instances of 'MagicMock' and 'float'`
- **Notes**: These are individual test failures that require specific investigation but are likely masked by the more systemic issues above.

## Risk Assessment
- **High Risk**: The sheer number of setup errors and `AttributeError`s on core agent objects indicates a fundamental disconnect between the current codebase and the integration tests. The merge has introduced significant instability.
- **Test Debt**: Many tests rely on fragile mock objects, which are now causing `TypeError`s and `AttributeError`s, indicating that the test setup is not robust against refactoring. The `MagicMock` filename issue is a prime example.

## Conclusion
The test suite requires immediate and prioritized attention. The current state prevents a reliable assessment of system health. Failures are systemic, stemming from breaking changes in core data structures (Agent State, DTOs) and test setup fragility.

### Prioritized Repair Plan
1.  **Blocker: Fix Systemic Setup Errors**:
    - **Action**: Resolve the `OSError` in `modules/analysis/crisis_monitor.py` caused by the `MagicMock` filename. This will unblock منهج/test_engine.py and other system tests.
    - **Action**: Correct the `AttributeError` for `Phase4_Lifecycle` in `tests/integration/test_tick_normalization.py`.
    - **Action**: Fix the `AttributeError` for `finance` in `tests/integration/test_wo167_grace_protocol.py`.
2.  **High Priority: Re-align Agent State & DTOs**:
    - **Action**: Globally refactor tests to accommodate the removal of `_econ_state` and `_bio_state`, updating attribute access to the new correct patterns.
    - **Action**: Update all tests that use the `make_decision` method to pass the correct arguments.
    - **Action**: Correct the initialization and usage of all failing DTOs (`FirmStateDTO`, `HousingMarketSnapshotDTO`, `MarketSnapshotDTO`).
3.  **Medium Priority: Address Individual Test Failures**:
    - **Action**: Once the systemic issues are resolved, work through the remaining `FAILED` tests one by one, diagnosing the specific logic or data setup issue. This includes assertion errors and mock-related `TypeError`s.
