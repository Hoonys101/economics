# Work Order: TD-067 - Refactoring `Firm` God Class (Phase B/C)

**Phase:** 31 (Golden Fixture & Stability)
**Priority:** HIGH
**Prerequisite:** TD-067 Phase A (FinanceDepartment extraction)

## 1. Problem Statement
The `Firm` class in `simulation/firms.py` remains a "God Class" despite the initial extraction of sub-components. It acts as a bloated facade, exposing over 20 wrapper properties that simply delegate to its internal `hr` and `finance` components. This violates the Single Responsibility Principle (SRP) and creates significant code duplication and maintenance overhead, as identified in technical debt item `TD-067`. Furthermore, the `CorporateManager` is tightly coupled to the `Firm`'s internal state, containing business logic that it should not own and directly manipulating `Firm` attributes, which is a critical architectural violation.

This refactoring aims to complete the work of TD-067 by removing the facade, enforcing strict SoC, and establishing a clean, command-based interaction pattern between the `CorporateManager` and the `Firm`'s specialist components.

## 2. Objective
1.  **Eliminate Wrapper Bloat**: Completely remove all delegating `@property` getters and setters from the `Firm` class.
2.  **Enforce Strict SoC**: Move all business logic for state changes out of `CorporateManager` and into the correct `Firm` sub-component (`ProductionDepartment`, `FinanceDepartment`, etc.).
3.  **Establish Command-Based API**: All state modifications must occur via explicit, high-level methods on the sub-components (e.g., `firm.production.invest_in_automation(...)`), not direct attribute access.
4.  **Refactor All Call Sites**: Update all external modules, tests, and scripts that currently use the wrapper properties to use the new, explicit component API. This is a **deliberate and necessary breaking change**.

## 3. Target Architecture
*   **`Firm` (The Orchestrator)**:
    *   Owns `HRDepartment`, `FinanceDepartment`, `ProductionDepartment`, `SalesDepartment`.
    *   **NO wrapper properties.**
    *   Exposes its components directly for data queries (e.g., `firm.finance.get_financial_snapshot()`).
    *   Receives tactical orders from `CorporateManager` and delegates them to the appropriate component.
*   **`CorporateManager` (The Strategist -> Tactician)**:
    *   Translates the AI's strategic `FirmActionVector` into a sequence of high-level commands.
    *   **Contains NO business logic.** It does not know *how* an investment is calculated or its effect on state.
    *   Only calls methods on the `Firm`'s components (e.g., `firm.production.invest_in_r_and_d(...)`). It **MUST NOT** modify any `firm` attribute directly.
*   **`FinanceDepartment`, `ProductionDepartment`, `HRDepartment` (The Specialists)**:
    *   Own their respective state (e.g., `FinanceDepartment` owns `assets`, `profit_history`).
    *   Contain all business logic for state changes (e.g., `ProductionDepartment` contains the logic for R&D success chance and cost calculation).
    *   Provide a high-level, atomic API for state modifications (e.g., `invest_in_automation(amount)`).

---

## 4. Implementation Plan

### Track A: Component API Hardening (The New Contract)
1.  **`simulation/components/production_department.py`**:
    *   Create a new method `invest_in_r_and_d(budget: float, avg_skill: float, current_time: int) -> bool` that encapsulates the entire "Innovation Physics" logic (success chance, state update) currently in `CorporateManager._manage_r_and_d`.
    *   Create a new method `invest_in_capex(budget: float, reflux_system: Any, current_time: int)`.
    *   Create a new method `invest_in_automation(budget: float, guidance_gap: float, government: Any, current_time: int)`.
2.  **`simulation/components/finance_department.py`**:
    *   Create a new method `set_dividend_rate(rate: float)`.
    *   Ensure methods exist for all financial state queries (e.g., `get_retained_earnings()`, `get_current_profit()`).
3.  **`simulation/components/hr_department.py`**:
    *   Create a new method `layoff_employees(count: int, severance_weeks: int, current_time: int)`.
    *   Create a new method `post_hiring_orders(count: int, wage_offer: float) -> List[Order]`.

### Track B: `CorporateManager` Decoupling
1.  **Refactor `simulation/decisions/corporate_manager.py`**:
    *   Go through each `_manage_*` method.
    *   Remove all business logic for cost calculation, success chance, and state modification.
    *   Replace direct `firm.assets -= ...`, `firm.capital_stock += ...`, etc., with calls to the new high-level methods defined in Track A.
    *   **Example (`_manage_r_and_d`)**: The method will now only determine the *budget* based on the aggressiveness vector and then call `firm.production.invest_in_r_and_d(budget, ...)`. All logic for `random.random()`, `firm.base_quality += ...`, etc., will be gone from this file.
    *   **Example (`_manage_hiring`)**: The method will calculate `needed_labor` and then call `firm.hr.layoff_employees(...)` or `firm.hr.post_hiring_orders(...)`. All logic for severance pay calculation and modifying the `firm.employees` list will be gone.

### Track C: Global Call Site Refactoring (The Breaking Change)
1.  **Identify All Usages**: Systematically find every file in the project that accesses a `Firm` wrapper property (e.g., `firm.employees`, `firm.retained_earnings`, `firm.current_profit`).
2.  **Refactor Test Code**:
    *   Update all test setup and assertions.
    *   `firm.employees = [...]` becomes `firm.hr.employees = [...]`.
    *   `assert firm.current_profit == 100` becomes `assert firm.finance.current_profit == 100`.
