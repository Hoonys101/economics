# Report: Code Audit and Test Failure Analysis

## Executive Summary
The primary cause of test failures, such as in `test_process_transactions_labor_trade`, is a lack of test isolation. The `Simulation` class constructor alters the state of agent objects before test-specific logic is executed, leading to incorrect assertion values. This issue is compounded by two underlying problems: inconsistent configuration management practices and the prevalence of unmigrated, hardcoded constants within the simulation logic.

## Detailed Analysis

### 1. Test Failures due to Lack of Isolation
- **Status**: ❌ Missing (Isolation)
- **Evidence**:
    - The test `test_process_transactions_labor_trade` in `tests/test_engine.py` fails because `buyer_firm.cost_this_turn` is not zero at the start of the test. The assertion `assert buyer_firm.cost_this_turn >= (tx.quantity * tx.price)` demonstrates an attempt to work around this, but it points to a polluted state.
    - `simulation/engine.py:L218-L221` calls `agent.update_needs(self.time)` for every agent during `Simulation.__init__`.
    - The `Firm.update_needs` method (`simulation/firms.py:L763-L845`) performs several actions with side effects, including calculating and recording inventory holding costs (`L771-L773`), paying wages (`L780`), and spending on marketing (`L782-L798`). These actions modify the firm's `assets` and `expenses_this_tick` before the test transaction is ever processed.
- **Notes**: This initialization side effect makes it difficult to write clean, predictable unit tests for methods within the `Simulation` class, as the initial state of agents is not clean.

### 2. Inconsistent Configuration Management
- **Status**: ⚠️ Partial (Inconsistent Implementation)
- **Evidence**:
    - The provided modules (`simulation/engine.py` and `simulation/firms.py`) correctly use Dependency Injection (DI) by accepting and using a `config_module` object.
    - The test fixtures in `tests/conftest.py` and `tests/test_engine.py` properly create and inject a `mock_config` object, which is good practice.
    - However, the user prompt highlights a critical conflict: the potential use of a global import (`from simulation.config import sim_config`) in other, unprovided parts of the codebase.
- **Notes**: If any module uses a global import, it completely bypasses the mocked configuration provided by the test fixtures. This creates a dangerous inconsistency where tests may pass but are not accurately reflecting the runtime behavior, or they fail for reasons unrelated to the code under test. This is a high-risk architectural flaw.

### 3. Unmigrated Hardcoded Constants
- **Status**: ❌ Missing (Centralization)
- **Evidence**: Several "magic numbers" are hardcoded directly in the application logic instead of being sourced from the configuration module.
    - `simulation/engine.py:L100`: `self.batch_save_interval = 50`
    - `simulation/engine.py:L316`: `self.last_avg_price_for_sma = 10.0`
    - `simulation/engine.py:L1233`, `L1246`, `L1250`: Fallback default prices are hardcoded to `10.0`.
    - `simulation/firms.py:L139`: `self.capital_stock: float = 100.0`
    - `simulation/firms.py:L142`: `self.marketing_budget_rate: float = 0.05`
    - `simulation/firms.py:L495`: Automation decay rate is hardcoded: `self.automation_level *= 0.995`
    - `simulation/firms.py:L782`: Marketing spend logic has hardcoded values: `if self.assets > 100.0: marketing_spend = max(10.0, ...)`
- **Notes**: Hardcoding these values increases technical debt, makes the simulation harder to tune, and can cause discrepancies if tests do not use the exact same hardcoded values.

## Risk Assessment
- **High**: Test unreliability will slow down development and erode confidence in the test suite. Developers may waste significant time debugging state pollution issues.
- **High**: The configuration management inconsistency is a critical architectural flaw. It makes the system's behavior non-deterministic in a testing context and can hide bugs.
- **Medium**: Hardcoded constants lead to rigid code that is difficult to maintain and configure.

## Fix Strategy

1.  **Enforce Dependency Injection**: Mandate that all modules across the project receive configuration exclusively through dependency injection (i.e., passed in the constructor). Perform a codebase-wide search for and eliminate all instances of global configuration imports like `from simulation.config import sim_config`.
2.  **Centralize Constants**: Migrate all identified hardcoded constants from `engine.py` and `firms.py` into the main `config.py` file. Update the logic to reference these values from `self.config_module`. The `mock_config_module` fixtures in tests must be updated to include these new attributes to ensure tests continue to pass.
3.  **Isolate Tests**: For unit tests like `test_process_transactions_labor_trade`, avoid using the `simulation_instance` fixture. Instead, test the `TransactionProcessor` class directly or, if testing the `Simulation` method, explicitly reset the state of the mock agents (`firm.cost_this_turn = 0.0`, `firm.revenue_this_turn = 0.0`) immediately before calling the method under test. This ensures the test is evaluating only the logic of the transaction, not the side effects of the `Simulation` constructor.
