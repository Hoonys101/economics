I will explain the command I am about to run. This command uses Python to write a multi-line markdown string into the file `reports/temp/residual_analysis.md`. This is a reliable way to create a file with complex content, as it avoids shell quoting issues.
I am unable to create the file `reports/temp/residual_analysis.md` as I do not have the necessary tools to write files. However, I have completed the analysis of the test errors. Here is the content I would have placed in the report:

# Analysis of Pytest ERRORs

## Executive Summary
The test suite is reporting numerous `ERROR` conditions, distinct from `FAILURES`. These errors primarily stem from outdated constructor calls for `Firm` and `Household` agents, incorrect test setup manipulating read-only properties, and improperly configured mocks. The fixes involve updating test fixtures and agent instantiations to match the current codebase APIs.

## Detailed Analysis

### 1. `Household` Constructor Mismatch
- **File Paths**:
  - `tests/integration/scenarios/diagnosis/conftest.py`
  - `tests/system/test_engine.py`
  - `tests/integration/test_td194_integration.py`
  - `tests/integration/test_wo058_production.py`
  - `tests/modules/household/test_political_integration.py`
  - `tests/unit/test_socio_tech.py`
- **Error Type**: `TypeError`
- **Details**: `Household.__init__() missing 2 required positional arguments: 'core_config' and 'engine'`
- **Suggested Fix**: The `Household` class constructor has been updated. All test cases instantiating `Household` must be modified to provide the mandatory `core_config` and `engine` arguments. This requires refactoring the test fixtures that create `Household` agents.

### 2. `Firm` Constructor Mismatch
- **File Paths**:
  - `tests/integration/scenarios/diagnosis/conftest.py`
  - `tests/integration/scenarios/phase21/test_automation.py`
  - `tests/integration/scenarios/phase21/test_firm_system2.py`
  - `tests/system/test_engine.py`
  - `tests/integration/test_td194_integration.py`
  - `tests/unit/test_marketing_roi.py`
- **Error Type**: `TypeError`
- **Details**: `Firm.__init__() got an unexpected keyword argument 'id'`
- **Suggested Fix**: The `Firm` class constructor no longer accepts `id` as an argument. The ID is likely assigned by a factory or manager. All tests that directly instantiate `Firm` with an `id` must be updated to remove it.

### 3. Improper Test Setup for `OrderBookMarket`
- **File Path**: `tests/integration/test_decision_engine_integration.py`
- **Error Type**: `AttributeError`
- **Details**: `property 'buy_orders' of 'OrderBookMarket' object has no setter`
- **Suggested Fix**: The test fixture attempts to directly assign a value to `market.buy_orders`, which is now a read-only property. The test should be refactored to use the market's public methods (e.g., `place_order`) to populate the order book instead of manipulating its internal state directly.

### 4. Incomplete Mock Configuration for `Firm`
- **File Path**: `tests/simulation/test_firm_refactor.py`
- **Error Type**: `AttributeError`
- **Details**: `Mock object has no attribute 'profit_history_ticks'`
- **Context**: The error occurs in `simulation/firms.py` during initialization: `self.finance_state.profit_history = deque(maxlen=self.config.profit_history_ticks)`.
- **Suggested Fix**: The mock `config` object passed to the `Firm` constructor in this test suite is missing the required `profit_history_ticks` attribute. The mock object needs to be configured to include this attribute to prevent the `AttributeError`.

## Conclusion
The identified ERRORs are systemic and point to significant refactoring of core agent classes (`Firm`, `Household`) and market logic (`OrderBookMarket`) that has not been propagated to the integration and unit tests. To resolve these, a focused effort is needed to update test setups to align with the new, more encapsulated APIs.
