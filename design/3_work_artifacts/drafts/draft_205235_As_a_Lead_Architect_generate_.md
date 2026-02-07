# modules/hr/api.py

```python
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, Protocol, TypedDict, Union
from dataclasses import dataclass, field

from modules.system.api import CurrencyCode, MarketContextDTO

# =================================================================
# 1. Service Protocols (Interfaces for Dependency Injection)
# =================================================================

class FinanceService(Protocol):
    """
    Defines the financial operations HR department can request.
    This is a handle to the firm's Finance department, abstracting its implementation.
    """
    def get_total_liquid_assets_in_primary_currency(self) -> float:
        """Calculates the firm's total assets convertible to the primary currency."""
        ...

    def get_balance(self, currency: CurrencyCode) -> float:
        """Gets the current balance for a specific currency."""
        ...

    def pay_severance(self, employee_id: int, amount: float, currency: CurrencyCode) -> bool:
        """
        Executes a severance payment. Returns True on success.
        This is a transactional method that will cause a side effect.
        """
        ...


class TaxService(Protocol):
    """
    Defines the tax calculation operations the HR department needs.
    This is a handle to the Government agent or a tax calculation utility.
    """
    def get_survival_cost(self, market_data: Dict[str, Any]) -> float:
        """Gets the baseline cost of living for tax calculations."""
        ...

    def calculate_income_tax(self, gross_income: float, survival_cost: float) -> float:
        """Calculates the income tax amount for a given gross income."""
        ...


# =================================================================
# 2. Data Transfer Objects (DTOs for State & Configuration)
# =================================================================

@dataclass(frozen=True)
class HRConfigDTO:
    """Configuration data relevant to the HR Department."""
    halo_effect: float
    labor_market_min_wage: float
    severance_pay_weeks: int
    ticks_per_year: int
    default_currency: CurrencyCode


@dataclass(frozen=True)
class EmployeeStateDTO:
    """A snapshot of an employee's state required for HR processing."""
    id: int
    employer_id: int
    is_employed: bool
    labor_skill: float
    education_level: int
    # New field to replace direct access to wage dict
    base_wage: float


@dataclass(frozen=True)
class PayrollContextDTO:
    """All necessary inputs for the process_payroll method."""
    current_time: int
    employees: List[EmployeeStateDTO]
    config: HRConfigDTO
    market_context: MarketContextDTO
    market_data: Dict[str, Any] # For survival cost, may be refined later
    finance_service: FinanceService
    tax_service: TaxService


# =================================================================
# 3. Action DTOs (Declarative Outputs)
# =================================================================

@dataclass(frozen=True)
class PayWageAction:
    """Action to pay a net wage and withhold taxes."""
    employee_id: int
    gross_wage: float
    net_wage: float
    income_tax: float
    tax_recipient_id: int
    currency: CurrencyCode


@dataclass(frozen=True)
class RecordUnpaidWageAction:
    """Action to record a wage that could not be paid due to illiquidity."""
    employee_id: int
    wage_amount: float
    tick: int
    currency: CurrencyCode


@dataclass(frozen=True)
class ExecuteSeveranceAction:
    """Action to fire an employee and execute a severance payment."""
    employee_id: int
    severance_pay: float
    currency: CurrencyCode


@dataclass(frozen=True)
class FireWithoutSeveranceAction:
    """Action to fire an employee when severance cannot be afforded."""
    employee_id: int


# A union of all possible actions HR can request
HRAction = Union[
    PayWageAction,
    RecordUnpaidWageAction,
    ExecuteSeveranceAction,
    FireWithoutSeveranceAction
]


@dataclass(frozen=True)
class PayrollProcessingResult:
    """The complete, declarative result of a payroll cycle."""
    actions: List[HRAction] = field(default_factory=list)


# =================================================================
# 4. Decoupled HR Department Interface
# =================================================================

class IHRDepartment(Protocol):
    """
    Decoupled interface for the HR Department.
    It operates on DTOs and Service Handles, with no direct reference to a Firm.
    """

    def calculate_wage(
        self,
        employee: EmployeeStateDTO,
        config: HRConfigDTO,
    ) -> float:
        """Calculates wage based on skill and halo effect."""
        ...


    def process_payroll(self, context: PayrollContextDTO) -> PayrollProcessingResult:
        """
        Processes payroll based on the provided context and returns a list of declarative actions.
        This method is now a pure function with no side effects.
        """
        ...
```

# design/3_work_artifacts/specs/hr_decoupling_spec.md

