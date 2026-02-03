# Spec: Test Architecture Refactoring (TD-180, TD-122)

- **Owner**: `antigravity`
- **Jules**: `gemini`
- **Related Tickets**: `TD-180`, `TD-122`
- **Status**: `PROPOSED`

---

## 1. Overview & Goals

This document outlines the mandatory refactoring of the project's test suite. The current primary test for the firm decision engine, `tests/unit/test_firm_decision_engine_new.py`, has exceeded 800 lines and become a "God Object" test, making it unmaintainable and a significant source of technical debt (TD-180). Furthermore, the lack of a clear boundary between unit and integration tests hinders development velocity and clarity (TD-122).

**Goals:**
1.  **Decomposition**: Split `test_firm_decision_engine_new.py` into smaller, domain-focused test files.
2.  **Centralization**: Consolidate monolithic and redundant mock/fixture setup logic into shared `conftest.py` files.
3.  **Clarification**: Establish and enforce a strict boundary and naming convention for `unit` and `integration` tests.
4.  **Stability**: Ensure no loss of test coverage, particularly for complex, inter-dependent decision logic.

## 2. 🚨 Risk & Impact Audit (Pre-flight Analysis)

This refactoring addresses critical architectural risks identified in the pre-flight audit. All work must proceed with the following constraints in mind:

- **Constraint: God Class SUT**: The System Under Test (SUT), `AIDrivenFirmDecisionEngine`, is a "God Class" that orchestrates all firm decisions. The refactoring must therefore be organized by its logical sub-domains (Production, HR, Sales, Finance), even though all tests target the same `make_decisions` method.
- **Risk: Monolithic Fixtures**: The `mock_firm` and `mock_config` fixtures are complex and tightly coupled to the SUT. Centralizing them in `conftest.py` is a **high-risk operation**. Any modification to these shared fixtures could cause cascading failures across the new test files. They must be treated as a critical, high-impact dependency.
- **Risk: Loss of Interaction Coverage**: The current bloated test file implicitly tests the interaction between different decision domains (e.g., how production targets affect hiring). Splitting the file into isolated unit tests risks losing this coverage.
- **Mitigation**: This plan explicitly mandates the creation of a new integration test suite using the existing `golden_*` fixtures to verify complex, cross-domain scenarios, ensuring that the complete output of `make_decisions` remains correct.

## 3. Phase 1: Directory Structure & Naming Conventions

The following structure and conventions are now mandatory.

### 3.1. `tests/unit/`
- **Purpose**: Tests a single class, method, or function in complete isolation. All external dependencies (other classes, I/O, databases) **MUST** be mocked.
- **File Naming**: `test_<module_or_class_name>.py`
- **Directory Structure**: Mirrors the `modules/` directory structure.
- **Example**: A test for `modules/finance/portfolio_manager.py` will be located at `tests/unit/finance/test_portfolio_manager.py`.

### 3.2. `tests/integration/`
- **Purpose**: Tests the interaction between multiple components, modules, or systems. Uses realistic data fixtures (`golden_*`) and may involve limited, controlled I/O.
- **File Naming**: `test_<workflow_or_scenario_name>.py`
- **Directory Structure**: A flatter structure organized by feature or workflow.
- **Example**: A test for the complete household consumption-to-firm-production loop will be at `tests/integration/test_economic_cycle.py`.

## 4. Phase 2: Fixture Centralization

The monolithic fixtures in `test_firm_decision_engine_new.py` will be refactored and moved to a dedicated `conftest.py` file to manage scope and dependencies.

1.  **Create New Config File**: Create `tests/unit/decisions/conftest.py`. This localizes the fixtures and prevents pollution of the root `conftest.py`.

