# Architecture Decision Record: Phase 10 Scalability & Debt Clearance Strategy

**Status**: Proposed

## 1. Context

Phase 9.3 successfully transitioned core agents (`Firm`, `Household`) to a Composition-over-Inheritance model, decoupling them from a monolithic `BaseAgent`. This introduced stateless `Engines` for logic and state-isolating `DTOs` (`FirmStateDTO`, `HouseholdSnapshotDTO`), significantly improving modularity.

However, to maintain backward compatibility and expedite the transition, several pieces of technical debt were intentionally incurred. These now represent the primary blockers to further scalability, testability, and maintainability. This ADR outlines the strategy to systematically eliminate this remaining debt.

The key pieces of debt to be addressed are:
1.  **Compatibility Proxies**: Temporary `firm.hr` and `firm.finance` properties that provide a facade to the old, direct-access patterns.
2.  **Hardcoded Logic**: `Firm.generate_transactions` contains a hardcoded 20% tax rate, making it unresponsive to dynamic government policy.
3.  **Legacy Data Access**: `AnalyticsSystem` uses `getattr` to probe for transient "flow" attributes on agent instances, violating encapsulation and creating implicit, brittle dependencies.
4.  **Lingering `BaseAgent`**: The `simulation/base_agent.py` file still exists, as minor utility agents may still inherit from it, posing a risk of continued use and representing an incomplete refactor.

## 2. Decision

We will execute a targeted refactoring initiative to purge the remaining Phase 9.3 technical debt. This involves:
1.  Eliminating the `HRProxy` and `FinanceProxy` from `firms.py` and updating all call sites to use the new DTO/Engine patterns.
2.  Implementing a formal context-passing protocol to inject dynamic tax rates from the `Government` into the `Firm`.
3.  Standardizing the observation of transient agent data by introducing a dedicated `AgentTickAnalyticsDTO`.
4.  Executing a safe decommissioning protocol to audit all remaining dependencies on `BaseAgent.py` and subsequently delete the file.

This will complete the transition to a pure, scalable, and observable agent architecture.

## 3. Detailed Design & Implementation Strategy

### 3.1. Compatibility Proxy Elimination (`firm.hr`, `firm.finance`)

The `HRProxy` and `FinanceProxy` are critical risks, as they hide the new architecture and allow legacy access patterns to persist. Their removal is the highest priority.

**Implementation Steps:**

1.  **Step 1: Global Call Site Audit**
    -   Execute a codebase-wide search to identify every usage of `firm.hr` and `firm.finance`.
    -   **Command**: `rg "firm\.hr|firm\.finance"`

2.  **Step 2: Refactor Call Sites**
    -   For each identified usage, apply the appropriate modern pattern. External systems should not be aware of "Engines"; they should interact with the `Firm`'s public API or its state DTOs.

    -   **Example 1: Accessing employee count**
        -   **Legacy**: `num_employees = len(firm.hr.employees)`
        -   **Refactored**:
            ```python
            # If you have the firm object and need live data
            state_dto = firm.get_state_dto()
            num_employees = len(state_dto.hr.employees)
            ```

    -   **Example 2: Checking bankruptcy**
        -   **Legacy**: `is_bankrupt = firm.finance.check_bankruptcy()`
        -   **Refactored**:
            ```python
            # The engine logic is now internal to the firm's decision-making.
            # External observers should read the resulting state.
            is_bankrupt = firm.get_state_dto().finance.is_bankrupt
            ```

    -   **Example 3: Accessing financial data in `AnalyticsSystem`**
        -   **Legacy**: `bvps = firm.finance.get_book_value_per_share()`
        -   **Refactored**:
            ```python
            # Use the public method on the Firm orchestrator itself
            bvps = firm.get_book_value_per_share()
            ```

3.  **Step 3: Delete Proxies**
    -   Once the audit is clean and all call sites are refactored, delete the `HRProxy` and `FinanceProxy` classes and the corresponding `@property` methods (`hr`, `finance`) from `simulation/firms.py`.

### 3.2. Dynamic Tax Rate Protocol

To break the hardcoded tax rate dependency, we will implement a "Context over Direct Access" pattern. The simulation orchestrator is responsible for making the `FiscalPolicyDTO` available to all agents that need it.

**Implementation Steps:**

1.  **Step 1: Define Orchestrator Sequence**
    -   The main simulation loop must enforce this order of operations:
        1.  `Government.make_policy_decision()` is called, which determines and updates `government.fiscal_policy: FiscalPolicyDTO`.
        2.  The orchestrator retrieves this DTO.
        3.  The orchestrator creates the `MarketContextDTO` for the current tick, embedding the `FiscalPolicyDTO` within it.
        4.  The orchestrator passes this `MarketContextDTO` to all relevant agents and systems, including `Firm.generate_transactions`.

2.  **Step 2: Update `MarketContextDTO`**
    -   Ensure `modules/system/api.py` (or equivalent) includes the fiscal policy.
        ```python
        # In modules/system/api.py
        class MarketContextDTO(TypedDict):
            # ... other fields
            fiscal_policy: "FiscalPolicyDTO" # Add this
        ```

