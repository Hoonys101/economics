# modules/finance/sagas/housing_api.py
```python
from typing import TypedDict, Literal, Optional, Protocol, List
from uuid import UUID
from dataclasses import dataclass

from modules.market.housing_planner_api import MortgageApplicationDTO

# --- DTOs for Saga State & Payloads ---

class MortgageApprovalDTO(TypedDict):
    """
    Represents the confirmed details of an approved mortgage.
    """
    loan_id: str  # Bank-issued unique loan identifier (string)
    lien_id: str  # Registry-issued unique lien identifier
    approved_principal: float
    monthly_payment: float

class HousingTransactionSagaStateDTO(TypedDict):
    """
    State object for the multi-tick housing purchase Saga.
    This object is persisted across ticks to manage the transaction lifecycle.
    """
    saga_id: UUID
    status: Literal[
        # Staging & Validation
        "INITIATED",            # -> Awaiting credit check
        "CREDIT_CHECK",         # -> Loan Approved or Rejected
        "APPROVED",             # -> Awaiting funds lock in escrow
        # Execution & Settlement
        "ESCROW_LOCKED",        # -> Awaiting final title transfer
        "TRANSFER_TITLE",       # -> Completed or Failed
        # Terminal States
        "COMPLETED",
        "FAILED_ROLLED_BACK"
    ]
    buyer_id: int
    seller_id: int
    property_id: int
    offer_price: float
    down_payment_amount: float
    
    # State-specific payloads, populated as the saga progresses
    loan_application: Optional[MortgageApplicationDTO]
    mortgage_approval: Optional[MortgageApprovalDTO]

    # Tracking IDs for compensation
    staged_loan_id: Optional[str]

    # Error logging
    error_message: Optional[str]
    last_processed_tick: int

# --- System Interfaces ---

class IProperty(Protocol):
    id: int
    owner_id: int
    is_under_contract: bool
    liens: List[str]

class IPropertyRegistry(Protocol):
    """
    Interface for a system managing property ownership and status.
    """
    def set_under_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Locks a property, preventing other sales. Returns False if already locked."""
        ...

    def release_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Releases the lock on a property."""
        ...

    def add_lien(self, property_id: int, loan_id: str) -> Optional[str]:
        """Adds a lien to a property, returns a unique lien_id."""
        ...
    
    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        """Removes a lien from a property."""
        ...
        
    def transfer_ownership(self, property_id: int, new_owner_id: int) -> bool:
        """Finalizes the transfer of the property."""
        ...

class ILoanMarket(Protocol):
    """
    Interface for the loan market.
    """
    def stage_mortgage_application(self, application: MortgageApplicationDTO) -> Optional[str]:
        """
        Submits an application for asynchronous credit check.
        Returns a unique `staged_loan_id` for tracking, or None if invalid.
        """
        ...
    
    def check_staged_application_status(self, staged_loan_id: str) -> Literal["PENDING", "APPROVED", "REJECTED"]:
        """Checks the status of a pending mortgage application."""
        ...

    def convert_staged_to_loan(self, staged_loan_id: str) -> Optional[MortgageApprovalDTO]:
        """
        Finalizes an approved application, creating an official loan and lien.
        Returns the final loan details or None on failure.
        """
        ...
        
    def void_staged_application(self, staged_loan_id: str) -> bool:
        """Cancels a pending or approved application before funds are disbursed."""
        ...

class IHousingTransactionSagaHandler(Protocol):
    """
    The refactored Saga Handler, now a state machine processor.
    """
    def execute_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        """Processes a single step of the saga based on its current status."""
        ...

    def compensate_step(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        """Triggers the rollback/compensation logic for the saga's current status."""
        ...

class ISagaManager(Protocol):
    """
    A new system responsible for managing all active sagas.
    """
    def process_sagas(self) -> None:
        """Iterates through all active sagas and executes the next step."""
        ...
    
    def register_saga(self, saga_state: HousingTransactionSagaStateDTO) -> None:
        """Adds a new saga to the manager."""
        ...
        
    def find_and_compensate_by_agent(self, agent_id: int) -> None:
        """Finds all sagas involving a specific agent and triggers their compensation."""
        ...
```
# design/3_work_artifacts/specs/housing_saga_refactor_spec.md
```markdown
# Spec: Multi-Tick Housing Transaction Saga

**Version:** 1.0
**Author:** Gemini (Scribe)
**Related Documents:** `modules/finance/sagas/housing_api.py`

## 1. Overview

This document outlines the refactoring of the `HousingTransactionSagaHandler` from a single, atomic operation into a distributed, multi-tick state machine. This change is necessary to support more complex, realistic housing transactions that cannot be resolved within a single tick, while ensuring the system remains robust against failures and unforeseen events like agent death.

The new design introduces a `SagaManager` to oversee the lifecycle of all active housing transactions, persisting their state across ticks and integrating with core simulation phases like `Phase_Bankruptcy`.

## 2. Architectural Changes

### 2.1. Saga Manager (`SagaManager`)

A new central service, `SagaManager`, will be introduced.
- **Responsibility**: Manages the persistence, retrieval, and execution of all `HousingTransactionSagaStateDTO` objects.
- **Integration**: A new `Phase_SagaProcessing` will be added to the `TickOrchestrator` after `Phase1_Decision`. During this phase, the `SagaManager.process_sagas()` method will be called to advance all active sagas.
- **Agent Lifecycle Integration**: The `Phase_Bankruptcy` will be modified. Before an agent is removed, it will call `SagaManager.find_and_compensate_by_agent(agent_id)` to gracefully roll back any transactions the agent was involved in.

### 2.2. State DTO (`HousingTransactionSagaStateDTO`)

The saga's state object is updated to reflect the new multi-tick process.
- **New Statuses**: `INITIATED`, `CREDIT_CHECK`, `APPROVED`, `ESCROW_LOCKED`, `TRANSFER_TITLE`.
- **New Fields**: 
    - `staged_loan_id: str`: Tracks the loan application before it's formally approved.
    - `last_processed_tick: int`: Prevents processing the same state multiple times in one tick.

## 3. Detailed Saga State Machine

The saga progresses through five main stages. Each `execute` step has a corresponding `compensate` step to ensure atomicity and rollback capability.

---

### **Stage 1: INITIATED**

- **Description**: The saga is created and submitted to the `SagaManager`. The first action is to lock the target property to prevent concurrent sales.
- **Execute**:
    1. Call `PropertyRegistry.set_under_contract(property_id, saga_id)`.
    2. If successful, prepare a `MortgageApplicationDTO`.
    3. Call `LoanMarket.stage_mortgage_application(application)`.
    4. Store the returned `staged_loan_id` in the saga state.
    5. Transition to `CREDIT_CHECK`.
- **Failure/Compensation**:
    - If `set_under_contract` fails (property already locked), transition to `FAILED_ROLLED_BACK`.
    - If `stage_mortgage_application` fails, call `PropertyRegistry.release_contract(property_id)` and transition to `FAILED_ROLLED_BACK`.

---

### **Stage 2: CREDIT_CHECK**

- **Description**: The saga waits for the bank/loan market to asynchronously perform a credit check on the buyer.
- **Execute**:
    1. Call `LoanMarket.check_staged_application_status(staged_loan_id)`.
    2. If `APPROVED`, transition to `APPROVED`.
    3. If `REJECTED`, trigger compensation.
    4. If `PENDING`, remain in `CREDIT_CHECK` and wait for the next tick.
- **Failure/Compensation**:
    - If status is `REJECTED`:
        1. Call `LoanMarket.void_staged_application(staged_loan_id)`.
        2. Call `PropertyRegistry.release_contract(property_id)`.
        3. Transition to `FAILED_ROLLED_BACK`.

---

### **Stage 3: APPROVED**

- **Description**: The loan has been approved. The system now converts the staged application into a formal loan, creates a lien on the property, and prepares for fund transfer.
- **Execute**:
    1. Call `LoanMarket.convert_staged_to_loan(staged_loan_id)`. This action should be idempotent or return the existing loan if already converted.
    2. The `convert_staged_to_loan` method is responsible for calling `PropertyRegistry.add_lien()` and returning the `MortgageApprovalDTO` containing both `loan_id` and `lien_id`.
    3. Store the `MortgageApprovalDTO` in the saga state.
    4. Transition to `ESCROW_LOCKED`.
- **Failure/Compensation**:
    - If `convert_staged_to_loan` fails:
        1. Call `LoanMarket.void_staged_application(staged_loan_id)`.
        2. Call `PropertyRegistry.release_contract(property_id)`.
        3. Transition to `FAILED_ROLLED_BACK`.

---

### **Stage 4: ESCROW_LOCKED**

- **Description**: All preconditions are met. The system now performs the multi-party settlement to move funds.
- **Execute**:
    1. Construct a list of financial transfers:
        - `(Buyer, EscrowAgent, down_payment_amount)`
        - `(Bank, EscrowAgent, approved_principal)`
    2. Execute transfers via `SettlementSystem`.
    3. If fund transfers are successful, transition to `TRANSFER_TITLE`.
- **Failure/Compensation**:
    - If any fund transfer fails (e.g., insufficient funds for down payment):
        1. The `SettlementSystem` is assumed to handle the atomic rollback of this specific multiparty transfer.
        2. Call `PropertyRegistry.remove_lien(lien_id)`.
        3. Call `LoanMarket.void_staged_application(staged_loan_id)` (or a new `terminate_loan(loan_id)` if funds were already committed).
        4. Call `PropertyRegistry.release_contract(property_id)`.
        5. Transition to `FAILED_ROLLED_BACK`.

---

### **Stage 5: TRANSFER_TITLE**

- **Description**: Funds are secure. The final step is to transfer the property title and release funds from escrow to the seller.
- **Execute**:
    1. Call `PropertyRegistry.transfer_ownership(property_id, buyer_id)`.
    2. Execute final settlement transfer: `(EscrowAgent, Seller, offer_price)`.
    3. Log the final `Transaction` record.
    4. Transition to `COMPLETED`.
- **Failure/Compensation**:
    - This is the "point of no return". A failure here is critical and may require manual intervention.
    - If `transfer_ownership` fails, the system is in an inconsistent state. The funds are in escrow but the title cannot be transferred.
    - **Mitigation**: The system should attempt to reverse the escrow settlement: `(EscrowAgent, Buyer, down_payment)` and `(EscrowAgent, Bank, principal)`. Then, perform all previous compensation steps. This path must be heavily logged.

## 4. Addressing Architectural Risks

This design explicitly mitigates the risks identified in the pre-flight audit:

1.  **God Class Dependency**: The `SagaManager` and `Phase_SagaProcessing` create a formal, bounded context for saga execution, reducing reliance on direct `world_state` manipulation within the handler itself. The handler now operates on a well-defined `HousingTransactionSagaStateDTO`.
2.  **Loss of Financial Atomicity**: By breaking the process into `execute` and `compensate` pairs for each stage, we create "mini-transactions". The system is designed to be able to roll back from any intermediate step, ensuring financial consistency.
3.  **Brittle Compensation Logic**: The fragile `_void_loan` logic is replaced by a formal set of interface methods (`void_staged_application`, `release_contract`, `remove_lien`). This enforces strict contracts between systems for rollback actions.
4.  **Agent Lifecycle Integration**: The `Phase_Bankruptcy` now has a clear hook (`SagaManager.find_and_compensate_by_agent`) to ensure that sagas involving a dying agent are correctly and automatically terminated, releasing locked assets.

## 5. Verification Plan

Given the lack of existing test coverage, a comprehensive test suite is mandatory.

-   **Unit Tests**:
    -   For each of the 5 stages, test the `execute` and `compensate` logic in isolation, mocking the `ILoanMarket` and `IPropertyRegistry` interfaces.
-   **Integration Tests**:
    -   **Success Path**: A multi-tick test that runs a saga from `INITIATED` to `COMPLETED`.
    -   **Failure Paths**: Create separate tests that simulate a failure at each of the 5 stages and verify that the correct compensation logic is triggered and the system returns to a consistent state.
    -   **Agent Death Test**: An integration test where the buyer or seller agent is removed mid-saga (e.g., during `CREDIT_CHECK`), verifying that `Phase_Bankruptcy` triggers the full rollback.
    -   **Concurrency Test**: A test where two buyers attempt to purchase the same property, verifying that `set_under_contract` correctly allows one to proceed and fails the other.
```
