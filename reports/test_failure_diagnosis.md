# Test Failure Analysis Report

## Executive Summary
The analysis of `failed_tests_final.txt` reveals 27 test failures, which can be primarily grouped into three categories: **Attribute Errors** from refactoring drift, **Type Errors** due to incorrect data types or mock configurations, and **Assertion Errors** indicating a divergence in core logic. Most issues stem from recent refactoring that was not propagated to the tests, along with changes in default values and expected computational outcomes.

## Detailed Analysis

### 1. Attribute & Refactoring-Related Failures
- **Root Cause**: These failures are symptomatic of recent code refactoring. Object attributes have been renamed, removed, or had their access patterns changed (e.g., direct access vs. a getter method), but the corresponding tests were not updated.
- **Evidence**:
    - `tests/integration/scenarios/phase21/test_automation.py:51`: `AttributeError: 'ProductionState' object has no attribute 'production_this_tick'`
    - `tests/integration/scenarios/phase21/test_automation.py:88`: `AttributeError: 'Firm' object has no attribute 'agent_data'. Did you mean: 'get_agent_data'?`
    - `tests/integration/scenarios/phase21/test_firm_system2.py:41, 60`: `AttributeError: 'Firm' object has no attribute '_social_state'`
    - `tests/integration/test_government_fiscal_integration.py`: `AttributeError: Mock object has no attribute 'progressive_tax_brackets'`
    - `tests/modules/household/test_political_integration.py:56`: `TypeError: SocialOutputDTO.__init__() got an unexpected keyword argument 'is_active'`
- **Files Requiring Correction**:
    - `tests/integration/scenarios/phase21/test_automation.py`
    - `tests/integration/scenarios/phase21/test_firm_system2.py`
    - `tests/integration/test_government_fiscal_integration.py`
    - `tests/modules/household/test_political_integration.py`
- **Recommended Fix Strategy**:
    - **Identify New Patterns**: For each `AttributeError`, locate the new attribute name or access method (e.g., use `get_agent_data()` instead of `agent_data`).
    - **Update Test Code**: Modify the test files to align with the updated code contracts.
    - **Update Mocks**: Correct the mock object in `test_government_fiscal_integration.py` to provide the expected `progressive_tax_brackets` attribute.
    - **Update DTO Instantiation**: Remove the `is_active` keyword argument when creating `SocialOutputDTO` in `test_political_integration.py`.

### 2. Type Mismatches and Incorrect Data Structures
- **Root Cause**: These errors occur when a function or method receives an object of an unexpected type. Common instances include `MagicMock` objects being used in numeric or string comparisons, or primitive types (`int`, `float`) being used where a dictionary-like object is expected.
- **Evidence**:
    - `simulation/systems/generational_wealth_audit.py:53`: `TypeError: unsupported format string passed to MagicMock.__format__` (in `test_run_audit`)
    - `modules/government/engines/decision_engine.py:106`: `TypeError: '>' not supported between instances of 'MagicMock' and 'int'` (in `test_make_policy_decision_updates_fiscal_policy`)
    - `simulation/ai/system2_planner.py:119`: `TypeError: '<' not supported between instances of 'MagicMock' and 'int'` (in `test_system2_housing_cost_renter` and `_owner`)
    - `simulation/core_agents.py:133`: `TypeError: Random.uniform() missing 2 required positional arguments` (in `test_immigration_trigger`)
    - `simulation/orchestration/tick_orchestrator.py:61` & `simulation/initialization/initializer.py:333`: `AttributeError: 'float'/'int' object has no attribute 'get'`
- **Files Requiring Correction**:
    - `simulation/systems/generational_wealth_audit.py`
    - `modules/government/engines/decision_engine.py`
    - `simulation/ai/system2_planner.py`
    - `simulation/core_agents.py`
    - `simulation/orchestration/tick_orchestrator.py`
    - `simulation/initialization/initializer.py`
    - The setup of the corresponding test files.
- **Recommended Fix Strategy**:
    - **Correct Function Calls**: Fix the `Random.uniform()` call in `simulation/core_agents.py` by providing the required arguments.
    - **Improve Mocking**: In the relevant tests, ensure that `MagicMock` objects are configured to return appropriate numeric values before being passed into logic that performs comparisons.
    - **Fix Data Structures**: Investigate the data being passed to the `tick_orchestrator` and `initializer`. The code expects a dictionary or object, so the input data structure must be corrected at the source.

### 3. Assertion Failures and Logic Drift
- **Root Cause**: These failures represent a deviation from the expected behavior. The code runs but produces incorrect results, causing assertions to fail. This indicates changes or regressions in the underlying business logic, calculations, or test environment setup.
- **Evidence**:
    - `test_foreign_currency_distribution_to_shareholders`: `AssertionError: False is not true : Shareholder should receive 1000 USD`
    - `test_bank_deposit_balance`: `AssertionError: 0.0 != 150.0`
    - `test_full_liquidation_cycle`: `assert 0.0 == 1000.0`
    - `test_run_tick_defaults`: `assert 0 > 10` (and log `Bank: EventBus not injected...`)
    - `test_implements_financial_entity` & `test_liquidation_order_generation_id`: `assert 999999 == -1`
    - `test_websocket_endpoint`: `AssertionError: assert 'timestamp' in {...}`
    - `test_newborn_receives_initial_needs_from_config`: `assert 0 == 1`
    - `test_appliance_effect` & `test_scenario_a_dark_ages`: Assertion errors with incorrect calculations.
- **Files Requiring Correction**:
    - `tests/integration/test_multicurrency_liquidation.py` (and related logic)
    - `tests/integration/test_portfolio_integration.py` (and related logic)
    - `tests/integration/test_public_manager_integration.py` (and related logic)
    - `tests/simulation/test_bank_decomposition.py`
    - `tests/unit/modules/system/execution/test_public_manager_compliance.py`
    - `server.py` (or wherever the websocket payload is generated)
    - `tests/unit/systems/test_demographic_manager_newborn.py` (and related logic)
    - `tests/unit/test_socio_tech.py` (and related logic)
- **Recommended Fix Strategy**:
    - **Isolate and Debug**: These errors require case-by-case debugging of the core application logic to understand why the output has diverged from the expectation.
    - **Fix Test Setup**: For `test_run_tick_defaults`, inject a mock `EventBus` into the `Bank` object during test setup to prevent skipping default consequences.
    - **Correct ID Handling**: For the `PublicManager` compliance tests, investigate why the default/sentinel ID is now `999999` instead of `-1` and align the test with the new expected value.
    - **Amend Data Payloads**: For the `websocket` test, ensure the `timestamp` key is added to the root of the JSON payload.
    - **Review Logic**: The remaining assertion failures require a direct review of the underlying economic calculations in liquidation, portfolio management, newborn initialization, and socio-tech effects.