```markdown
# Spec: HRDepartment Decoupling & Service-Oriented Refactor

## 1. Overview
This document outlines the technical specification for decoupling the `HRDepartment` from the `Firm` agent. The primary goal is to eliminate all direct parent references (`self.firm`) and transform the department into a modular, testable component that operates on Data Transfer Objects (DTOs) and explicit Service Handles.

This is a **major architectural refactor**, not an incremental change. It directly addresses the high-risk technical debt identified in `ARCH_AGENTS.md` and the `Domain_Auditor` pre-flight check, moving the `Firm` agent towards a more robust and maintainable service-oriented architecture.

## 2. 🚨 Addressing Pre-flight Audit Risks

This refactor is a direct response to the critical risks identified. Here is how each is addressed:

### 2.1. On: The "Single Inseparable Unit" Principle
- **Acknowledgement**: We acknowledge this refactor directly challenges the documented "pragmatic" state of the `Firm` agent in `ARCH_AGENTS.md`.
- **Justification**: The "inseparable unit" has proven to be a significant source of hidden dependencies, untestability, and architectural fragility. The cost of maintaining this tight coupling now outweighs the initial implementation convenience. This "controlled demolition" is a strategic investment to reduce cognitive overhead, improve testability, and enable safer future modifications.

### 2.2. On: Financial Action Dependency
- **Problem**: `HRDepartment` needs to perform financial *actions* (e.g., check solvency, pay severance), not just read state.
- **Solution**: We will introduce a `FinanceService` protocol (see `modules/hr/api.py`). The `Firm`'s `FinanceDepartment` will implement this protocol. `HRDepartment` will be given a handle to this service during initialization, allowing it to *request* financial operations without being coupled to the implementation.

### 2.3. On: Guaranteed Test Suite Breakage
- **Problem**: Existing tests instantiate a full `Firm` to test HR logic. These will all fail.
- **Solution**: The verification plan (Section 6) outlines a three-pronged approach:
    1.  **New Unit Tests**: `HRDepartment` will get its own test suite (`tests/modules/hr/test_hr_department.py`). These tests will use a `MockFinanceService` and `MockTaxService` for complete isolation.
    2.  **Test Refactoring**: Existing `Firm` tests related to payroll will be refactored to check that the `Firm` correctly executes the `HRAction` objects returned by the new `process_payroll`.
    3.  **Deprecation**: Old, brittle tests that are now redundant will be removed.

### 2.4. On: Unmanaged Side Effects & SRP Violation
- **Problem**: `HRDepartment` directly modifies other agents (e.g., `employee.quit()`).
- **Solution**: The refactored `HRDepartment` will be a **pure function**. It will not cause any side effects. Instead, its `process_payroll` method will return a `PayrollProcessingResult` DTO containing a list of declarative `HRAction`s (e.g., `ExecuteSeveranceAction`, `RecordUnpaidWageAction`). The `Firm` agent will be responsible for interpreting and executing these actions.

## 3. API & DTO Specification
The new API contracts are defined in `modules/hr/api.py`. Key components include:

-   **Service Protocols**: `FinanceService` and `TaxService` define the contracts for dependencies.
-   **Input DTOs**: `PayrollContextDTO` bundles all necessary data (state, config, services) for a payroll run. `EmployeeStateDTO` provides an immutable snapshot of employee data.
-   **Output DTOs**: `PayrollProcessingResult` contains a list of `HRAction` objects (`PayWageAction`, `RecordUnpaidWageAction`, etc.), which are declarative instructions for the calling agent (`Firm`).

## 4. Refactored Logic (Pseudo-code)

The core logic of `HRDepartment` will be transformed as follows.

### `HRDepartment.calculate_wage` (New Signature)
```python
# No longer needs a firm reference. Operates purely on inputs.
def calculate_wage(self, employee: EmployeeStateDTO, config: HRConfigDTO) -> float:
    # WO-023-B: Skill-based Wage Bonus
    actual_skill = employee.labor_skill

    # WO-Sociologist: Halo Effect (Credential Premium)
    education_level = employee.education_level
    halo_modifier = 1.0 + (education_level * config.halo_effect)

    return employee.base_wage * actual_skill * halo_modifier
```

### `HRDepartment.process_payroll` (New Signature & Logic)
```python
# Becomes a pure function returning a list of actions.
def process_payroll(self, context: PayrollContextDTO) -> PayrollProcessingResult:
    
    generated_actions: List[HRAction] = []
    
    # Use the service to get total solvency.
    total_liquid_assets = context.finance_service.get_total_liquid_assets_in_primary_currency()
    survival_cost = context.tax_service.get_survival_cost(context.market_data)

    for employee in context.employees:
        # Step 1: Calculate the gross wage
        wage = self.calculate_wage(employee, context.config)

        # Step 2: Determine affordability using the FinanceService
        can_afford_in_primary = context.finance_service.get_balance(context.config.default_currency) >= wage
        is_solvent_overall = total_liquid_assets >= wage
        
        # Step 3: Generate declarative actions based on affordability
        if can_afford_in_primary:
            # Case 1: Can pay fully.
            income_tax = context.tax_service.calculate_income_tax(wage, survival_cost)
            net_wage = wage - income_tax
            
            action = PayWageAction(
                employee_id=employee.id,
                gross_wage=wage,
                net_wage=net_wage,
                income_tax=income_tax,
                tax_recipient_id=context.tax_service.id, # Assuming service has an ID
                currency=context.config.default_currency
            )
            generated_actions.append(action)

        elif is_solvent_overall:
            # Case 2: Solvent but illiquid. Record unpaid "zombie" wage.
            action = RecordUnpaidWageAction(
                employee_id=employee.id,
                wage_amount=wage,
                tick=context.current_time,
                currency=context.config.default_currency
            )
            generated_actions.append(action)

        else:
            # Case 3: Insolvent. Attempt severance.
            severance_pay = wage * context.config.severance_pay_weeks
            can_afford_severance = context.finance_service.get_balance(context.config.default_currency) >= severance_pay

            if can_afford_severance:
                 action = ExecuteSeveranceAction(
                    employee_id=employee.id,
                    severance_pay=severance_pay,
                    currency=context.config.default_currency
                 )
                 generated_actions.append(action)
            else:
                # Fallback: Insolvent and cannot even pay severance.
                # Fire without pay and record unpaid wage as a claim.
                generated_actions.append(FireWithoutSeveranceAction(employee_id=employee.id))
                generated_actions.append(RecordUnpaidWageAction(
                    employee_id=employee.id,
                    wage_amount=wage,
                    tick=context.current_time,
                    currency=context.config.default_currency
                ))

    return PayrollProcessingResult(actions=generated_actions)
