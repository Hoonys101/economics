# SPEC: TD-073 Firm Refactor (V2)

**Objective**: Liquidate technical debt TD-073 and TD-190 by refactoring the `Firm` class into a pure facade, removing state-delegating `@property` wrappers, and decomposing the `_execute_internal_order` method.

---

## 1. Problem Definition

-   **TD-073 (Firm "Split Brain")**: The `Firm` class violates the Single Responsibility Principle. It acts as both a facade and a state holder. Convenience `@property` wrappers (e.g., `firm.assets`) obscure the true location of state, which resides in departmental components (`firm.finance`, `firm.hr`). This makes the class difficult to reason about, test, and use for AI model training.
-   **TD-190 (Complex `if/elif` chain)**: The `_execute_internal_order` method in `firms.py` is a large procedural block that directly manipulates state, violating SRP and the facade pattern.

## 2. Implementation Plan

### Phase 1: Remove Property Wrappers

1.  **Targeted Removal**: Systematically delete all `@property` definitions from `simulation/firms.py` that delegate state access to a sub-component. This includes, but is not limited to:
    -   `assets` (delegates to `finance.balance`)
    -   `current_profit` (delegates to `finance.current_profit`)
    -   `revenue_this_turn` (delegates to `finance.revenue_this_turn`)
    -   `expenses_this_tick` (delegates to `finance.expenses_this_tick`)
    -   `sales_volume_this_tick`
    -   `last_sales_volume`
2.  **Update Call Sites**: Use `ripgrep` or a similar tool to find all usages of the removed properties throughout the codebase (in `modules/`, `simulation/`, and `tests/`).
3.  **Refactor Access Patterns**: Modify each call site to use the explicit, direct path to the state.
    -   `firm.assets` -> `firm.finance.balance`
    -   `firm.current_profit` -> `firm.finance.current_profit`
    -   `firm.hr.employees` (already correct, but serves as the pattern)

### Phase 2: Decompose `_execute_internal_order`

1.  **Create Departmental Methods**: Implement new public methods on the relevant department classes to handle specific internal orders. The logic from the `if/elif` block will be moved into these methods.

    -   **`ProductionDepartment` (`production_department.py`)**:
        -   `invest_in_automation(amount: float) -> bool`: Handles the logic for automation investment.
        -   `invest_in_rd(amount: float) -> bool`: Handles R&D investment and its probabilistic outcome.
        -   `invest_in_capex(amount: float) -> bool`: Handles capital expenditure.
        -   `set_production_target(quantity: float)`

    -   **`FinanceDepartment` (`finance_department.py`)**:
        -   `set_dividend_rate(rate: float)`
        -   `pay_ad_hoc_tax(amount: float, reason: str, government: Any, current_time: int) -> bool`

    -   **`SalesDepartment` (`sales_department.py`)**:
        -   `set_price(item_id: str, price: float)`

    -   **`HRDepartment` (`hr_department.py`)**:
        -   `fire_employee(employee_id: int, severance_pay: float) -> bool`

2.  **Refactor `Firm._execute_internal_order`**: The method in `firms.py` will be reduced to a simple router that calls the appropriate new departmental method.

    ```python
    # In simulation/firms.py
    def _execute_internal_order(self, order: Order, government: Optional[Any], current_time: int) -> None:
        """[REFACTORED] Routes internal orders to the correct department."""
        if order.order_type == "SET_TARGET":
            self.production.set_production_target(order.quantity)
        elif order.order_type == "INVEST_AUTOMATION":
            self.production.invest_in_automation(order.quantity, government)
        elif order.order_type == "SET_PRICE":
            self.sales.set_price(order.item_id, order.quantity)
        # ... etc.
    ```

### Phase 3: DTO Definitions (Composite State)