2.  **Migrate and Refactor Fixtures**: Move the following fixtures from `test_firm_decision_engine_new.py` to the new `tests/unit/decisions/conftest.py`:
    - `mock_config` -> Rename to `firm_engine_config`. This fixture is highly specific to the decision engine and should not be confused with the global `mock_config`.
    - `mock_firm` -> Rename to `base_mock_firm`.
    - `mock_ai_engine` -> Keep name.
    - `firm_decision_engine_instance` -> Rename to `ai_decision_engine`. It should be constructed using the other centralized fixtures.
    - `create_mock_state` -> Rename to `create_firm_state_dto`. This is a factory helper and should be clearly named.

## 5. Phase 3: Test File Decomposition

The existing `tests/unit/test_firm_decision_engine_new.py` **MUST** be deleted and replaced by the following domain-specific files within `tests/unit/decisions/`.

1.  **`test_production_rules.py`**:
    - **Responsibility**: Tests related to production target setting.
    - **Tests to Move**: `test_make_decisions_overstock_reduces_target`, `test_make_decisions_understock_increases_target`, `test_make_decisions_target_within_bounds_no_change`, `test_make_decisions_target_min_max_bounds`.

2.  **`test_hr_rules.py`**:
    - **Responsibility**: Tests related to hiring and firing logic.
    - **Tests to Move**: `test_make_decisions_hires_labor`, `test_make_decisions_does_not_hire_when_full`, `test_make_decisions_fires_excess_labor`.

3.  **`test_sales_rules.py`**:
    - **Responsibility**: Tests related to pricing and sales strategy.
    - **Tests to Move**: `test_sales_aggressiveness_impact_on_price`.

4.  **`test_finance_rules.py`**:
    - **Responsibility**: Tests related to corporate finance decisions (investment, dividends).
    - **Tests to Move**: `test_rd_investment`, `test_capex_investment`, `test_dividend_setting`.

## 6. Phase 4: Integration Test Creation

To mitigate the risk of lost interaction coverage, a new integration test suite will be created.

1.  **Create New Integration Test File**: `tests/integration/test_firm_decision_scenarios.py`.

2.  **Implement Scenario Tests**: This file will use the `golden_firms` and `golden_config` fixtures from the root `conftest.py` to test the holistic behavior of `AIDrivenFirmDecisionEngine`.

3.  **Example Test Case**:
    ```python
    import pytest
    from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
    from simulation.dtos import DecisionContext

    def test_growth_scenario_with_golden_firm(golden_firms, golden_config):
        """
        Tests that a healthy firm from a golden snapshot correctly decides
        to invest in capex and hire more employees when presented with
        high demand signals.
        """
        if not golden_firms:
            pytest.skip("Golden fixtures not found.")

        # Arrange: Select a healthy firm and create context
        healthy_firm_mock = golden_firms[0] # Assume first is healthy
        engine = AIDrivenFirmDecisionEngine(ai_engine=Mock(), config_module=golden_config)
        
        # Create a State DTO from the mock
        state = create_firm_state_dto(healthy_firm_mock, golden_config)
        
        # Simulate high demand
        market_data = {"food": {"demand_signal": 1.5}}
        context = DecisionContext(state=state, config=golden_config, market_data=market_data, ...)

        # Act
        output = engine.make_decisions(context)
        orders = output.orders

        # Assert: Check for combined, correct decisions
        assert any(o.order_type == "INVEST_CAPEX" for o in orders)
        assert any(o.order_type == "BUY" and o.item_id == "labor" for o in orders)
        assert not any(o.order_type == "FIRE" for o in orders)
    ```

## 7. Verification Plan

1.  Execute `pytest tests/unit/` and `pytest tests/integration/`. All tests must pass.
2.  Run `ruff check .` and `ruff format .` on all new and modified files. No errors should be reported.
3.  Measure code coverage before and after the refactoring. Coverage must not decrease.
4.  The old file `tests/unit/test_firm_decision_engine_new.py` must be deleted.

## 8. [Routine] Mandatory Reporting

Jules implementing this specification **MUST** create a report detailing any unforseen difficulties, particularly around the monolithic fixture refactoring, and any insights gained about the `AIDrivenFirmDecisionEngine`'s implicit logic.

- **Output File**: `communications/insights/TD-180-Test-Refactor.md`
