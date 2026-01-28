# Work Order: WO-103 - Architectural Surgery for Phase 23 Escape Velocity

**Objective:** Execute a three-phase architectural refactoring to eliminate critical-risk bugs causing cascading firm bankruptcies. This surgery will enforce financial integrity, guarantee execution order, and complete the DTO decoupling, creating a stable foundation to achieve Phase 23's "escape velocity" goals.

**Prerequisite:** All findings from `audit_report_01` to `05` are considered binding constraints for this Work Order.

---

## 1. Problem Statement

The simulation is plagued by systemic firm failures that are not driven by legitimate economic conditions but by deep architectural flaws. These include:
1.  **Inaccurate Financial Logic:** Incorrect cost calculations and fragmented financial state management create unpredictable cash drains, leading to premature insolvency.
2.  **Race Conditions:** The implicit and unverified order of operations for transaction settlement and agent liquidation creates a high risk of catastrophic economic inconsistencies.
3.  **Data Flow Corruption:** The incomplete DTO refactoring perpetuates circular dependencies and allows decision logic to bypass core psychological models, invalidating simulation results.

This Work Order provides the definitive implementation plan to surgically remove these defects.

---

## 2. Implementation Plan: A Three-Phase Surgery

### Phase 1: Financial Integrity & SoC (Single-Responsibility)

**Goal:** Establish the `FinanceDepartment` as the immutable, single source of truth for all financial state and operations.

1.  **Centralize Asset Management:**
    -   **Action:** Move the `assets: float` variable from the `Firm` class (`firms.py`) into the `FinanceDepartment` class (`finance_department.py`).
    -   **Constraint:** The `Firm` class may no longer directly modify its cash balance. All debits and credits MUST be processed through new transactional methods in the `FinanceDepartment`.
    -   **Evidence:** `audit_report_03_firm_soc.md`

2.  **Create Transactional Methods:**
    -   **Action:** Implement `debit(amount: float, description: str)` and `credit(amount: float, description: str)` methods within `FinanceDepartment`. These methods will update the internal `_assets` variable and log the transaction, ensuring atomic updates.
    -   **Constraint:** This eliminates the "dual-entry" bug where cash and P&L statements could diverge.
    -   **Evidence:** `audit_report_03_firm_soc.md`

3.  **Delegate Cost Calculations:**
    -   **Action:** Remove the holding cost calculation logic from `firms.py:L452-L454`.
    -   **Action:** The `Firm.pay_holding_costs` method must now call a new `FinanceDepartment.calculate_and_debit_holding_costs()` method. This new method MUST use the `finance.get_inventory_value()` function to calculate costs based on value, not quantity.
    -   **Constraint:** The `Firm` class delegates financial logic; it does not implement it.
    -   **Evidence:** `audit_report_03_firm_soc.md`

4.  **Respect Cash-Flow Insolvency Rule:**
    -   **Constraint:** This refactoring must not alter the core economic rule that inventory has zero liquidation value. Firm survival is determined by cash flow alone. All changes must focus on making cash flow accounting accurate and robust.
    -   **Evidence:** `audit_report_03_firm_soc.md`

### Phase 2: Guaranteed Execution Sequence

**Goal:** Formally codify and enforce the execution order of macro-level systems to eliminate race conditions.

1.  **Refactor `Simulation.run_tick()`:**
    -   **Action:** The (currently unseen) central loop in the `Simulation` class must be explicitly structured to execute in the following, non-negotiable order.
    -   **The Sacred Sequence:**
        1.  `_run_agent_decisions()`
        2.  `_run_market_clearing()`
        3.  `transaction_processor.process()`
        4.  `lifecycle_manager.process_lifecycle_events()`
    -   **Constraint:** This ensures that all financial settlements for a tick are completed *before* any agent is removed from the simulation via bankruptcy or death.
    -   **Evidence:** `audit_report_05_macro_systems.md`

2.  **Create System Service Contracts:**
    -   **Action:** Define `SystemInterface` in `simulation/systems/api.py` with a single method: `execute(sim_state: SimulationState)`.
    -   **Action:** The `TransactionProcessor` and `AgentLifecycleManager` must implement this interface.
    -   **Action:** A new `SimulationState` DTO will be created to pass all necessary data (agents, markets, etc.) from the `Simulation` object to the system services, preventing them from needing to hold a reference to the God `sim` object.
    -   **Constraint:** Systems are stateless services that operate on the state they are given for a single tick.
    -   **Evidence:** `audit_report_05_macro_systems.md`

### Phase 3: DTO Decoupling & Data Flow Purity

**Goal:** Complete the DTO transition to break circular dependencies and ensure decision logic uses the intended data pathways.

1.  **Finalize `DecisionContext` Decoupling:**
    -   **Action:** Modify `DecisionContext` in `simulation/dtos/api.py` as defined in `audit_report_01_core.md`.
        -   **REMOVE** the `household: Optional[Household]` and `firm: Optional[Firm]` fields.
        -   **ADD** `household_state: Optional[HouseholdStateDTO]` and `firm_state: Optional[FirmStateDTO]`.
    -   **Action:** Create the `FirmStateDTO` in `simulation/dtos/api.py` with all the fields specified in the audit report.
    -   **Constraint:** This is an intentionally breaking change that severs the circular dependency between DTOs and agent implementations.
    -   **Evidence:** `audit_report_01_core.md`

2.  **Fix Behavioral Inconsistency:**
    -   **Action:** Refactor `RuleBasedHouseholdDecisionEngine`.
    -   **Action:** The engine MUST stop calling `market.get_best_ask()` directly.
    -   **Action:** It must now retrieve the agent's price perception by querying the `EconComponent` via the household object *before* creating the `DecisionContext`. The "perceived price" should be used to formulate its bid, not the raw market price.
    -   **Constraint:** This ensures agents' psychological models are not bypassed in their most basic decisions.
    -   **Evidence:** `audit_report_04_household_logic.md`

3.  **Modernize the Test Suite:**
    -   **Action:** All tests for decision engines that fail after the `DecisionContext` refactor must be updated.
    -   **Constraint:** Tests must NOT create full mock `Household` or `Firm` objects. Instead, they must instantiate and populate `HouseholdStateDTO` and `FirmStateDTO` objects for test data, passing these into the `DecisionContext`.
    -   **Evidence:** `audit_report_01_core.md`

---

## 3. Verification Plan

1.  **Post-Phase 1:** `pytest` passes. A global search for `.assets` modification outside of `finance_department.py` yields zero results. Simulation runs show more stable firm financials.
2.  **Post-Phase 2:** `pytest` passes. The `Simulation.run_tick` method clearly shows the "Sacred Sequence." A test case where a firm goes bankrupt must prove its final sales transactions were still processed correctly.
3.  **Post-Phase 3:** `pytest` passes. A global search for `context.household` or `context.firm` within any decision engine yields zero results. A new test confirms that the `RuleBasedHouseholdDecisionEngine`'s bid price is different from the market's best ask, reflecting the agent's perception. The full simulation completes without errors.

---

## 🚨 Mandatory Reporting (Jules)

For each Phase of this surgery, you must log any unforeseen side effects or implementation difficulties. Create a new report for each phase (`WO-103-Phase1-Log.md`, `WO-103-Phase2-Log.md`, etc.) in the `communications/insights/` directory. Document any logic that was particularly brittle or hard to refactor, as it may be a candidate for future extraction.