1.  **Departmental DTOs**: If they don't exist, create `FinanceStateDTO`, `HRStateDTO`, `ProductionStateDTO`, `SalesStateDTO` in a new `simulation/dtos/department_dtos.py` file. These will be dataclasses or TypedDicts representing the state of each department.
2.  **Composite `FirmStateDTO`**: Modify `FirmStateDTO` in `simulation/dtos/firm_state_dto.py` to be a composite of the departmental DTOs.

    ```python
    # In simulation/dtos/firm_state_dto.py
    from .department_dtos import FinanceStateDTO, HRStateDTO, ...

    @dataclass
    class FirmStateDTO:
        id: int
        is_active: bool
        # ... other core firm attributes
        finance: FinanceStateDTO
        hr: HRStateDTO
        production: ProductionStateDTO
        sales: SalesStateDTO
    ```
3.  **Update `Firm.get_state_dto()`**: Refactor this method to construct the new composite DTO from its departmental components.

## 3. Verification Plan

1.  **Static Analysis**: After refactoring, confirm no targeted `@property` definitions remain in `firms.py`.
2.  **Unit Tests**:
    -   All existing unit tests for `Firm` and `CorporateManager` must be updated to use the new access patterns (e.g., `firm.finance.balance`) and must pass.
    -   New unit tests must be created for the new methods on each department class (e.g., `test_production_invest_in_automation`).
3.  **Integration Tests**: The entire test suite must pass. Pay special attention to tests that run the full simulation loop to catch any cascading failures.
4.  **Golden Fixture Audit**:
    -   The `golden_firms` fixture in `tests/conftest.py` creates mocks. The generation script or the mock creation logic (`loader.create_firm_mocks()`) must be updated. The mocks must now have nested mock objects (e.g., `firm.finance.balance` must be a valid attribute).

## 4. Risk & Impact Audit

-   **Critical Risk**: **Widespread Test Failure**. Removing properties is a breaking change that will affect dozens of tests.
    -   **Mitigation**: This is an expected outcome. The verification plan explicitly requires a systematic search-and-replace operation on the `tests/` directory to update all failing tests. This is a mechanical task that must be completed thoroughly.
-   **Architectural Impact**: This change is **highly positive**. It resolves two major pieces of technical debt (TD-073, TD-190) and strictly enforces the project's desired Facade and SRP principles for the `Firm` agent, improving long-term maintainability.

---
# SPEC: TD-005 Halo Effect Liquidation

**Objective**: Liquidate technical debt TD-005 by removing the hardcoded `is_visionary` "Halo Effect" and replacing it with an emergent, brand-based resilience mechanism.

---

## 1. Problem Definition

-   **TD-005 (Hardcoded Halo Effect)**: The `is_visionary` flag in `simulation/firms.py` gives certain firms an unfair, hardcoded advantage by doubling their bankruptcy threshold. This violates market fairness principles and is redundant with the more sophisticated `BrandManager` system.

## 2. Implementation Plan

### Phase 1: Remove `is_visionary` Flag

1.  **Remove from Constructor**: Delete `is_visionary: bool = False` from the `Firm.__init__` signature in `simulation/firms.py`.
2.  **Remove from State**: Delete the `self.is_visionary = is_visionary` assignment within `__init__`.
3.  **Remove Logic Block**: Delete the entire `if self.is_visionary:` block that sets `self.consecutive_loss_ticks_for_bankruptcy_threshold`. The threshold will now be derived from the base config value for all firms initially.
4.  **Code Audit**: Perform a global search for `is_visionary` to ensure no other logic paths (e.g., in hiring or marketing) depend on this legacy flag. Remove any that are found.

### Phase 2: Implement Brand-Based Resilience

1.  **Modify Bankruptcy Check**: The primary logic will be in `simulation/components/finance_department.py`, within the `check_bankruptcy` method (or a similar method that tracks consecutive losses).
2.  **Introduce "Resilience" Logic**: The check for bankruptcy will be modified to account for brand strength.

    ```python
    # In simulation/components/finance_department.py
    # Inside a method like check_bankruptcy() or update_solvency()

    # 1. Get Brand Awareness from the firm's BrandManager
    # This requires the FinanceDepartment to have a reference to the firm.
    brand_awareness = self.firm.brand_manager.awareness

    # 2. Calculate resilience bonus ticks
    # The formula is tunable. Start with a simple linear mapping.
    # A resilience_factor of 0.05 means 20 points of awareness forgive 1 loss tick.
    resilience_factor = self.config.get("brand_resilience_factor", 0.05)
    resilience_ticks = int(brand_awareness * resilience_factor)

    # 3. Calculate effective loss ticks
    effective_loss_ticks = self.consecutive_loss_turns - resilience_ticks

    # 4. Check against threshold
    threshold = self.config.bankruptcy_consecutive_loss_threshold
    if effective_loss_ticks >= threshold:
        self.firm.is_bankrupt = True
        # ... bankruptcy logic
    ```

