# Technical Spec: Bank Class Decomposition (TD-274)

## 1. Overview & Goal

This document outlines the technical specification for refactoring the monolithic `Bank` class to resolve **TD-274**. The current `Bank` class violates the Single Responsibility Principle (SRP) by managing deposits, loans, and central banking functions.

The goal is to decompose the `Bank` class into two distinct, single-responsibility services:
1.  `LoanManager`: Manages all aspects of the loan lifecycle.
2.  `DepositManager`: Manages all agent deposit accounts and interest calculations.

The existing `Bank` class will be repurposed as a facade, delegating calls to the appropriate manager and serving as the single point of contact for external systems like the `SettlementSystem`. This refactoring directly addresses the risks of abstraction leaks (**TD-276**, **TD-275**) and protocol bypasses (**TD-273**) identified in the pre-flight audit.

## 2. Architectural Principles

-   **Single Responsibility Principle (SRP)**: Each new manager will have one well-defined responsibility.
-   **No Raw Agent Access**: All interactions with agents (e.g., `Household`, `Firm`) **MUST** be through their unique integer IDs. Direct manipulation of agent objects or lists of agent objects is strictly forbidden, adhering to the remediation plan for **TD-276**.
-   **Protocol Compliance**: All financial transactions **MUST** use the established `SettlementSystem` and wallet interfaces (`deposit`/`withdraw`). Direct manipulation of agent assets is forbidden, addressing **TD-273** and **TD-260**.
-   **DTO Purity**: Data transfer between components and services will exclusively use strongly-typed Data Transfer Objects (DTOs).

## 3. Proposed Architecture

The `Bank` class will transition from a "God Class" to a **Facade**. It will instantiate and hold references to `LoanManager` and `DepositManager`. External callers will interact with the `Bank` facade, which will route requests to the appropriate underlying service.

```
+----------------+      +------------------+      +-----------------+
|   Other        |----->|   Bank (Facade)  |----->|  LoanManager    |
|   Systems      |      +------------------+      +-----------------+
| (e.g., Firm,   |               |
|  Household)    |               |
+----------------+               |            +------------------+
                                 +----------->|  DepositManager  |
                                              +------------------+
```

## 4. Interface Definitions (`api.py`)

The public contract for the new financial services will be defined in `modules/finance/api.py`.

### 4.1. Data Transfer Objects (DTOs)

```python
# modules/finance/dtos.py (or a similar central DTO file)
from typing import TypedDict, Literal

# --- Loan DTOs ---
LoanStatus = Literal["PENDING", "ACTIVE", "PAID", "DEFAULTED"]

class LoanApplicationDTO(TypedDict):
    applicant_id: int
    amount: float
    purpose: str
    term_months: int # Duration of the loan

class LoanDTO(TypedDict):
    loan_id: str
    borrower_id: int
    principal: float
    interest_rate: float
    term_months: int
    remaining_principal: float
    status: LoanStatus

# --- Deposit DTOs ---
class DepositDTO(TypedDict):
    owner_id: int
    balance: float
    interest_rate: float
```

### 4.2. Service Interfaces

```python
# modules/finance/api.py
from typing import Protocol, List
from .dtos import LoanApplicationDTO, LoanDTO, DepositDTO

class ILoanManager(Protocol):
    """Interface for managing the entire lifecycle of loans."""

    def submit_loan_application(self, application: LoanApplicationDTO) -> str:
        """Submits a new loan application, returns a unique application ID."""
        ...

    def process_applications(self) -> None:
        """Reviews pending applications and approves/rejects them."""
        ...

    def service_loans(self) -> None:
        """
        Processes monthly payments for all active loans.
        Generates settlement tasks for payments due.
        """
        ...

    def get_loan_by_id(self, loan_id: str) -> LoanDTO | None:
        ...

    def get_loans_for_agent(self, agent_id: int) -> List[LoanDTO]:
        ...

class IDepositManager(Protocol):
    """Interface for managing agent deposit accounts."""

    def get_balance(self, agent_id: int) -> float:
        """Returns the deposit balance for a given agent."""
        ...

    def get_deposit_dto(self, agent_id: int) -> DepositDTO | None:
        ...

    def calculate_and_distribute_interest(self) -> None:
        """
        Calculates interest for all accounts and generates settlement tasks
        for crediting the interest.
        """
        ...
```

## 5. Component Responsibilities (Pseudo-code)

### 5.1. `LoanManager`

