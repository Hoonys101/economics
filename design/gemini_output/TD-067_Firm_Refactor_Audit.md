# Report: `Firm` Class Architecture Audit (TD-067)

## Executive Summary
The `simulation/firms.py:Firm` class has been partially refactored into sub-components (`HRDepartment`, `FinanceDepartment`, etc.), but it remains a "God Class" facade, exhibiting significant "Wrapper Bloat" as described in `design/TECH_DEBT_LEDGER.md:TD-067`. A full Separation of Concerns (SoC) refactoring is feasible and recommended, but it carries a significant integration risk, primarily with `simulation/decisions/corporate_manager.py` and its associated tests, which are tightly coupled to the `Firm` object's attributes.

## Detailed Analysis

### 1. God Class & Wrapper Bloat Analysis
- **Status**: ✅ Implemented (Partial Refactor), ⚠️ Bloated Facade
- **Evidence**:
    - The `Firm` class correctly initializes dedicated components for HR, Finance, Production, and Sales (`simulation/firms.py:L90-93`).
    - However, it exposes the internal state of these components through at least **20** `@property` wrappers (`simulation/firms.py:L181-299`). This includes critical state like `employees`, `retained_earnings`, and `current_profit`, creating extensive boilerplate code and hiding the true data owner. This directly corresponds to the "Wrapper Bloat" described in `TD-067`.
    - The `Firm` class still holds significant logic that should belong to its components, such as `calculate_valuation` (`simulation/firms.py:L302`) and `get_book_value_per_share` (`simulation/firms.py:L487`), which are purely financial calculations.
    - The `update_needs` method (`simulation/firms.py:L679`) is a large orchestration method mixing responsibilities from all sub-departments (payroll, marketing, taxes), indicating that the `Firm` class still holds too much process responsibility.

### 2. SoC Refactoring Feasibility
- **Status**: ✅ Feasible
- **Evidence**: The foundational components already exist within the `Firm` class (`simulation/firms.py:L90-93`). The primary task is not creating new components, but rather eliminating the facade (wrapper properties) and forcing external modules to communicate directly with the correct sub-component (`firm.finance` instead of `firm`).

### 3. Integration Risk Assessment
- **Status**: 🔴 High Risk
- **Evidence**:
    - **Test Coupling (`test_corporate_manager.py`)**: The tests for `CorporateManager` are extremely brittle and tightly coupled to the `Firm` object's structure. The `firm_mock` fixture directly sets dozens of attributes on the `Firm` instance (`tests/test_corporate_manager.py:L26-72`). Tests directly assert changes on `firm_mock.assets` and `firm_mock.dividend_rate`, which would break if this state were moved to `firm.finance`.
    - **Module Coupling (`CorporateManager`)**: The `CorporateManager.realize_ceo_actions` method accepts a `Firm` object and directly manipulates its state. A refactor would require this manager to be aware of the sub-components, increasing its complexity or requiring a DTO-based approach.
    - **Fixture Interdependence (`test_firms.py`)**: Tests like `test_book_value_with_liabilities` (`tests/test_firms.py:L48-59`) rely on mocking a chain of objects (`firm.decision_engine.loan_market.bank`). Moving financial logic would require updating these fragile mock chains.

## Risk Audit & Mitigation

*   **Risk: Widespread Test Breakage**
    *   **Description**: Removing wrapper properties will break dozens of tests that directly get/set attributes on `Firm` instances, especially in `test_corporate_manager.py`.
    *   **Mitigation**: The refactoring work must explicitly include a track for refactoring all affected tests. The goal is not to preserve them but to adapt them to the new, correct architecture. This high effort is a necessary part of paying down the technical debt.

*   **Risk: Breaking Dependent Modules**
    *   **Description**: Modules like `CorporateManager` are coupled to the `Firm` facade.
    *   **Mitigation**: A `FirmStateDTO` could be introduced, similar to the `Household` refactor (`design/specs/TD-065_Household_Refactor_Spec.md`), for read operations. However, for write operations, `CorporateManager` must be updated to call the correct sub-component (e.g., `firm.finance.issue_dividend()` instead of `firm.dividend_rate = x`).