3.  **Configuration**: Add `brand_resilience_factor: 0.05` to the relevant configuration file (e.g., `economy_params.yaml`) to make the new mechanic tunable.

## 3. Verification Plan

1.  **Code Search**: After implementation, verify that no instances of the string `is_visionary` remain in the Python codebase.
2.  **Unit Test (`test_finance_department.py`)**:
    -   **Test Case 1 (Low Brand)**: Create a mock firm with low brand awareness (`awareness = 0`). Simulate consecutive losses and assert that the firm becomes bankrupt exactly at `config.bankruptcy_consecutive_loss_threshold`.
    -   **Test Case 2 (High Brand)**: Create a mock firm with high brand awareness (e.g., `awareness = 40`). Simulate consecutive losses. Assert that the firm survives *past* the default threshold and only goes bankrupt when `effective_loss_ticks` reaches the threshold.
3.  **Simulation Balance Test**:
    -   Run a baseline simulation for 1000 ticks with the old `is_visionary` code and record the total number of firm bankruptcies.
    -   Run the same simulation scenario with the new brand resilience code.
    -   Compare the total number of bankruptcies. The numbers should be in a similar range (e.g., within +/- 20%). If a mass extinction or mass survival event occurs, the `brand_resilience_factor` in the config must be tuned and the test re-run until the simulation is stable.

## 4. Risk & Impact Audit

-   **Critical Risk**: **Simulation Imbalance**. Removing the halo effect without a proper replacement could drastically increase bankruptcies and destabilize the economy.
    -   **Mitigation**: The proposed brand-based resilience mechanism is a direct, tunable replacement. The **Simulation Balance Test** is the key mitigation step. It is mandatory to run this test and analyze its output to ensure the new mechanic is properly calibrated before the change is considered complete.
-   **Architectural Impact**: This change is **positive**. It removes arbitrary, hardcoded rules and replaces them with an emergent property derived from a core simulation system (`BrandManager`), strengthening the integrity of the economic model.

---
# SPEC: TD-006 Dynamic Household Personality

**Objective**: Liquidate technical debt TD-006 and support TD-162 by converting the `Household` agent's static personality into a dynamic trait that adapts to its economic circumstances.

---

## 1. Problem Definition

-   **TD-006 (Static Personality)**: `Household` personality is fixed at initialization, leading to unrealistic behavior where agents do not adapt their core motivations (e.g., a `MISER` remains a miser even when wealthy).
-   **TD-162 (Bloated God Class)**: The `Household` class is a "God Class" undergoing decomposition. New logic must be placed in the correct sub-components, not added to the `Household` facade.

## 2. Implementation Plan

### Phase 1: Enable Dynamic Personality

1.  **Remove `__init__` Parameter**: Delete the `personality: Personality` parameter from the `Household.__init__` method signature in `simulation/core_agents.py`.
2.  **Default Personality**: Set a neutral default personality (e.g., `Personality.BALANCED`) inside `__init__` when initializing the `SocialStateDTO`.
3.  **Update Call Sites**: Find all `Household(...)` instantiation calls and remove the `personality` keyword argument. This will cause intentional compilation/runtime errors that will guide the refactoring.

### Phase 2: Implement Logic in `SocialComponent`

1.  **New Method**: Create a new method in `modules/household/social_component.py`:
    `update_dynamic_personality(social_state: SocialStateDTO, econ_state: EconStateDTO, macro_context: MacroFinancialContext) -> SocialStateDTO`