```

## 5. `Firm` Agent Adaptation
The `Firm` agent must be updated to use this new system. Its `generate_transactions` method will change:

```python
# In Firm.generate_transactions
# ...
# 1. Prepare the context DTO
payroll_context = PayrollContextDTO(
    current_time=current_time,
    employees=[emp.get_state_dto() for emp in self.hr.employees], # Assume employees have this method
    config=self.hr.config_dto, # HR dept now holds its own config subset
    market_context=market_context,
    market_data=market_data,
    finance_service=self.finance, # FinanceDepartment implements the protocol
    tax_service=government # Government implements the protocol
)

# 2. Call the pure function
payroll_result = self.hr.process_payroll(payroll_context)

# 3. Execute the returned actions (new logic)
for action in payroll_result.actions:
    if isinstance(action, PayWageAction):
        # create two transactions: one for employee, one for tax
        # self.finance.withdraw(...)
    elif isinstance(action, ExecuteSeveranceAction):
        # self.finance.pay_severance(...)
        # employee = self.get_employee(action.employee_id)
        # employee.quit()
    # ... and so on for other action types
```

## 6. Verification Plan & Mocking Guide

-   **Phase 1 (Unit Tests)**: Create `tests/modules/hr/test_hr_department.py`.
    -   Implement `MockFinanceService` and `MockTaxService`.
    -   Write tests for `process_payroll` covering all three affordability cases (can pay, illiquid, insolvent).
    -   Assert that the correct `HRAction` objects are returned in each case.
-   **Phase 2 (Integration Tests)**: Refactor `tests/simulation/test_firm_lifecycle.py`.
    -   Modify tests that check payroll outcomes.
    -   Instead of checking for specific `Transaction` objects, verify that the `Firm` correctly processes the `HRAction`s and produces the expected state changes (e.g., employee is fired, balance is reduced).
-   **Mocking `FinanceService` Example**:
    ```python
    @dataclass
    class MockFinanceService:
        balances: Dict[CurrencyCode, float]
        can_pay_severance: bool = True
        
        def get_total_liquid_assets_in_primary_currency(self) -> float:
            return sum(self.balances.values()) # Simplified for example
            
        def get_balance(self, currency: CurrencyCode) -> float:
            return self.balances.get(currency, 0.0)
            
        def pay_severance(self, ...) -> bool:
            return self.can_pay_severance
            
    # In test:
    mock_finance = MockFinanceService(balances={"USD": 100.0})
    context = PayrollContextDTO(..., finance_service=mock_finance)
    result = hr_department.process_payroll(context)
    # assert result.actions...
    ```

## 7. 🚨 Risk & Impact Audit
-   **Risk**: **Increased Complexity in `Firm` Agent**. The `Firm` now has the added responsibility of interpreting and executing `HRAction`s. This logic must be robust.
    -   **Mitigation**: This is a deliberate trade-off. We are moving complexity out of a black-box component and into the orchestrating agent, making the flow of logic explicit and easier to trace.
-   **Risk**: **Protocol Drift**. The `FinanceService` and `TaxService` protocols could become outdated if the underlying `FinanceDepartment` or `Government` changes.
    -   **Mitigation**: Rigorous type checking (Mypy) will catch protocol violations at compile time. Test failures will catch them at runtime.
-   **Impact**: This change will touch `Firm`, `HRDepartment`, `FinanceDepartment` (to implement the protocol), `Government` (to implement the protocol), and all related tests. The scope is significant.

## 8. 🚨 Mandatory Reporting Verification
-   All insights and identified technical debts during the creation of this specification have been captured. A corresponding report will be filed in `communications/insights/SPEC-HR-DECOUPLING.md` detailing the architectural decision-making process and highlighting the "stateful component" pattern as a major source of technical debt that this refactor begins to address.
```
