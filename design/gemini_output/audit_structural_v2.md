# Structural Audit V2 Results

## [God Class Risk List]
Files exceeding 800 lines of code or exhibiting deep inheritance complexity.

*   **CRITICAL**: `simulation/core_agents.py` (900 lines)
    *   *Risk*: High coupling, maintenance difficulty. Contains core `Household` and `Firm` logic which attracts feature creep.
    *   *Recommendation*: Extract sub-components (e.g., specific logic for specialized agent types) or move methods to `System` classes.

*   *Inheritance Depth*: No classes with depth >= 4 were detected in the `simulation/` namespace during this scan.

## [Leaky Abstraction Violations]
Instances where raw Agent objects are passed to Decision Engines or Contexts instead of DTOs (Data Transfer Objects).

*   **DecisionContext Leaks**:
    *   `simulation/firms.py:335`: `DecisionContext` initialized with `government=government`.
        *   *Violation*: Passing the raw `Government` agent exposes methods and mutable state to the decision logic.
    *   `simulation/core_agents.py:737`: `DecisionContext` initialized with `government=government`.
        *   *Violation*: Same as above.

*   **make_decision(self)**:
    *   No instances found where `self` is explicitly passed as an argument to `make_decision`.

## [Sequence Audit: tick_scheduler.py]
Verification of the "Sacred Sequence": **Decisions -> Matching -> Transactions -> Lifecycle**.

*   **Compliance Status**: **Mostly Compliant**, with noted exceptions.
    *   The core loop explicitly calls `_phase_decisions`, `_phase_matching`, `_phase_transactions`, and `_phase_lifecycle` in correct order.

*   **Deviations / Exceptions**:
    1.  **System Transaction Generation (Phase B)**:
        *   Occurs *before* the Decision Phase.
        *   Includes: Firm Production, Bank Interest, Firm Financials (Wages/Dividends), Debt Service, Welfare.
        *   *Impact*: Valid approach for "automatic" transactions, but technically generates financial intent before agents "decide". Firm Production modifies inventory state before `make_decision` sees it.
    2.  **Commerce System (Post-Tick)**:
        *   `state.commerce_system.execute_consumption_and_leisure` runs *after* Lifecycle.
        *   *Impact*: If this system executes financial transactions (buying goods), it effectively occurs outside the "Transactions" phase and potentially bypasses the `TransactionProcessor` batching.
    3.  **Firm Production Side-Effect**:
        *   `firm.produce()` runs in the pre-decision "Phase B".
        *   *Impact*: Inventory state is mutated before the Decision Engine observes the state. This is likely intended (decide based on new stock) but violates "Read-Only Pre-Decision" strictness if strict purity is required.

## [Architecture Debt Priority]
Prioritized actions to resolve identified issues.

1.  **High Priority: Fix Leaky DecisionContext**
    *   **Action**: Create or use `GovernmentStateDTO`.
    *   **Refactor**: Modify `simulation/firms.py` and `simulation/core_agents.py` to convert `government` agent to `GovernmentStateDTO` before passing to `DecisionContext`.

2.  **Medium Priority: Decompose `simulation/core_agents.py`**
    *   **Action**: Refactor `Household` and `Firm` classes.
    *   **Strategy**: Move non-core logic (e.g., specific update routines, complex calculations) into separate `System` classes or `Component` modules. Goal: Reduce file size < 800 lines.

3.  **Low Priority: Formalize Post-Tick Commerce**
    *   **Action**: Review `CommerceSystem`.
    *   **Refactor**: If it generates transactions, move logic to `_phase_decisions` (Households generating "Consumption Orders") and execution to `_phase_transactions`. If it is purely effect-based (utility update), it can remain but should be documented as "State Update" rather than "Commerce".