2.  **Call from `Household`**: This new method should be called once per tick, for example, from within `Household.update_needs`.
3.  **Personality Logic**: The core logic will reside in `update_dynamic_personality`.

    ```python
    # In modules/household/social_component.py

    def update_dynamic_personality(self, social_state: SocialStateDTO, econ_state: EconStateDTO, macro_context: MacroFinancialContext) -> SocialStateDTO:
        """Updates personality based on relative wealth."""

        # Use percentile from macro_context, which should be pre-calculated
        wealth_percentile = macro_context.wealth_percentiles.get(social_state.id, 0.5)

        new_personality = social_state.personality
        
        # Define thresholds in config
        status_seeker_threshold = self.config.personality_status_seeker_wealth_pct
        survival_mode_threshold = self.config.personality_survival_mode_wealth_pct

        if wealth_percentile >= status_seeker_threshold:
            new_personality = Personality.STATUS_SEEKER
        elif wealth_percentile <= survival_mode_threshold:
            # Assume SURVIVAL_MODE is a new Personality enum member
            new_personality = Personality.SURVIVAL_MODE 
        else:
            # Optional: Revert to a base or neutral personality
            # For now, we only change at the extremes.
            pass
        
        if new_personality != social_state.personality:
            social_state.personality = new_personality
            # IMPORTANT: Update desire weights to match the new personality
            social_state.desire_weights = self.config.desire_weights_map.get(new_personality.name)

        return social_state
    ```
4.  **Add `SURVIVAL_MODE`**: Add `SURVIVAL_MODE` to the `Personality` enum in `simulation/ai/enums.py`.
5.  **Configuration**: Add the thresholds and desire weights map to the configuration files.
    -   `personality_status_seeker_wealth_pct: 0.9` (Top 10%)
    -   `personality_survival_mode_wealth_pct: 0.2` (Bottom 20%)
    -   A `desire_weights_map` that links each personality name to its desire weight dictionary.

## 3. Verification Plan

1.  **Unit Test (`test_social_component.py`)**:
    -   **Test Case 1 (Status Seeker)**: Create state DTOs where the agent's wealth percentile in `macro_context` is `0.95`. Call `update_dynamic_personality` and assert that the returned `SocialStateDTO` has `personality = Personality.STATUS_SEEKER`.
    -   **Test Case 2 (Survival Mode)**: Create state DTOs where the agent's wealth percentile is `0.15`. Call the method and assert the personality becomes `Personality.SURVIVAL_MODE`.
    -   **Test Case 3 (No Change)**: Use a wealth percentile of `0.5` and assert the personality does not change from its initial state.
2.  **Integration Test**:
    -   Create a test scenario where a household's assets are manually increased over several ticks.
    -   In each tick, call `update_needs` (which triggers the personality update) and assert that the `household.personality` property changes from `BALANCED` to `STATUS_SEEKER` once its relative wealth crosses the configured threshold.
3.  **Call Site Audit**: The primary verification is to run the entire test suite. The build will fail at every location where `Household` is instantiated with the removed `personality` argument. Each of these failures must be fixed.

## 4. Risk & Impact Audit

-   **Critical Risk**: **Breaking Test and Scenario Setups**. Many existing tests rely on initializing households with a specific personality to create a predictable scenario. Removing the `__init__` argument will break all of them.
    -   **Mitigation**: This is an unavoidable and intended consequence of the refactoring. Test setups must be updated to reflect the new dynamic system. Instead of setting personality directly, tests must now **manipulate the economic state** to *induce* the desired personality.
    -   **Example Fix**:
        -   **Old**: `household = Household(..., personality=Personality.STATUS_SEEKER)`
        -   **New**:
            ```python
            household = Household(...)
            # Manually set high assets and a macro context to force the change
            household._econ_state.assets = 1_000_000
            mock_macro_context = MacroFinancialContext(wealth_percentiles={household.id: 0.95})
            household._social_state = household.social_component.update_dynamic_personality(household._social_state, household._econ_state, mock_macro_context)
            # Now the household is a STATUS_SEEKER for the test
            ```
-   **Architectural Impact**: **Positive**. This change resolves TD-006 and pushes the `Household` class further towards a clean, decomposed state (addressing TD-162) by correctly placing behavioral logic in the `SocialComponent`.

---
# SPEC: TD-122 Test Directory Reorganization

