# To-Do List: Refactoring to Declarative Transactions (WO-116-B)

## 1. Executive Summary

This document outlines the detailed, module-by-module tasks required to complete the architectural refactoring initiated in WO-116-B. The core objective is to eradicate all direct asset modifications (`_assets +/-=`) and replace them with a declarative `Transaction` intent-generation model. This ensures all financial operations are atomic and processed through the `TransactionProcessor`, guaranteeing zero-sum integrity.

This plan addresses all risks identified in the pre-flight audit, including the phased refactoring of God Classes (`Household`, `Firm`) and the adoption of Behavior Verification in the test suite.

---

## 2. Global Refactoring Mandates

-   **Prohibition**: All direct calls to `_internal_add_assets`, `_internal_sub_assets`, `deposit`, `withdraw`, and `adjust_assets` for inter-agent transfers must be located and removed.
-   **Pattern**: These direct calls must be replaced by methods that **return** a `List[Transaction]`.
-   **Orchestration**: The caller of the refactored method is now responsible for collecting these `Transaction` intents and passing them up to the `TickOrchestrator` to be processed by the `TransactionProcessor`.
-   **Configuration**: All magic numbers (e.g., tax rates, fees, investment amounts) uncovered during refactoring must be externalized to the appropriate `config/*.yaml` file.

---

## 3. Module-by-Module Refactoring Plan

### Module: `simulation.agents`

#### 3.1. `government.py`

The `Government` class is the highest priority as it contains significant architectural violations related to direct asset modification and synchronous bond issuance.

-   **[HIGH] `provide_household_support` & `provide_firm_bailout`:**
    -   **Problem**: These methods currently check the government's asset balance, synchronously issue bonds via `finance_system.issue_treasury_bonds` if funds are low, and then directly modify assets to reflect the spending—all in one monolithic function. This breaks atomicity and the "Intent -> Collect -> Execute" pattern.
    -   **Refactoring**:
        1.  The core logic of these methods should be refactored to **only** generate a `welfare` or `bailout_loan` `Transaction` intent. The `price` of the transaction should be the calculated support amount.
        2.  Remove all internal logic related to checking `self.assets`. The `TransactionProcessor` and `SettlementSystem` are solely responsible for verifying the payer's (Government's) funds during execution.
        3.  Remove the synchronous call to `finance_system.issue_treasury_bonds`. The Government's need for funds must be handled as a separate preceding decision (e.g., in `make_policy_decision`), not as a side-effect of a spending decision.
        4.  The direct modifications (`self.total_spent_subsidies += ...`, `self.expenditure_this_tick += ...`) must be moved to a post-settlement accounting method (e.g., `record_expenditure`) that is called by the `TransactionProcessor` after a transaction is confirmed.
    -   **Config Mapping**:
        -   `modules/government/constants.py` -> `config/economy_params.yaml`: `government.welfare.unemployment_benefit_ratio`, `government.stimulus.gdp_drop_trigger`, `government.stimulus.amount_per_household`.

-   **[MEDIUM] `run_welfare_check` & `invest_infrastructure`:**
    -   **Problem**: These methods orchestrate calls to the violating methods listed above.
    -   **Refactoring**: Update these methods to simply collect the `List[Transaction]` returned by the newly refactored `provide_household_support` and `invest_infrastructure` methods and return them to the `TickOrchestrator`.

#### 3.2. `core_agents.py` (Household)

-   **[LOW] `adjust_assets(self, delta: float)`:**
    -   **Problem**: This method provides a direct, non-atomic way to alter an agent's assets. It is a remnant of the old architecture.
    -   **Refactoring**:
        1.  Locate all callers of `adjust_assets`.
        2.  For each call site, determine the economic event being modeled (e.g., receiving a gift, a system-level injection).
        3.  Refactor the caller to generate an appropriate `Transaction` intent instead. For example, a system-level cash injection should be a transaction with the `CentralBank` as the seller/source.
        4.  Delete the `adjust_assets` method from the `Household` class and its base class.

### Module: `simulation.components`

#### 3.3. `finance_department.py` (Firm)

The `FinanceDepartment` is largely compliant but has one area needing formalization.

-   **[LOW] `pay_ad_hoc_tax`:**
    -   **Problem**: While it correctly uses the `settlement_system`, it directly calls `government.record_revenue`, violating the Saga pattern where the `TaxationSystem` should record revenue only after processor confirmation.
    -   **Refactoring**:
        1.  Remove the call to `government.record_revenue`.
        2.  The `TransactionProcessor`'s handler for the `tax` transaction type must be updated to call `taxation_system.record_revenue` upon successful settlement. This ensures the logic is centralized and correctly sequenced.

### Module: `simulation.systems`

#### 3.4. `lifecycle_manager.py`

-   **[HIGH] `_handle_agent_liquidation`:**
    -   **Problem**: This method currently handles the complex process of agent "death" (bankruptcy/natural death). Part of this process, especially inheritance, involves direct asset transfers that are not yet fully declarative. The call to `inheritance_manager.process_death` is synchronous and complex.
    -   **Refactoring**:
        1.  `inheritance_manager.process_death` must be refactored to return a `List[Transaction]`. These transactions will represent the transfer of the net estate from the deceased agent (or an escrow account) to the heirs and the government (for taxes).
        2.  The `_handle_agent_liquidation` method will collect these transactions. Crucially, these transactions should be added to the `inter_tick_queue` to be processed in the *next* tick's `Phase3_Transaction`. This prevents logical paradoxes where an agent receives an inheritance and spends it in the same tick they died.
    -   **Config Mapping**:
        -   `config.py` -> `config/economy_params.yaml`: `inheritance.tax_rate`, `inheritance.deduction_amount`.

#### 3.5. `immigration_manager.py`

-   **[MEDIUM] `_create_immigrants`:**
    -   **Problem**: The method directly calls `settlement_system.create_and_transfer` to grant initial assets to new immigrants.
    -   **Refactoring**:
        1.  The `process_immigration` method should not trigger the transfer directly.
        2.  It should return a list of newly created `Household` objects *and* a corresponding list of `Transaction` intents for the "immigration_grant".
        3.  The `TickOrchestrator` will be responsible for registering the new agents and queueing the transactions for settlement.

## 4. Test Suite Refactoring Plan

-   **Phase 1 (Containment)**: All existing tests that assert direct asset changes (`assert agent.assets == ...`) must be marked with `@pytest.mark.legacy_state_test`. This acknowledges they are testing deprecated behavior and will be removed or refactored.
-   **Phase 2 (Behavior Verification)**: For every refactored method, a new test must be written. This test will:
    1.  Call the refactored method (e.g., `government.run_welfare_check`).
    2.  Assert the **structure and content** of the returned `List[Transaction]`.
    3.  Verify that the transaction `price`, `buyer_id`, `seller_id`, and `transaction_type` are correct.
    4.  **Crucially, it will assert that the agent's assets have NOT changed.**

This "tell, don't ask" approach to testing aligns the test suite with the new declarative and atomic architecture.
