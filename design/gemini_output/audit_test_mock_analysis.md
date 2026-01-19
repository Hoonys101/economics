# MagicMock Migration Analysis & Plan

## Executive Summary

The test suite relies heavily on `unittest.mock` (`MagicMock`, `Mock`, `patch`) to isolate components and test logic. While effective, this creates brittleness and a disconnect from real-world agent states. Migrating to a "Golden Fixture" pattern, where tests load pre-recorded, realistic agent data, will improve test reliability and maintainability.

This plan prioritizes migrating tests from simple, data-holding mocks to more complex, behavior-driven mocks. Tests with significant `patch`ing or complex integrations are deferred. Tests related to `Bank` and `FinanceSystem` are flagged for special consideration due to the upcoming WO-081 refactor.

## Mock Usage Analysis

| Test File | Mock Count | Mocked Classes | Difficulty | WO-081 Flag |
| :--- | :--- | :--- | :--- | :--- |
| `test_ai_driven_firm_engine.py` | 2 | `Firm`, `AIEngine` | EASY | No |
| `test_ai_training_manager.py` | 2+ | `Household`, `random` | EASY | No |
| `test_ai_training_manager_new.py`| 1 | `Household` | EASY | No |
| `test_corporate_manager.py` | 2 | `Firm`, `DecisionContext` | EASY | No |
| `test_firm_decision_engine.py` | 1 | `AIEngine` | EASY | No |
| `test_firm_decision_engine_new.py`| 3+ | `Firm`, `AIEngine`, `logging` | EASY | No |
| `test_firm_profit.py` | 2 | `Config`, `DecisionEngine` | EASY | No |
| `test_generational_wealth_audit.py` | 2 | `Household`, `logging` | EASY | No |
| `test_government_ai_logic.py` | 2 | `Government`, `Config` | EASY | No |
| `test_household_ai_consumption.py` | 3 | `HouseholdAI`, `Household`, `Config`| EASY | No |
| `test_household_decision_engine_new.py`| 4+ | `Household`, `HouseholdAI`, `Config`| EASY | No |
| `test_household_system2.py`| 2 | `Household`, `Config` | EASY | No |
| `verify_automation_tax.py` | 3 | `CorporateManager`, `Firm`, `Govt` | EASY | No |
| `verify_leviathan.py` | 1 | `Household` | EASY | No |
| `test_wo065_minimal.py` | 1 | `FinanceSystem` | EASY | Yes |
| `test_agent_lifecycle.py` | 4 | `Household`, `LaborManager`, ... | EASY | No |
| `test_demographics_component.py`| 2 | `Household`, `Config` | EASY | No |
| `test_market_component.py` | 2 | `Household`, `Config` | EASY | No |
| `diagnosis/test_agent_decision.py`| 2 | `DecisionEngine` | EASY | No |
| `test_api_extensions.py` | 4 | `Repo`, `Household`, `Firm`, `Market` | MEDIUM | No |
| `test_dashboard_api.py` | 6 | `Repo`, `Sim`, `Trackers`, `Govt`, `Stock`| MEDIUM | No |
| `test_engine.py` | 5+ | `Household`, `Firm`, `AITrainer`, `Repo`| MEDIUM | Yes |
| `test_finance_bailout.py` | 4 | `Govt`, `CentralBank`, `Bank`, `Firm` | MEDIUM | Yes |
| `test_firms.py` | 3 | `DecisionEngine`, `LoanMarket`, `Bank`| MEDIUM | Yes |
| `test_government_fiscal_policy.py`| 1 | `Firm` | MEDIUM | Yes |
| `test_loan_market.py` | 2+ | `Bank`, `logging` | MEDIUM | Yes |
| `test_stock_market.py` | 2 | `Config`, `Firm` | MEDIUM | No |
| `verify_inheritance.py` | 5 | `Config`, `Sim`, `Govt`, `HH`, `Stock`| MEDIUM | No |
| `verify_mitosis.py` | 2 | `Config`, `DecisionEngine` | MEDIUM | No |
| `modules/finance/test_double_entry.py`| 5 | `Govt`, `CentralBank`, `Bank`, `Firm` | MEDIUM | Yes |
| `modules/finance/test_system.py` | 4 | `Govt`, `CentralBank`, `Bank`, `Firm` | MEDIUM | Yes |
| `test_app.py` | 2+ | `app.get_repository` | HARD | No |
| `test_decision_engine_integration.py` | 2+ | `Firm.make_decision`, `HH.make_decision`| HARD | No |
| `test_fiscal_policy.py` | 1 | `FinanceSystem.issue_treasury_bonds`| HARD | Yes |
| `test_household_ai.py` | 2 | `Market`, `AIEngineRegistry` | HARD | No |
| `test_phase20_integration.py` | 3+ | `Config`, `Engine`, `Households` | HARD | No |
| `test_phase29_depression.py` | 4+ | `Config`, `Household`, `Firm`, `Repo`... | HARD | No |
| `verify_gold_standard.py` | 3+ | `DecisionEngine`, `Firm`, `Household` | HARD | Yes |
| `test_wo058_production.py` | 3 | `Config`, `Repo`, `AITrainer` | HARD | No |
| `test_wo048_breeding.py` | 2 | `config`, `random` | HARD | No |
| `verify_population_dynamics.py` | 1 | `Config` | HARD | No |
| `verify_socio_tech_logic.py` | 1 | `AIDecisionEngine` | HARD | No |
| `test_bank.py` | 2 | `logging`, `ConfigManager` | MEDIUM | Yes |