3.  **Refactor Simulation Code**:
    *   Update `simulation/systems/`, `simulation/decisions/`, `scripts/`, and any other module that accesses the deprecated properties.
    *   `firm.employees.remove(emp)` becomes `firm.hr.remove_employee(emp)`.
    *   `if firm.current_profit > 0:` becomes `if firm.finance.current_profit > 0:`.
4.  **Refactor `clone()` method**: The `firm.clone()` method must be updated to correctly initialize the sub-departments of the new firm instance, rather than setting properties on the top-level object.

### Track D: `Firm` Class Cleanup
1.  **Delete Wrapper Properties**: Once all call sites in Track C are refactored, delete all 20+ `@property` getters and setters from `simulation/firms.py`. The `Firm` class should be significantly smaller.

---

## 5. Verification Plan
1.  **Unchanged Tests are the Goal**: A successful refactoring will result in **zero functional changes** to the simulation's behavior. Therefore, all existing tests in `tests/` should pass *after* their call sites have been updated in Track C.
2.  **New Component Tests (Optional but Recommended)**: Add specific unit tests for the new command methods in `test_production_department.py`, etc., to verify their internal logic (e.g., test the R&D success calculation in isolation).
3.  **Run Full Test Suite**: Execute the entire `pytest` suite. The final result must be 100% pass rate.

---

## 6. 🚨 Risk & Impact Audit (TD-067 Phase B/C)

*   **Risk: Systemic Test Failure (DELIBERATE)**
    *   **Mitigation**: This is an intentional breaking change. **Track C is the most critical and time-consuming part of this work order.** Every test that fails due to a removed property must be manually updated to use the new component API (`firm.finance.get_retained_earnings()`, `firm.hr.employees`, etc.). There is no alternative.

*   **Risk: Logic Regression into `CorporateManager`**
    *   **Mitigation**: The implementation **must** adhere to the strict unidirectional dependency outlined in the architecture. `CorporateManager` is a *caller*, not an *implementer*. All business logic (IF statements, calculations, random checks) related to the *consequences* of a decision must be moved to a `Firm` sub-component. This will be strictly enforced during code review.

*   **Risk: Inconsistent State from Non-Atomic Operations**
    *   **Mitigation**: Track A explicitly requires creating high-level, atomic "command" methods. For example, `invest_in_automation` **must** handle asset reduction, automation level increase, and tax payment within a single, unified method on the `ProductionDepartment`. This ensures the `Firm`'s state can never be partially updated.

*   **Constraint: NO MORE PROPERTY WRAPPERS**
    *   **Mitigation**: This refactoring explicitly forbids the Facade pattern used in TD-065. The goal of TD-067 is to **remove the facade**. The public API of the `Firm` class is being changed, and all client code must be updated. No new properties are to be added to `Firm`.

---
## 7. Inventory of Changes

### Wrapper Properties to be Removed

| Property Name | Target Component | External Usages | Risk |
| :--- | :--- | :--- | :--- |
| `employees` | `hr` | HIGH (Dozens) | **HIGH** |
| `employee_wages` | `hr`| HIGH | **HIGH** |
| `retained_earnings`| `finance`| HIGH | **HIGH** |
| `dividends_paid_last_tick`|`finance` | LOW | LOW |
| `consecutive_loss_turns`| `finance` | MEDIUM | MEDIUM |
| `current_profit`| `finance` | HIGH | **HIGH** |
| `revenue_this_turn`| `finance` | HIGH | **HIGH** |
| `cost_this_turn`| `finance` | MEDIUM | MEDIUM |
| `revenue_this_tick`| `finance` | MEDIUM | MEDIUM |
| `expenses_this_tick`| `finance` | MEDIUM | MEDIUM |
| `profit_history`| `finance` | HIGH | **HIGH** |
| `last_revenue`| `finance` | MEDIUM | MEDIUM |
| `last_marketing_spend`| `finance` | MEDIUM | MEDIUM |
| `last_daily_expenses`| `finance` | LOW | LOW |
| `last_sales_volume`| `finance` | LOW | LOW |
| `sales_volume_this_tick`| `finance` | MEDIUM | MEDIUM |

### `CorporateManager` Logic to be Moved

| `CorporateManager` Method | Direct State Manipulation / Logic | Proposed New Method (on Firm Component) |
| :--- | :--- | :--- |
| `_manage_automation` | `firm.assets -= ...`, `firm.automation_level += ...` | `firm.production.invest_in_automation(budget, ...)` |
| `_manage_r_and_d` | `firm.assets -= ...`, `firm.base_quality += ...`, `random.random()` | `firm.production.invest_in_r_and_d(budget, ...)` |
| `_manage_capex` | `firm.assets -= ...`, `firm.capital_stock += ...` | `firm.production.invest_in_capex(budget, ...)` |
| `_manage_dividends` | `firm.dividend_rate = ...` | `firm.finance.set_dividend_rate(rate)` |
| `_manage_hiring` (Layoffs) | `firm.assets -= severance_pay`, `emp.quit()` | `firm.hr.layoff_employees(count, ...)` |
| `_manage_hiring` (Hiring) | Creates `Order` objects directly | `firm.hr.post_hiring_orders(count, wage)` |
| `_attempt_secondary_offering`| Creates `StockOrder` directly | `firm.finance.issue_treasury_shares(quantity, price)` |
