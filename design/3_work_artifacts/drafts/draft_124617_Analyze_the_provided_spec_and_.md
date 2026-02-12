I will begin by analyzing the test failures to understand the problem. I'll start by reading the test failure diagnosis report.
This report provides a clear breakdown of the test failures. It seems the core issue is a drift between the application code and the tests, primarily due to refactoring. The failures are categorized into `AttributeErrors`, `TypeErrors`, and `AssertionErrors`, and the report suggests specific fixes for many of them.

To provide the requested fix strategy for "Engine Purity," I first need to understand that concept as defined in the project. The `GEMINI.md` context file mentions `design/1_governance/architecture/standards/SEO_PATTERN.md`. I'll read that document now.
Based on my analysis of the test failures and the project's architectural standards, here is a comprehensive fix strategy.

# Fix Strategy: Restoring QE and Enforcing Engine Purity

## 1. Executive Summary

The current 27 test failures are symptoms of a deeper issue: a divergence between the application's core logic and its tests, exacerbated by recent refactoring. The root causes are twofold:
1.  **QE Logic Drift**: Test code and mocks are outdated and no longer reflect the current application contracts (attributes, methods, and data types).
2.  **Engine Purity Violations**: Business logic components (Engines) appear to be violating the **Stateless Engine & Orchestrator (SEO)** pattern, causing unpredictable side effects and logic errors that manifest as assertion failures.

This strategy addresses both problems in two phases: an immediate triage to get tests passing and a proactive refactoring to restore architectural integrity and prevent future regressions.

## 2. Phase 1: Immediate QE Fixes (Triage)

This phase focuses on correcting the direct causes of test failures as identified in `test_failure_diagnosis.md`.

### 2.1. Attribute & Refactoring-Related Failures

*   **Immediate Fix**:
    1.  **Update Accessors**: In `tests/integration/scenarios/phase21/test_automation.py`, replace direct access like `firm.agent_data` with the correct getter method, e.g., `firm.get_agent_data()`.
    2.  **Correct Attribute Names**: In `test_automation.py` and `test_firm_system2.py`, find the new names for `production_this_tick` and `_social_state` and update the test code.
    3.  **Update Mocks**: In `tests/integration/test_government_fiscal_integration.py`, configure the `Mock` object to have the `progressive_tax_brackets` attribute.
    4.  **Update DTOs**: In `tests/modules/household/test_political_integration.py`, remove the invalid `is_active` keyword argument from the `SocialOutputDTO` constructor.

*   **Purity Check**: These errors are primarily in test code, but they highlight the importance of stable contracts. As you fix them, verify that the attributes being accessed are part of a defined DTO or a public accessor on an Agent, not an internal state variable of an Engine.

### 2.2. Type Mismatches and Incorrect Data Structures

*   **Immediate Fix**:
    1.  **Configure Mocks**: The errors `'>' not supported between instances of 'MagicMock' and 'int'` are critical. In the tests for `decision_engine.py` and `system2_planner.py`, the `MagicMock` objects must be configured with a `return_value` for the attributes being compared against integers.
        ```python
        # Example Fix
        mock_agent.some_attribute.return_value = 10 
        ```
    2.  **Correct Calls**: In `simulation/core_agents.py`, fix the call to `Random.uniform()` by providing the required arguments.
    3.  **Fix Data Structures**: The `AttributeError: 'float'/'int' object has no attribute 'get'` in `tick_orchestrator.py` and `initializer.py` indicates that a primitive is being passed where an object or dictionary is expected. The test setup must be corrected to pass the appropriate data structure.

*   **Purity Check**: The `TypeError` issues are strong evidence of an SEO violation. An Engine should receive a DTO with well-defined data, not a `MagicMock` pretending to be an Agent. The fix is not just to make the mock work, but to ensure the Engine under test is designed to accept a DTO.

### 2.3. Assertion Failures and Logic Drift

*   **Immediate Fix**:
    1.  **Inject Dependencies**: In `test_run_tick_defaults`, the log `Bank: EventBus not injected...` is the key. The test must inject a mock `EventBus` into the `Bank` instance during setup to ensure consequences are not skipped.
    2.  **Align Sentinel Values**: In `test_public_manager_compliance.py`, the expected ID `999999 == -1` failure shows the default/sentinel value has changed. Update the test assertion to use the new value (`999999`).
    3.  **Correct Payloads**: In the `test_websocket_endpoint` test, modify the test to ensure the `timestamp` key is present in the expected websocket JSON payload.
    4.  **Debug Calculations**: For the remaining financial and economic calculation errors (e.g., `0.0 != 150.0`), perform isolated debugging of the underlying application logic to understand why the output has diverged.

*   **Purity Check**: These failures are the most likely to be caused by Engine Purity violations. A stateful engine can produce unpredictable results (logic drift) based on hidden internal state or by mutating inputs directly. The debugging process must focus on identifying side effects within the engines.

## 3. Phase 2: Proactive Refactoring (Enforce Engine Purity)

This phase moves from fixing symptoms to curing the disease by systematically enforcing the SEO pattern across the codebase.

### 3.1. Audit & Identify Violations

Execute a codebase audit to find violations of the SEO pattern. Use the following search queries as a starting point:

1.  **Find Engines receiving Agent instances (BAD):**
    ```sh
    rg "def \w+\(self, .*agent: \w+\)" ./modules ./simulation
    ```
2.  **Find Engines accessing internal Agent state (BAD):**
    ```sh
    rg "\._" ./modules/*/engines ./simulation/systems
    ```
3.  **Find Engines with internal business state (BAD):**
    ```sh
    rg "self\.(?!logger|_config)" ./modules/*/engines ./simulation/systems
    ```

### 3.2. Refactor Violating Engines

For each violation identified:

1.  **Define DTOs**: Create explicit Input and Output DTOs for the engine. The DTOs should contain all the necessary data from the Agent/System state.
2.  **Make Engine Pure**: Refactor the Engine's `execute` method to be a pure function:
    *   It should accept the Input DTO.
    *   It must not modify the Input DTO.
    *   It must not have any side effects (e.g., no database calls, no direct state mutation).
    *   It should return a new Output DTO containing the results.
3.  **Move State Updates to Orchestrator**: Move the logic that applies the changes (i.e., mutates the Agent's state) out of the Engine and into the calling Orchestrator (the Agent or System). The Orchestrator will now call the engine with a DTO and then use the returned DTO to update its own state.

### 3.3. Update Tests

1.  **Test the Pure Engine**: The unit tests for the Engine should now be much simpler. They will initialize an Input DTO, call the engine, and assert that the returned Output DTO has the expected values. No complex `MagicMock` of agents is needed.
2.  **Test the Orchestrator**: The integration tests for the Agent/System (Orchestrator) will test the stateful part: that it correctly calls the engine and updates its state after receiving the result.

## 4. Verification

1.  **Run Full Test Suite**: After both phases, run the entire test suite to confirm all 27 failures are resolved and no new regressions have been introduced.
2.  **Continuous Integration Check**: Add a CI step that runs the audit scripts from Phase 2 to automatically flag any new SEO pattern violations, preventing architectural drift in the future.