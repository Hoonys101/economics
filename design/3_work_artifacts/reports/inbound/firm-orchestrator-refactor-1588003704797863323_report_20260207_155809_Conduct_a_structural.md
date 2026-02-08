# Report: Decoupling Strategy for HR and Finance Departments

## Executive Summary

The `HRService` and `TaxService` (acting as HR and Finance departments) are tightly coupled to the `Firm` agent, directly accessing its state and the state of other agents, which violates the "Purity Gate" principle outlined in `ARCH_AGENTS.md`. This report details these violations and proposes a decoupling strategy using Agent IDs and Data Transfer Objects (DTOs) to align with architectural standards and resolve technical debt issue TD-276.

## Detailed Analysis

### 1. `HRService` (`modules/hr/service.py`)

-   **Status**: ❌ Violation
-   **Evidence**: The `calculate_liquidation_employee_claims` method exhibits direct access to live agent objects and their state.
    -   `modules/hr/service.py:L33`: Iterates directly over a list of employee objects (`for employee in firm.hr.employees:`). These `employee` objects are presumed to be `Household` agents.
    -   `modules/hr/service.py:L35`: Accesses internal state of an employee object (`getattr(employee._econ_state, 'employment_start_tick', -1)`).
    -   `modules/hr/service.py:L14`, `L20`, `L43`: Accesses state on sibling components through the parent `firm` reference (e.g., `firm.hr.unpaid_wages`, `firm.hr.employee_wages`).
-   **Notes**: This implementation is a clear example of the "Stateful Components" risk described in `ARCH_AGENTS.md`, where components have unrestricted access to the parent's state, leading to hidden dependencies and making isolated testing impossible.

### 2. `TaxService` (`modules/finance/service.py`)

-   **Status**: ⚠️ Partial Violation
-   **Evidence**: The `calculate_liquidation_tax_claims` method directly accesses its parent `Firm`'s state.
    -   `modules/finance/service.py:L20`: Reads profit directly from a sibling component attached to the `Firm` object (`firm.finance.current_profit`).
-   **Notes**: While this service does not iterate over other agents like `HRService` does, it still relies on the tightly coupled "parent pointer" pattern to function, preventing it from being used as a pure, stateless function.

## Decoupling Strategy (TD-276 Resolution)

To align with the "Purity Gate" principle and resolve TD-276, the following decoupling strategy is proposed:

### 1. Isolate Services from Live Objects

-   **Action**: Refactor service methods to operate on primitive types and DTOs instead of `Firm` objects. The parent object's ID should be passed for context.

-   **Example: `HRService`**
    -   **Current**: `calculate_liquidation_employee_claims(self, firm: Firm, ...)`
    -   **Proposed**:
        ```python
        class EmployeeInfoDTO:
            id: AgentID
            employment_start_tick: int
            current_wage: float

        calculate_liquidation_employee_claims(
            self,
            firm_id: AgentID,
            employees: List[EmployeeInfoDTO],
            unpaid_wages: Dict[AgentID, List[Tuple[int, float]]],
            config: FirmConfigDTO,
            ...
        )
        ```

-   **Example: `TaxService`**
    -   **Current**: `calculate_liquidation_tax_claims(self, firm: Firm)`
    -   **Proposed**:
        ```python
        calculate_liquidation_tax_claims(
            self,
            firm_id: AgentID,
            current_profit: float,
            tax_rate: float,
            ...
        )
        ```

### 2. Introduce a Data Assembler/Broker

-   **Action**: The responsibility of gathering data and constructing DTOs should be moved out of the services and into a higher-level orchestrator or manager (e.g., a `LiquidationSaga` or `FirmLifecycleManager`).
-   **Workflow**:
    1.  The orchestrator receives a `firm_id` for liquidation.
    2.  It queries the necessary agent registries and data sources to gather information about the firm's employees, finances, and configuration.
    3.  It assembles this raw data into the required DTOs (`EmployeeInfoDTO`, `FirmConfigDTO`, etc.).
    4.  It calls the now-decoupled `HRService` and `TaxService` methods, passing the pure DTOs as arguments.

## Risk Assessment

-   **Refactoring Cost**: This is a significant refactoring that will touch all call sites of the affected service methods.
-   **Circular Dependencies**: The current model's risk of circular imports, as noted in `ARCH_AGENTS.md`, will be eliminated for these components as they will no longer need to import `Firm`.
-   **Performance**: There may be a minor performance overhead from creating DTOs, but this is an acceptable trade-off for the gains in modularity, testability, and architectural integrity.

## Conclusion

The current implementation of `HRService` and `TaxService` directly contravenes the project's architectural principles by accessing live agent objects, creating tight coupling and significant technical debt. By refactoring these services to operate on Agent IDs and DTOs, we can restore them to the intended "Purity Gate" standard, improve testability, and formally resolve the structural issues identified in ticket TD-276. This change is critical for the long-term maintainability and stability of the agent system.