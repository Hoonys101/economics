# Test Plan: Government Module (TD-229)

## 1. Executive Summary

This document outlines the testing strategy to resolve technical debt item **TD-229**, which highlights the critical lack of test coverage for the `Government` module. The primary goal is to design a robust, multi-layered test suite that ensures the module's correctness, maintainability, and resilience to future changes. This plan is predicated on the architectural refactoring of the `Government` "God Class" into a decoupled set of components, as detailed in related technical debt items (TD-226, TD-227, TD-228).

## 2. Architectural Refactoring Preconditions

This test plan **assumes** the following architectural changes have been implemented. Attempting to apply these tests to the legacy `Government` class is impractical and not recommended.

1.  **Dependency Injection (DI)**: The `Government` agent no longer instantiates its own components (`TaxService`, `WelfareService`, etc.). Instead, these dependencies are injected into its constructor.
2.  **Component Decoupling**: Components like `WelfareService` and `TaxService` no longer hold a reference to the parent `Government` instance, eliminating circular dependencies. They operate on primitive types and Data Transfer Objects (DTOs).
3.  **Single Responsibility Principle (SRP)**: Methods with multiple responsibilities are broken down. For instance, the `run_welfare_check` logic in `Government` is now a pure orchestrator, delegating tax and welfare logic to their respective services. `WelfareService` is refactored into a `WelfareManager` to reflect its broader responsibilities (or its single responsibility is sharpened).

## 3. Phase 1: Component Unit Tests

These tests focus on individual components in complete isolation, using mocked dependencies and data fixtures.

### 3.1. `WelfareManager` (Refactored `WelfareService`)

-   **Objective**: Verify the core logic of welfare distribution, household support, and survival cost calculation.
-   **Dependencies to Mock**: `ISettlementSystem`.
-   **Fixtures**: `golden_households` (from `conftest.py`).

| Test Case ID | Description | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| **WU-WM-001** | Successfully provide welfare to a household below the poverty line. | A household's assets are below `survival_cost`. `ISettlementSystem` will succeed. | `run_welfare_check` is called. | `ISettlementSystem.transfer` is called with the correct subsidy amount. |
| **WU-WM-002** | Do not provide welfare to a household above the poverty line. | A household's assets are above `survival_cost`. | `run_welfare_check` is called. | `ISettlementSystem.transfer` is not called for this household. |
| **WU-WM-003** | Calculate `survival_cost` correctly based on market data. | `market_data` contains a price for `basic_food`. | `get_survival_cost` is called. | The correct survival cost is returned. |
| **WU-WM-004** | Successfully provide discretionary household support. | `ISettlementSystem` will succeed. | `provide_household_support` is called. | `ISettlementSystem.transfer` is called with the specified amount. |
| **WU-WM-005** | Handle `ISettlementSystem` failure during welfare payment. | `ISettlementSystem.transfer` is mocked to return `False`. | `run_welfare_check` is called. | The household's assets remain unchanged and the error is handled gracefully. |

### 3.2. `TaxService`

-   **Objective**: Verify the correctness of all tax calculation and revenue recording logic.
-   **Dependencies to Mock**: None (pure calculation).
-   **Fixtures**: `golden_households`, `golden_firms`.

| Test Case ID | Description | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| **WU-TS-001** | Calculate progressive income tax for a household. | A household with a specific income. | `calculate_tax_liability` is called. | The correct tax amount is returned based on configured tax brackets. |
| **WU-TS-002** | Calculate corporate tax for a profitable firm. | A firm with `revenue > cost`. | `calculate_corporate_tax` is called. | The tax is `(revenue - cost) * corporate_tax_rate`. |
| **WU-TS-003** | Do not calculate corporate tax for a firm with losses. | A firm with `revenue <= cost`. | `calculate_corporate_tax` is called. | The tax amount is `0`. |
| **WU-TS-004** | Calculate wealth tax for a household above the threshold. | A household with `net_worth > wealth_tax_threshold`. | `calculate_wealth_tax` is called. | The correct tax on assets above the threshold is returned. |
| **WU-TS-005** | Record revenue from a successful tax collection result. | A `TaxCollectionResult` with `success=True`. | `record_revenue` is called. | `total_collected_tax` and `tax_revenue` breakdown are updated correctly. |
| **WU-TS-006** | Do not record revenue from a failed tax collection result. | A `TaxCollectionResult` with `success=False`. | `record_revenue` is called. | Internal ledgers are not changed. |

### 3.3. `PolicyLockoutManager`

-   **Objective**: Verify that policy tags can be locked and checked correctly.
-   **Dependencies to Mock**: None.

