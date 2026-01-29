# Implementation Spec: CorporateManager Departmentalization (TD-142)

## 1. Overview

This document outlines the implementation plan for refactoring the monolithic `CorporateManager` into a set of specialized, department-specific managers. This refactoring addresses the "God Class" anti-pattern (TD-142) and improves modularity, testability, and adherence to the Single Responsibility Principle (SRP).

The refactoring will be guided by the `GOD_FILE_DECOMPOSITION_SPEC.md` and the critical constraints identified in the pre-flight audit.

**The core architectural change is to transform `CorporateManager` from a doer into an orchestrator.** It will be responsible for gathering data, delegating decisions to specialized departmental managers, and applying the resulting plans.

## 2. Architectural Principles & Constraints

This implementation **MUST** adhere to the following principles:

1.  **Unidirectional Data Flow**: Departmental managers **MUST NOT** communicate with each other directly. The `CorporateManager` orchestrator is the single source of truth for data flow, preventing circular dependencies.
2.  **DTO-Purity Gate (WO-114)**: All data passed to and from departmental managers **MUST** be encapsulated in DTOs. No direct access to simulation state or objects is permitted.
3.  **Preservation of R&D Logic (WO-136)**: The endogenous R&D investment logic, originating from `FirmSystem2Planner` guidance, **MUST** be preserved and correctly implemented within the new `OperationsManager`.
4.  **Test Suite Obsolescence**: The existing test suite `tests/unit/test_corporate_manager.py` is considered **obsolete** and will be deprecated. It serves as a behavioral reference only. New, focused unit tests for each departmental manager are a mandatory part of this work.

## 3. High-Level Architecture & Data Flow

The `CorporateManager.realize_ceo_actions` method will be refactored to orchestrate the decision-making process as follows:

1.  **Gather State**: The orchestrator collects all necessary information (`FirmStateDTO`, market data, planner guidance) and packages it into a `DecisionContextDTO`.
2.  **Delegate to Departments (in sequence)**:
    a. **Finance**: `FinanceManager` receives the `DecisionContextDTO` and produces a `FinancialPlanDTO` outlining budgets and financial constraints.
    b. **HR**: `HRManager` receives the context and the `FinancialPlanDTO` to produce an `HRPlanDTO` with hiring, firing, and wage decisions.
    c. **Operations**: `OperationsManager` receives the context, financial plan, and HR plan to produce an `OperationsPlanDTO` detailing production targets and R&D investment.
    d. **Sales**: `SalesManager` receives the context and all preceding plans to produce a `SalesPlanDTO` with pricing and marketing decisions.
3.  **Apply Decisions**: The orchestrator collects all `*PlanDTO` objects and translates them into concrete state changes for the simulation.