3.  **Step 3: Refactor `Firm.generate_transactions`**
    -   Modify the method to extract the tax rate from the passed-in context.
    -   **File**: `simulation/firms.py`
    -   **Before**:
        ```python
        def generate_transactions(self, government: ..., market_data: ..., current_time: int, market_context: MarketContextDTO) -> List[Transaction]:
            # ...
            tax_rates = {"income_tax": 0.2} # HARDCODED
            # ...
            fin_ctx = FinancialTransactionContext(
                # ...
                tax_rates=tax_rates,
                # ...
            )
            # ...
        ```
    -   **After**:
        ```python
        def generate_transactions(self, government: ..., market_data: ..., shareholder_registry: IShareholderRegistry, current_time: int, market_context: MarketContextDTO) -> List[Transaction]:
            # ...
            fiscal_policy = market_context.get("fiscal_policy")
            income_tax_rate = fiscal_policy.income_tax_rate if fiscal_policy else 0.2 # Failsafe
            
            # The FinanceEngine expects a dict, we can construct it here
            tax_rates = {"income_tax": income_tax_rate}

            fin_ctx = FinancialTransactionContext(
                # ...
                tax_rates=tax_rates,
                shareholder_registry=shareholder_registry,
                # ...
            )
            # ...
        ```

### 3.3. Analytics Data Normalization

The use of `getattr` in `AnalyticsSystem` is a major architectural smell. We will introduce a dedicated DTO for reporting transient, tick-specific data.

**Implementation Steps:**

1.  **Step 1: Define `AgentTickAnalyticsDTO`**
    -   Create a new DTO to hold "flow" data that is not part of an agent's persistent state but is crucial for analytics.
    -   **Proposed Location**: `modules/analytics/dtos.py`
        ```python
        from typing import TypedDict, Optional
        
        class AgentTickAnalyticsDTO(TypedDict):
            run_id: int
            time: int
            agent_id: int
            labor_income_this_tick: Optional[float]
            capital_income_this_tick: Optional[float]
            # Add other transient metrics as needed
        ```

2.  **Step 2: Agent-Side Population**
    -   Modify `Household` (and other agents) to populate this DTO during their tick processing. This data should be stored temporarily on the agent instance.
        ```python
        # In Household class
        def update_income_and_expenses(self, ...):
            # ... after calculating income
            self.tick_analytics = AgentTickAnalyticsDTO(
                ...,
                labor_income_this_tick=self.labor_income_this_tick,
                capital_income_this_tick=self.capital_income_this_tick
            )
        ```

3.  **Step 3: Refactor `AnalyticsSystem`**
    -   Update `aggregate_tick_data` to read from the clean DTO.
    -   **File**: `simulation/systems/analytics_system.py`
    -   **Before**:
        ```python
        total_labor_income = sum(getattr(h, "labor_income_this_tick", 0.0) for h in world_state.households)
        total_capital_income = sum(getattr(h, "capital_income_this_tick", 0.0) for h in world_state.households)
        ```
    -   **After**:
        ```python
        total_labor_income = sum(
            h.tick_analytics.get("labor_income_this_tick", 0.0)
            for h in world_state.households if hasattr(h, 'tick_analytics')
        )
        total_capital_income = sum(
            h.tick_analytics.get("capital_income_this_tick", 0.0)
            for h in world_state.households if hasattr(h, 'tick_analytics')
        )
        ```

### 3.4. `BaseAgent.py` Decommissioning Protocol

To safely remove `BaseAgent.py`, a strict, auditable protocol is required.

**Implementation Steps:**

1.  **Step 1: Codebase Audit**
    -   Find all files that still import `BaseAgent`.
    -   **Command**: `rg "from simulation.base_agent import BaseAgent"`

2.  **Step 2: Dependency Analysis & Refactoring Mandate**
    -   For each file identified, create a task to refactor the dependent class.
    -   The refactoring must ensure the class no longer inherits from `BaseAgent`.
    -   Instead, it should implement the necessary `Protocol`s (`IOrchestratorAgent`, `IInventoryHandler`, etc.) and use composition for components like `Wallet` and `InventoryManager`, following the pattern set by `Firm` and `Household`.

3.  **Step 3: Verification**
    -   Confirm that all refactoring tasks are complete.
    -   Run the audit command from Step 1 again. It must return zero results.

4.  **Step 4: Deletion**
    -   Only after the audit is clean may the file `simulation/base_agent.py` be deleted from the repository.

## 4. Verification Plan

The success of this refactoring will be verified by:
1.  **Automated Tests**: 100% of the existing test suite (unit, integration) must pass.
2.  **New Unit Tests**: New tests must be added to cover the refactored call sites and ensure they interact correctly with the DTOs and public agent methods.
3.  **Zero-Sum Audit**: `scripts/audit_zero_sum.py` must pass, confirming that the changes have not introduced any monetary leaks into the system.
4.  **Stability Test**: A full 1000-tick simulation run (`scripts/iron_test.py`) must complete without any `AttributeError` or `TypeError` exceptions related to the refactored modules.
5.  **Data Integrity**: Analytics output from the refactored `AnalyticsSystem` must be compared against a baseline run to ensure key indicators (like `total_labor_income`) are still being calculated correctly.