| Test Case ID | Description | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| **WU-PL-001** | A policy is locked for a specific duration. | Current tick is 100. | `lock_policy(KEYNESIAN_FISCAL, 20, 100)` is called. | `is_locked(KEYNESIAN_FISCAL, 110)` returns `True`. |
| **WU-PL-002** | A policy lock correctly expires. | Policy was locked at tick 100 for 20 ticks. | `is_locked` is checked at tick 121. | `is_locked(KEYNESIAN_FISCAL, 121)` returns `False`. |
| **WU-PL-003** | Checking a policy that was never locked. | No lock has been set for `AUSTRIAN_AUSTERITY`. | `is_locked(AUSTRIAN_AUSTERITY, 100)` is called. | The method returns `False`. |

## 4. Phase 2: Integration & Regression Tests

These tests verify the interactions between the `Government` orchestrator and its components.

### 4.1. Government & Component Integration

-   **Objective**: Ensure the `Government` agent correctly delegates tasks to its components.

| Test Case ID | Description | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| **INT-GC-001** | `run_welfare_check` orchestrates tax and welfare. | Mocked `TaxService` and `WelfareManager`. | `Government.run_welfare_check` is called. | Both `TaxService.calculate_wealth_tax` and `WelfareManager.run_welfare_check` are called. |
| **INT-GC-002** | `provide_firm_bailout` integrates with `FinanceSystem`. | A solvent firm and a mocked `FinanceSystem`. | `Government.provide_firm_bailout` is called. | `FinanceSystem.grant_bailout_loan` is called and transactions are returned. |
| **INT-GC-003** | `invest_infrastructure` integrates with `InfrastructureManager`. | Mocked `InfrastructureManager`. | `Government.invest_infrastructure` is called. | `InfrastructureManager.invest_infrastructure` is called. |

### 4.2. Regression: Policy Lockout & Political Ideology

-   **Objective**: Create regression tests for complex, state-dependent policy logic.

| Test Case ID | Description | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| **REG-PL-001** | **(Scapegoat Lockout)** Firing an advisor blocks associated policies. | `Government.fire_advisor(EconomicSchool.KEYNESIAN)` is called at tick 100. | `provide_household_support` is attempted at tick 105. | The `WelfareManager` method is not called and no support is given. |
| **REG-PI-002** | **(Political Influence)** Ruling party affects policy decisions. | Mock `AdaptiveGovPolicy` to capture the `fiscal_stance` passed to it. | 1. Set `ruling_party=RED`. <br> 2. Call `make_policy_decision`. <br> 3. Set `ruling_party=BLUE`. <br> 4. Call `make_policy_decision`. | The decisions from the policy engine reflect the political bias (e.g., austerity vs. stimulus multipliers). |

## 5. Test Coverage Strategy (Path to 80%)

1.  **Step 1: Foundational Unit Tests (Coverage: 0% -> 45%)**
    -   Implement all unit tests outlined in **Phase 1** for `WelfareManager`, `TaxService`, and `PolicyLockoutManager`. This establishes a baseline of correctness for the core, decoupled logic.

2.  **Step 2: Critical Path Integration Tests (Coverage: 45% -> 65%)**
    -   Implement the integration tests from **Phase 2**, focusing on the main orchestration flows within the `Government` agent (`run_welfare_check`, `provide_firm_bailout`, `make_policy_decision`).
    -   Implement the regression tests for policy lockouts and political influence.

3.  **Step 3: Edge Case & Failure Mode Analysis (Coverage: 65% -> 75%)**
    -   Add tests for scenarios with insufficient government funds for welfare or bailouts.
    -   Add tests where `market_data` is missing expected keys (e.g., `basic_food_current_sell_price`).
    -   Add tests for the legacy `Government.collect_tax` adapter to ensure backward compatibility during transition.
    -   Add tests for `update_public_opinion` and `check_election` logic.

4.  **Step 4: Full Scenario & Configuration Testing (Coverage: 75% -> 80%+)**
    -   Create parameterized tests that run key scenarios under different `config_module` settings (e.g., `GOVERNMENT_POLICY_MODE` set to `AI_ADAPTIVE` vs. `TAYLOR_RULE`).
    -   Test scenarios involving portfolio management (`receive_portfolio`, `get_portfolio`).
    -   Add tests for public education (`run_public_education`).

## 6. Risk & Impact Audit

-   **Test Brittleness & Refactoring**: The existing tests in `test_tax_collection.py` are integration tests, not unit tests. They are tightly coupled to the `Government` God Class and **will break** during the refactoring process. They must be **deleted or completely rewritten** as proper integration tests that use a fully instantiated (but mocked) `Government` agent post-refactoring.
-   **Refactoring Dependency**: This test plan is **strictly contingent** on the successful completion of architectural refactoring (TD-226, TD-227, TD-228). Attempting to implement this suite on the current codebase will reinforce existing anti-patterns and result in a brittle, unmaintainable test suite.
-   **Mocking Strategy**: To mitigate test fragility, `MagicMock` should be avoided for complex objects like `Household` or `Firm`. Instead, the project's `golden_households` and `golden_firms` fixtures must be used. Mocking should be confined to well-defined interfaces like `ISettlementSystem` and `IFinanceSystem`.