-   **State**: `Dict[str, LoanDTO]`, `List[LoanApplicationDTO]`
-   **Logic**:
    -   `submit_loan_application(app)`:
        -   Validate application DTO.
        -   Generate a unique ID.
        -   Store in a pending applications list.
    -   `process_applications()`:
        -   For each pending application:
            -   `applicant_dto = agent_registry.get_dto(app.applicant_id)` (DO NOT get the object)
            -   Assess creditworthiness based on DTO data (e.g., income, existing debt).
            -   If approved:
                -   Create a new `LoanDTO`.
                -   Create a settlement task to transfer principal to the borrower.
                -   `settlement_system.submit_task(...)`
            -   Remove from pending list.
    -   `service_loans()`:
        -   For each `loan` where `status == "ACTIVE"`:
            -   Calculate monthly payment (principal + interest).
            -   Create a settlement task to debit the borrower's account.
            -   `settlement_system.submit_task(...)`
            -   If payment fails (notified by `SettlementSystem` via a callback or status check):
                -   Handle delinquency (e.g., mark as late, eventually default).

### 5.2. `DepositManager`

-   **State**: `Dict[int, DepositDTO]` (mapping agent_id to their deposit)
-   **Logic**:
    -   `get_balance(agent_id)`: Return `deposits.get(agent_id, {}).get('balance', 0)`.
    -   `calculate_and_distribute_interest()`:
        -   For each `agent_id`, `deposit` in `deposits.items()`:
            -   `interest_amount = deposit.balance * deposit.interest_rate`
            -   If `interest_amount > 0`:
                -   Create settlement task to credit `interest_amount` to the agent.
                -   `settlement_system.submit_task(...)`

### 5.3. `Bank` (Facade)

-   **State**: `ILoanManager`, `IDepositManager`
-   **Logic**: Mostly delegates.
    -   `def __init__(self, agent_registry, settlement_system):`
        -   `self.loan_manager = LoanManager(agent_registry, settlement_system)`
        -   `self.deposit_manager = DepositManager(settlement_system)`
    -   `def submit_loan_application(self, app)`:
        -   `return self.loan_manager.submit_loan_application(app)`
    -   `def get_balance(self, agent_id)`:
        -   `return self.deposit_manager.get_balance(agent_id)`
    -   `def tick_update(self)`:
        -   `self.loan_manager.process_applications()`
        -   `self.loan_manager.service_loans()`
        -   `self.deposit_manager.calculate_and_distribute_interest()`

## 6. Verification Plan & Mocking Strategy

1.  **Unit Tests**: New test suites will be created for `LoanManager` and `DepositManager` in isolation.
    -   Dependencies like the `AgentRegistry` and `SettlementSystem` will be replaced with mock implementations that conform to their respective `Protocol` interfaces.
    -   `MagicMock` should be avoided in favor of creating concrete test doubles.
2.  **Integration Tests**: Existing tests that use the `Bank` class will be refactored.
    -   Instead of mocking the entire `Bank`, tests should provide mock implementations of the new `ILoanManager` and `IDepositManager` interfaces to the `Bank` facade. This allows for more targeted testing.
3.  **Golden Data**:
    -   The `golden_households` and `golden_firms` fixtures will be used to generate realistic `LoanApplicationDTO`s.
    -   Tests will verify that the `LoanManager` correctly requests agent DTOs from a mock `AgentRegistry` using the IDs from the golden fixtures.

## 7. Risk & Impact Audit

-   **Risk of Abstraction Leaks (TD-276, TD-275)**: **Mitigated.** This design explicitly forbids the new managers from accessing agent objects directly. All interactions are through IDs and DTOs, enforced by the `ILoanManager` and `IDepositManager` protocols.
-   **Risk of Circular Dependencies (TD-270)**: **Mitigated.** The managers are self-contained and do not have dependencies on other business logic components like `FinanceDepartment`. They communicate outwards only to core services (`AgentRegistry`, `SettlementSystem`).
-   **Risk of Protocol Bypass (TD-273, TD-260)**: **Mitigated.** All transfers of funds (loan disbursement, repayments, interest) are handled exclusively by creating tasks for the `SettlementSystem`. The managers have no code to directly alter agent wallets.
-   **Test Suite Fragility**: **Acknowledged.** A significant portion of the test suite will break. Refactoring will proceed incrementally:
    1.  Implement `LoanManager` and `DepositManager` with new unit tests.
    2.  Adapt the `Bank` class to its new Facade role.
    3.  Incrementally update failing integration tests to use the new mock strategies for `ILoanManager` and `IDepositManager`.

## 8. Mandatory Reporting Verification

During the creation of this specification, architectural insights regarding dependency injection and the contract with the `SettlementSystem` have been identified. These insights will be recorded in `communications/insights/TD-274_Bank_Decomposition.md` as required.