## Conclusion & Recommendation
The "Wrapper Bloat" in the `Firm` class is a significant source of technical debt (`TD-067`). While a full SoC refactoring is architecturally sound and feasible, it cannot be done without a concurrent, high-effort refactoring of coupled modules and tests.

**Recommendation**: Proceed with the refactoring by approving the following specification. The work must be planned to include test and module refactoring as a primary task, not an afterthought.

---

# Draft Work Order: TD-067 - Deconstruct `Firm` Facade

**Phase:** 30 (Architecture Refinement)
**Priority:** HIGH
**Prerequisite:** None

## 1. Problem Statement
The `Firm` class (`simulation/firms.py`) acts as a "God Class" facade, violating the Single Responsibility Principle. It proxies dozens of attributes from its own sub-components (e.g., `firm.assets` is an alias for `firm.finance.assets`), resulting in "Wrapper Bloat" (`TD-067`). This creates high maintenance overhead, confuses data ownership, and leads to brittle tests as seen in `tests/test_corporate_manager.py`.

## 2. Objective
Eliminate the facade pattern in the `Firm` class by removing all wrapper properties. External modules and tests **must** be refactored to interact directly with the appropriate sub-component (`firm.hr`, `firm.finance`, `firm.production`, `firm.sales`), enforcing a strict Separation of Concerns.

## 3. Target Architecture
*   **`Firm`**: Becomes a pure orchestrator and container. It owns the components but does not expose their internal state via wrappers.
*   **`FinanceDepartment`**: Assumes sole ownership of all financial state (e.g., `assets`, `retained_earnings`, `profit_history`, `debt`) and financial methods (`calculate_valuation`, `get_book_value_per_share`, `pay_taxes`).
*   **`HRDepartment`, `ProductionDepartment`, `SalesDepartment`**: Sole owners of their respective state and logic.

## 4. Implementation Plan

### Track A: Consolidate Logic into Components
1.  **Move Methods to `FinanceDepartment`**:
    *   Relocate `get_book_value_per_share`, `calculate_valuation`, and `get_financial_snapshot` logic from `Firm` into `FinanceDepartment`.
2.  **Move State to `FinanceDepartment`**:
    *   The `assets` attribute will be moved from `Firm` to `FinanceDepartment`. The `Firm.__init__`'s `initial_capital` will now be passed to the `FinanceDepartment` constructor.
    *   All other financial attributes currently exposed via properties (e.g., `retained_earnings`, `profit_history`) will become direct attributes of `FinanceDepartment`.
3.  **Move State to other Components**:
    *   Ensure all state related to employees, production, and sales resides exclusively within `HRDepartment`, `ProductionDepartment`, and `SalesDepartment` respectively.

### Track B: Eliminate the Facade
1.  **Remove Wrapper Properties from `Firm`**:
    *   Delete all `@property` and `@*.setter` methods in `Firm` that delegate to `self.hr`, `self.finance`, `self.production`, or `self.sales` (`simulation/firms.py:L181-299`).

### Track C: Refactor All Call Sites
1.  **Refactor `CorporateManager`**:
    *   Modify `realize_ceo_actions` to access sub-components directly. For example, `firm.assets` becomes `firm.finance.assets`, and `firm.employees` becomes `firm.hr.employees`.
2.  **Refactor Test Suite**:
    *   Update `tests/test_corporate_manager.py`: Modify the `firm_mock` fixture and all test cases to set and assert values on the sub-components (e.g., `firm_mock.finance.assets = 1000.0`).
    *   Update `tests/test_firms.py`: Adjust tests like `TestFirmBookValue` to call methods on `firm.finance` and to mock dependencies on the sub-components.
3.  **Refactor `Firm` Internals**:
    *   Update methods remaining in `Firm`, such as `make_decision` and `get_agent_data`, to correctly source data from their sub-components.

## 5. Verification Plan
1.  **Update and Execute All Tests**: The primary verification is ensuring the entire modified test suite passes, including the heavily refactored `tests/test_corporate_manager.py` and `tests/test_firms.py`.
2.  **Static Analysis**: Run `ruff` to ensure no unused imports or variables remain after the refactoring.