---

## Migration Plan to Golden Fixtures

The migration will be phased, starting with the tests that have the most straightforward mocks. The `GoldenLoader` utility already exists in `tests/utils/golden_loader.py` and is integrated into `tests/conftest.py`, providing `golden_households` and `golden_firms` fixtures.

### **Phase 1: Easy Targets (Simple Data Mocks)**

These tests use mocks primarily as data containers. Replacing them with golden fixtures will be simple and provide immediate value.

1.  **`test_corporate_manager.py`**:
    *   **Action:** Replace `firm_mock` fixture with `golden_firms[0]`. The test verifies logic within `CorporateManager` that acts on a firm's state. A realistic firm state from a golden fixture is ideal.
2.  **`test_generational_wealth_audit.py`**:
    *   **Action:** Replace `create_mock_household` with the `golden_households` fixture. The test audits a list of households, making it a perfect use case for a realistic, diverse population sample.
3.  **`test_household_decision_engine_new.py`**:
    *   **Action:** The `mock_household` fixture can be replaced by a `golden_households[0]`. This will test the decision engine against a more realistic agent state.
4.  **`test_ai_training_manager_new.py` / `test_ai_training_manager.py`**:
    *   **Action:** Replace `mock_agents` / `mock_households` fixtures with the `golden_households` fixture. These tests evaluate agent performance based on assets, which is a core part of the golden fixture data.
5.  **Component Tests (`/components/*.py`)**:
    *   **Action:** Tests like `test_agent_lifecycle.py` and `test_demographics_component.py` that mock the `owner` can be parameterized to run against each agent in `golden_households`.

### **Phase 2: Medium Targets (Integrated Mocks)**

These tests involve mocks with some behavior or interactions between multiple mocked classes.

1.  **`test_dashboard_api.py`**:
    *   **Action:** This test mocks numerous simulation components. The `mock_households` and `mock_firms` can be directly replaced by `golden_households` and `golden_firms`. This will make the dashboard snapshot test much more representative.
2.  **`test_api_extensions.py`**:
    *   **Action:** Similar to the dashboard test, replace mocked `households` and `firms` with golden fixtures to test the ViewModel logic with realistic data.
3.  **`test_stock_market.py`**:
    *   **Action:** Replace mocked `Firm` instances with `golden_firms` to test IPO and SEO logic against realistic firm financial data.
4.  **`verify_inheritance.py`**:
    *   **Action:** Replace the manually created `deceased` and `heir` mocks with two agents from the `golden_households` fixture. This will test the inheritance logic with real asset, portfolio, and demographic data.

### **Phase 3: Hard Targets & Behavioral Mocks**

These tests mock complex behaviors, use `@patch` extensively, or test high-level integrations. They should be migrated last, as it may require creating new, more complex golden fixtures (e.g., saving a whole `Simulation` object state).

1.  **`test_engine.py`**:
    *   **Action:** This is a high-value target. The `mock_households` and `mock_firms` fixtures should be replaced with `golden_households` and `golden_firms`. The key challenge will be ensuring the mocked `decision_engine` on the golden agents doesn't interfere with the engine's transaction processing logic being tested. The test may need to be refactored to inspect state changes rather than mock calls.
2.  **`test_phase29_depression.py` / `verify_gold_standard.py`**:
    *   **Action:** These are full simulation runs with heavily mocked agent setups. The goal would be to create a "golden simulation" fixture that captures the entire list of households and firms from a specific tick, then load that into a `Simulation` instance for testing specific scenarios. This is the end-state goal for fixture-based testing.
3.  **`test_decision_engine_integration.py`**:
    *   **Action:** This test uses `@patch.object` to mock the `make_decision` method itself. It tests that the market correctly processes the *results* of decisions. It cannot be directly migrated to golden fixtures without changing the nature of the test. A new integration test should be created that uses golden agents with *real* decision engines and asserts the market state.

### **Special Handling: WO-081 Bank Dependencies**

The following files are flagged due to their dependency on `Bank` or `FinanceSystem`. They should be reviewed and potentially refactored after the WO-081 changes are complete. Migration to golden fixtures can proceed, but they may need rework.

*   `test_bank.py`
*   `test_finance_bailout.py`
*   `test_loan_market.py`
*   `test_engine.py`
*   `test_fiscal_policy.py`
*   `modules/finance/test_double_entry.py`
*   `modules/finance/test_system.py`

The priority for these is to first update them for WO-081 compliance, then proceed with the migration plan above where applicable (e.g., replacing the `mock_firm` in `test_finance_bailout.py` with a golden one).