**Objective**: Liquidate technical debt TD-122 by defining and implementing a tiered directory structure for tests, ensuring discoverability and improving project organization.

---

## 1. Problem Definition

-   **TD-122 (Test Directory Fragmentation)**: The current `tests/` directory is flat. It is difficult to distinguish between fast unit tests, slower integration tests, and full system tests. This increases maintenance overhead and developer friction when adding new tests.

## 2. Implementation Plan

### Phase 1: Directory Structure and Configuration

1.  **Create Directories**: Create the following new subdirectories within the `tests/` folder:
    -   `tests/unit/`: For tests of a single class or function in isolation. Must not have external dependencies like files, databases, or network calls. Mocks are used for all collaborators. These should be very fast.
    -   `tests/integration/`: For tests that verify the interaction between two or more components. For example, testing that a `CorporateManager`'s decision correctly creates an `Order` that a `Market` can process. These tests can use fixtures that load data (e.g., `golden_households`) but should not run a full simulation loop.
    -   `tests/system/`: For end-to-end tests. These tests typically run a full simulation for a small number of ticks to ensure all major components of the system work together correctly.

2.  **Update `pytest.ini`**: Modify the `pytest.ini` file in the project root to ensure `pytest` discovers tests in the new directories, while also maintaining discovery in the root for the transition period.

    ```ini
    [pytest]
    # Explicitly define all paths where tests can be found.
    # The root 'tests' is kept for backward compatibility during migration.
    testpaths =
        tests/unit
        tests/integration
        tests/system
        tests
    ```

### Phase 2: Migration Policy and Initial Move

1.  **Document the Policy**: Update the project's primary development guide (e.g., `CONTRIBUTING.md` or `design/2_operations/development_workflow.md`) with the new testing policy.
    -   **Policy Statement**: "All *new* tests must be placed in the appropriate `tests/unit/`, `tests/integration/`, or `tests/system/` subdirectory. Existing tests located in the `tests/` root directory are to be migrated to the new structure only when they are next modified. There will be no dedicated, large-scale effort to move all old tests at once."

2.  **Proof-of-Concept Migration**: To validate the setup, move a small number of existing tests to their new homes:
    -   Find a simple unit test (e.g., `test_some_dto.py`) and move it to `tests/unit/`.
    -   Find a test that uses a fixture like `golden_firms` (e.g., `test_corporate_manager.py`) and move it to `tests/integration/`.
    -   Find a test that runs `Simulation.run_for_n_ticks` and move it to `tests/system/`.

## 3. Verification Plan

1.  **Pytest Discovery**: Run `pytest --collect-only -q` from the project root. The output should list test files from the newly migrated locations as well as from the root `tests/` directory.
2.  **Test Count Verification**:
    -   Run `pytest` *before* the changes and record the total number of tests collected and run.
    -   Run `pytest` *after* the proof-of-concept migration.
    -   Assert that the total number of tests collected and run is identical, proving that no tests were "lost" during the move.
3.  **CI Pipeline Audit**:
    -   Manually inspect the project's CI/CD configuration file (e.g., `.github/workflows/ci.yml`, `azure-pipelines.yml`).
    -   Locate the testing step. Ensure that the command used is generic (e.g., `pytest` or `python -m pytest`) and does not contain a hardcoded path like `pytest tests/`. If it does, remove the explicit path to allow `pytest.ini` to control discovery.

## 4. Risk & Impact Audit

-   **Critical Risk**: **CI Test Blindness**. If the CI/CD script is hardcoded to run tests only in the root `tests/` folder, it will not discover any tests moved or added to the new subdirectories. This would create a silent and critical gap in test coverage.
    -   **Mitigation**: The implementation plan has two key safeguards:
        1.  Using `pytest.ini`'s `testpaths` is the canonical and most robust way to configure test discovery, making it less likely to be overridden.
        2.  The verification plan includes a **mandatory manual audit** of the CI configuration file to find and remove any such hardcoded paths.
-   **Architectural Impact**: **Positive**. This resolves TD-122 and introduces a clean, scalable, and conventional structure for tests, which will improve developer experience and the long-term maintainability of the test suite.