![Data Flow Diagram](https://mermaid.ink/svg/eyJjb2RlIjoiXG5ncmFwaCBURDtcbiAgICBTdWJzYW1wbGVyW0NvcnBvcmF0ZU1hbmFnZXIgT3JjaGVzdHJhdG9yXSAgLS0-IHwgMS4gR2F0aGVyIFN0YXRlIHwgRGVjaXNpb25Db250ZXh0RFRPO1xuICAgIERlY2lzaW9uQ29udGV4dERUTyAtLT58Mi5hLiBQbGFuIEZpbmFuY2VzfCBGaW5hbmNlTWFuYWdlcjtcbiAgICBGaW5hbmNlTWFuYWdlciAtLT4gRmluYW5jaWFsUGxhbkRUTztcblxuICAgIERlY2lzaW9uQ29udGV4dERUTyAtLT58Mi5iLiBQbGFuIEhSfCBIUk1hbmFnZXI7XG4gICAgRmluYW5jaWFsUGxhbkRUTyAtLT4gSFJNYW5hZ2VyO1xuICAgIEhSTWFuYWdlciAtLT4gSFJQbGFuRFRPO1xuXG4gICAgRGVjaXNpb25Db250ZXh0RFRPLGZpbmFuY2lhbFBsYW5EVG8sSFJQbGFuRFRPLG9wZXJhdGlvbnNQbGFuRFRPLFNhbGVzUGxhbkRUT1tEZWNpc2lvbiBQbGFuc10gLS0-fDMuIEFwcGx5IERlY2lzaW9uc3wgU3Vic2FtcGxlcjtcblxuICAgIERlY2lzaW9uQ29udGV4dERUTyAtLT58Mi5jLiBQbGFuIE9wZXJhdGlvbnN8IE9wZXJhdGlvbnNNYW5hZ2VyO1xuICAgIEZpbmFuY2lhbFBsYW5EVE8gLS0-IE9wZXJhdGlvbnNNYW5hZ2VyO1xuICAgIEhSUGxhbkRUTyAtLT4gT3BlcmF0aW9uc01hbmFnZXI7XG4gICAgT3BlcmFtionsTWFuYWdlciAtLT4gT3BlcmF0aW9uc1BsYW5EVE87XG5cbiAgICBEZWNpc2lvbkNvbnRleHREVE8gLS0-fDIuZC4gUGxhbiBTYWxlc3wgU2FsZXNNYW5hZ2VyO1xuICAgIEZpbmFuY2lhbFBsYW5EVE8gLS0-IFNhbGVzTWFuYWdlcjtcbiAgICBIUlBsYW5EVE8gLS0-IFNhbGVzTWFuYWdlcjtcbiAgICBPcGVyYXRpb25zUGxhbkRUTyAtLT4gU2FsZXNNYW5hZ2VyO1xuICAgIFNhbGVzTWFuYWdlciAtLT4gU2FsZXNQbGFuRFRPO1xuXG4gICAgc3R5bGUgRGVjaXNpb25Db250ZXh0RFRPLCBGaW5hbmNpYWxQbGFuRFRPLCBfSG5kcFBtYW5EVE8sIE9wZXJhdGlvbnNQbGFuRFRPLCBTYWxlc1BsYW5EVE8gZmlsbDojZDNmZmQzLHN0cm9rZTojMzMzLHN0cm9rZS13aWR0aDoycHg7XG4gICAgc3R5bGUgRGVjaXNpb25QbGFucyBmaWxsOiNkM2ZmZDMsc3Ryb2tlOiMzMzMsc3Ryb2tlLXdpZHRoOjJweDtcbiAgICBzdHlsZSBTVUIgZmlsbDojZjVmNWY1LGZpbGwtb3BhY2l0eTogMC4xO1xuICAgIHN1YmdyYXBoIFNVQlxuICAgICAgICBEZWNpc2lvbkNvbnRleHREVE8sIEZpbmFuY2lhbFBsYW5EVE8sIEhSUGxhbkRUTywgT3BlcmF0aW9uc1BsYW5EVE8sIFNhbGVzUGxhbkRUTyxcbiAgICAgICAgRGVjaXNpb25QbGFuc1xuICAgIGVuZFxuXG4iLCJtZXJtYWlkIjp7InRoZW1lIjoiZGVmYXVsdCJ9fQ)

## 4. Detailed Design & Interfaces

See `modules/corporate/api.py` for the definitive interfaces.

### 4.1. FinanceManager

-   **Responsibility**: Manages the firm's budget, financing, and financial planning.
-   **Key Logic**:
    -   Calculates available cash and credit.
    -   Determines budget allocations for wages, production, R&D, and marketing based on strategic guidance.
    -   Handles debt and interest payments.
-   **Pseudo-code (`plan_finances`)**:
    ```python
    # 1. Assess current financial state from context.firm_state
    available_cash = context.firm_state.cash
    # 2. Project revenue and costs based on previous cycle
    # 3. Use context.guidance to determine financial strategy (e.g., austerity, growth)
    # 4. Allocate budgets for each department
    wage_budget = ...
    production_budget = ...
    # 5. Return FinancialPlanDTO with budgets and constraints
    return FinancialPlanDTO(wage_budget=wage_budget, ...)
    ```

### 4.2. HRManager

-   **Responsibility**: Manages hiring, firing, and wages.
-   **Key Logic**:
    -   Determines required workforce based on production targets and planner guidance.
    -   Adjusts workforce based on the `FinancialPlanDTO`'s wage budget.
    -   Sets wages based on market conditions and firm strategy.
-   **Pseudo-code (`plan_workforce`)**:
    ```python
    # 1. Determine ideal number of employees from context.guidance.
    # 2. Check financial_plan.wage_budget to see if ideal is affordable.
    # 3. Calculate number of employees to hire or fire.
    # 4. Set target wage based on context.market_state.average_wage.
    # 5. Return HRPlanDTO with hiring/firing delta and target wage.
    return HRPlanDTO(employees_to_hire=10, target_wage=55000)
    ```

### 4.3. OperationsManager

-   **Responsibility**: Manages production levels and R&D investment. **This is the new home for the WO-136 R&D logic.**
-   **Key Logic**:
    -   Determines production quantity based on inventory, sales forecasts, and planner guidance.
    -   **Crucially**, calculates R&D investment based on `context.guidance.rd_investment_focus` and `financial_plan.rd_budget`.
-   **Pseudo-code (`plan_production_and_rd`)**:
    ```python
    # 1. Determine production target based on inventory and sales forecasts.
    production_target = ...
    
    # 2. [WO-136 LOGIC PRESERVATION]
    #    Retrieve R&D strategy from the planner's guidance.
    rd_focus = context.guidance.rd_investment_focus
    
    # 3. Allocate the R&D budget from the financial plan according to the strategy.
    rd_budget = financial_plan.rd_budget
    investment = calculate_rd_investment(rd_budget, rd_focus) # Re-implement CorporateManager._manage_r_and_d
    
    # 4. Return OperationsPlanDTO.
    return OperationsPlanDTO(production_quantity=production_target, r_and_d_investment=investment)
    ```

### 4.4. SalesManager

-   **Responsibility**: Manages pricing, marketing, and sales forecasting.
-   **Key Logic**:
    -   Sets product price based on inventory levels, production costs, and market competition.
    -   Allocates marketing budget to influence demand.
-   **Pseudo-code (`plan_sales`)**:
    ```python
    # 1. Analyze market competition from context.market_state.
    # 2. Get production cost from operations_plan.
    # 3. Set price to maximize profit or market share based on context.guidance.
    price = ...
    
    # 4. Allocate marketing budget from financial_plan.
    marketing_spend = financial_plan.marketing_budget
    
    # 5. Return SalesPlanDTO.
    return SalesPlanDTO(price=price, marketing_investment=marketing_spend)
    ```

## 5. Verification & Test Plan

1.  **Deprecate Old Tests**: The file `tests/unit/test_corporate_manager.py` is to be considered obsolete and will be removed or archived after the new tests are stable.
2.  **Create New Unit Tests**: New, focused test files **MUST** be created for each manager:
    -   `tests/unit/corporate/test_finance_manager.py`
    -   `tests/unit/corporate/test_hr_manager.py`
    -   `tests/unit/corporate/test_operations_manager.py`
    -   `tests/unit/corporate/test_sales_manager.py`
3.  **Test Strategy**:
    -   Each test will construct the necessary input DTOs (`DecisionContextDTO`, `FinancialPlanDTO`, etc.) by hand or using fixtures.
    -   It will call the manager's `plan_*` method.
    -   It will assert that the returned `*PlanDTO` contains the expected values for a given scenario.
4.  **Golden Data Fixtures**:
    -   Utilize existing fixtures like `golden_households` and `golden_firms` from `tests/conftest.py` to create realistic DTOs for testing.
    -   **DO NOT** use `MagicMock` to mock DTOs, as this subverts type safety. Use real dataclass instances.
5.  **Integration Test**: A single integration test within a new `tests/integration/test_corporate_orchestrator.py` should verify that the refactored `CorporateManager` can successfully execute a full decision cycle using mock versions of the new departmental managers.

## 6. Risk & Impact Audit (Resolution)

-   **Circular Dependency Risk**: **Mitigated.** The unidirectional orchestrator pattern is explicitly designed to prevent this. The `api.py` will enforce this separation.
-   **Test Suite Obsolescence**: **Accepted.** The Verification Plan mandates the creation of a new, more robust and maintainable test suite. The old suite is acknowledged as a sunk cost.
-   **R&D Logic Preservation**: **Addressed.** The `OperationsManager` is designated as the new owner of the R&D logic, and its interface is designed to receive the necessary `guidance` and budget DTOs. This is a critical item for code review.
-   **DTO Adherence**: **Enforced.** The `api.py` and the proposed architecture are strictly based on DTOs, satisfying the DTO Purity Gate requirement.

## 7. Mandatory Reporting

As part of this implementation, the developer (Jules) **MUST** record any discovered insights, unforseen complexities, or new technical debt in a dedicated report file: `communications/insights/TD-142_Corporate_Departmentalization.md`. This ensures that knowledge is captured without causing merge conflicts in shared documentation.

---
```python
#
# modules/corporate/api.py
#

from __future__ import annotations
from typing import Protocol, TypedDict
from dataclasses import dataclass

# =================================================================
# 1. Core Data Transfer Objects (DTOs)
# =================================================================

# --- Input DTOs ---

@dataclass(frozen=True)
class FirmStateDTO:
    """A snapshot of the firm's current state."""
    cash: float
    inventory: int
    employees: int
    # ... other relevant fields from the firm object
    
@dataclass(frozen=True)
class MarketStateDTO:
    """A snapshot of the current market conditions."""
    average_wage: float
    # ... other relevant market fields

@dataclass(frozen=True)
class PlannerGuidanceDTO:
    """Strategic guidance from the FirmSystem2Planner."""
    rd_investment_focus: str  # e.g., 'cost_reduction', 'quality_improvement'
    # ... other strategic goals

@dataclass(frozen=True)
class DecisionContextDTO:
    """A comprehensive context object passed to all managers."""
    firm_state: FirmStateDTO
    market_state: MarketStateDTO
    guidance: PlannerGuidanceDTO

# --- Departmental Plan DTOs (Output of each manager) ---

@dataclass(frozen=True)
class FinancialPlanDTO:
    """Output from FinanceManager."""
    wage_budget: float
    production_budget: float
    rd_budget: float
    marketing_budget: float

@dataclass(frozen=True)
class HRPlanDTO:
    """Output from HRManager."""
    employees_to_hire: int
    employees_to_fire: int
    target_wage: float

@dataclass(frozen=True)
class OperationsPlanDTO:
    """Output from OperationsManager."""
    production_quantity: int
    r_and_d_investment: float

@dataclass(frozen=True)
class SalesPlanDTO:
    """Output from SalesManager."""
    price: float
    marketing_investment: float

# =================================================================
# 2. Departmental Manager Interfaces
# =================================================================

class FinanceManagerInterface(Protocol):
    """Interface for managing the firm's finances."""
    def plan_finances(self, context: DecisionContextDTO) -> FinancialPlanDTO:
        """
        Creates a financial plan based on the current context.
        """
        ...

class HRManagerInterface(Protocol):
    """Interface for managing the firm's workforce."""
    def plan_workforce(
        self, context: DecisionContextDTO, financial_plan: FinancialPlanDTO
    ) -> HRPlanDTO:
        """
        Creates a workforce plan based on context and financial constraints.
        """
        ...

class OperationsManagerInterface(Protocol):
    """Interface for managing production and R&D."""
    def plan_production_and_rd(
        self,
        context: DecisionContextDTO,
        financial_plan: FinancialPlanDTO,
        hr_plan: HRPlanDTO,
    ) -> OperationsPlanDTO:
        """
        Creates a plan for production and R&D, preserving WO-136 logic.
        """
        ...

class SalesManagerInterface(Protocol):
    """Interface for managing sales, pricing, and marketing."""
    def plan_sales(
        self,
        context: DecisionContextDTO,
        financial_plan: FinancialPlanDTO,
        hr_plan: HRPlanDTO,
        operations_plan: OperationsPlanDTO,
    ) -> SalesPlanDTO:
        """
        Creates a sales and marketing plan.
        """
        ...

# =================================================================
# 3. Orchestrator Interface
# =================================================================

class CorporateOrchestratorInterface(Protocol):
    """
    The refactored CorporateManager, which orchestrates departmental decisions.
    """
    def __init__(
        self,
        finance_manager: FinanceManagerInterface,
        hr_manager: HRManagerInterface,
        operations_manager: OperationsManagerInterface,
        sales_manager: SalesManagerInterface,
    ):
        ...

    def realize_ceo_actions(self, firm_id: int) -> None:
        """
        Orchestrates the full decision-making cycle for a firm.
        1. Gathers state into DecisionContextDTO.
        2. Calls departmental managers in sequence.
        3. Applies the resulting plans to the simulation state.
        """
        ...
```
