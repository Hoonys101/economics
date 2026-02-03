# Spec: Detailed Implementation of the Housing Purchase Saga

- **Mission**: To provide a detailed, implementable blueprint for integrating a multi-tick, atomic housing purchase process (Saga) into the existing `SettlementSystem`.
- **Audience**: Jules (Developer Agent). This document is your direct instruction set.
- **Architectural Mandate**: This implementation must strictly adhere to the project's core architectural principles, especially the primacy of the `SettlementSystem` for all transactional integrity. All risks identified in the pre-flight audit must be addressed.

---

## 1. Core Principles & Constraints (MANDATORY)

1.  **`SettlementSystem` is the Sole Coordinator**: The Saga state machine **MUST** be implemented *within* the `SettlementSystem`. No other component shall manage or be aware of the saga's internal state. This is non-negotiable and upholds `platform_architecture.md: 2.3`.
2.  **Strict Separation of Responsibilities (SRP)**:
    -   **`HousingPlanner`**: ONLY evaluates and decides. It remains stateless and is unaware of the saga.
    -   **`DecisionUnit`**: ONLY initiates the saga via a "fire-and-forget" call to `SettlementSystem.submit_saga()`. It does not track progress.
    -   **`LoanMarket`**: ONLY validates loan applications against `economy_params.yaml` (LTV/DTI) and creates `LoanDTO` objects.
3.  **Testability First**: The `SagaTestHelper` is a **mandatory prerequisite**. Implementation of the saga itself shall not proceed until this test utility is functional.

---

## 2. API & DTO Definitions

The following interfaces and data structures, originally defined in `spec_h1_housing_v3_saga.md`, are confirmed. Note the comprehensive `status` literals which are critical for the state machine.

### DTOs

```python
from typing import TypedDict, List, Optional, Literal, Union
from modules.household.dtos import HouseholdStateDTO
from modules.housing.dtos import HousingMarketSnapshotDTO
from modules.finance.dtos import LoanDTO

# --- Saga-Specific DTOs ---

class MortgageApplicationDTO(TypedDict):
    """
    Formal mortgage application sent to the LoanMarket.
    Contains all data required for LTV/DTI checks.
    """
    applicant_id: int
    property_id: int
    offer_price: float
    loan_principal: float
    applicant_gross_income: float
    applicant_existing_debt_payments: float

class HousingPurchaseSagaDataDTO(TypedDict):
    """
    The data payload for the housing purchase saga.
    Carries all necessary information through the saga steps.
    """
    household_id: int
    property_id: int
    offer_price: float
    down_payment: float
    mortgage_application: MortgageApplicationDTO
    # This will be populated once the loan is approved
    approved_loan_id: Optional[int]
    # To log the reason for termination
    failure_reason: Optional[str]

class HousingPurchaseSagaDTO(TypedDict):
    """
    The stateful object representing a single housing purchase transaction.
    This will be managed by the SettlementSystem.
    """
    saga_id: str
    saga_type: Literal["HOUSING_PURCHASE"]
    status: Literal[
        "STARTED",                      # Initiated by DecisionUnit
        "LOAN_APPLICATION_PENDING",     # Submitted to LoanMarket, awaiting outcome
        "LOAN_APPROVED",                # Loan approved, ready for asset transfer
        "LOAN_REJECTED",                # Loan denied (LTV/DTI fail), saga terminated
        "PROPERTY_TRANSFER_PENDING",    # Atomic asset/property transfer in progress
        "COMPLETED",                    # All steps successful
        "FAILED_COMPENSATED"            # A failure occurred after the loan was approved, and state was rolled back
    ]
    current_step: int
    data: HousingPurchaseSagaDataDTO
```

### Interfaces

```python
from abc import ABC, abstractmethod
from .dtos import HousingPurchaseSagaDTO, MortgageApplicationDTO
from modules.finance.dtos import LoanDTO

class ILoanMarket(ABC):
    @abstractmethod
    def apply_for_mortgage(self, application: MortgageApplicationDTO) -> Optional[LoanDTO]:
        """
        Processes a mortgage application. Enforces LTV/DTI limits from SimulationConfig.
        Returns a new LoanDTO if approved, None otherwise.
        """
        ...

class ISettlementSystem(ABC):
    @abstractmethod
    def submit_saga(self, saga: HousingPurchaseSagaDTO) -> bool:
        """Submits a new saga to be processed."""
        ...
```

---

## 3. Detailed Saga State Machine (Inside `SettlementSystem`)

The `SettlementSystem` will gain a new internal registry (e.g., `self.sagas: Dict[str, HousingPurchaseSagaDTO]`) and a new processing method called during the tick sequence.

### Step 0: Initiation (Responsibility: `DecisionUnit`)

1.  **Trigger**: `HousingPlanner` returns a `HousingDecisionDTO` with `decision_type="MAKE_OFFER"`.
2.  **Action**: The `DecisionUnit` **constructs** a `HousingPurchaseSagaDTO`.
    -   `saga_id` is generated (e.g., `f"HPS_{household_id}_{tick_number}"`).
    -   `status` is set to `"STARTED"`.
    -   `current_step` is set to `0`.
    -   All `data` fields are populated.
3.  **Submission**: The `DecisionUnit` calls `SettlementSystem.submit_saga(saga_dto)`. The `SettlementSystem` adds it to its internal `self.sagas` registry.

### Step 1: Loan Application (Inside `SettlementSystem.process_sagas`, Tick T)

-   **Selector**: The system processes sagas with `status == "STARTED"`.
-   **Action**:
    1.  The `SettlementSystem` retrieves the `MortgageApplicationDTO` from the saga's data.
    2.  It invokes `self.loan_market.apply_for_mortgage(application)`.
-   **State Transition**:
    -   The saga's `status` is immediately updated to `"LOAN_APPLICATION_PENDING"`.
    -   `current_step` is incremented to `1`.
-   **NOTE**: The result of the application is not known in this tick. The saga is now waiting.

### Step 2: Loan Judgment (Inside `SettlementSystem.process_sagas`, Tick T+1 or later)

-   **Selector**: The system processes sagas with `status == "LOAN_APPLICATION_PENDING"`.
-   **Action**:
    1.  The `SettlementSystem` must query for the loan outcome. It does this by checking for a newly created `LoanDTO` linked to the `applicant_id` and `offer_price` (or a more direct event/ID lookup mechanism if available).
-   **State Transition (Path A: Success)**:
    -   **Condition**: A matching, approved `LoanDTO` is found.
    -   **Action**:
        1.  Update the saga's data: `approved_loan_id` is set to the new loan's ID.
    -   **New Status**: `"LOAN_APPROVED"`.
    -   `current_step` -> `2`.
-   **State Transition (Path B: Failure)**:
    -   **Condition**: No approved `LoanDTO` is found after a reasonable period (e.g., 1-2 ticks), or a `LoanRejection` event is found.
    -   **Action**:
        1.  Update saga data: `failure_reason` is set to `"Loan rejected by market (LTV/DTI failure)"`.
    -   **New Status**: `"LOAN_REJECTED"`. The saga is now terminal.
    -   `current_step` -> `2`.

### Step 3: Atomic Asset & Property Transfer (Inside `SettlementSystem.process_settlement`, Tick T+1)

This is the most critical step and leverages the `SettlementSystem`'s core atomicity guarantees.

-   **Selector**: The system processes sagas with `status == "LOAN_APPROVED"`.
-   **Action**: The `SettlementSystem` executes the following transfers **as a single, indivisible block**. If any one of these fails, they all fail.
    1.  **[Verify]** Confirm seller still owns `property_id` in the `Registry`. If not, trigger compensation (Step 4).
    2.  **[Debit]** Buyer's cash account by `data.down_payment`.
    3.  **[Credit]** Seller's cash account by `data.offer_price`.
    4.  **[Activate Loan]** Activate the `Loan` with `id == data.approved_loan_id`. This credits the buyer's cash by `loan_principal`.
    5.  **[Transfer Title]** Update the `Registry` to transfer ownership of `property_id` from seller to buyer.
-   **State Transition**:
    -   On successful execution of the entire block, set `status` to `"PROPERTY_TRANSFER_PENDING"`.
    -   `current_step` -> `3`.

### Step 4: Finalization & Compensation

-   **Selector (Success)**: Sagas with `status == "PROPERTY_TRANSFER_PENDING"`.
    -   **Action (Tick T+2)**: The system performs a final verification check on the ledger.
    -   **New Status**: `"COMPLETED"`. The saga can now be archived.
-   **Compensation (Rollback)**:
    -   **Trigger**: A failure during the atomic transfer in Step 3 (e.g., seller no longer owns the property).
    -   **Action**: The `SettlementSystem`'s atomic block automatically discards all partial changes. No manual rollback is needed for the financial transaction.
    -   **State Transition**:
        1.  The saga's `status` is set to `"FAILED_COMPENSATED"`.
        2.  `failure_reason` is set (e.g., "Property ownership check failed before transfer").
        3.  The saga is now terminal and can be archived.

---

## 4. Test Strategy (MANDATORY PREREQUISITE)

Development on the saga logic is **blocked** until the `SagaTestHelper` is implemented.

-   **Location**: `tests/helpers/saga_test_helper.py`
-   **Required Interface**:

    ```python
    class SagaTestHelper:
        def create_housing_saga(self, household, property, offer_price) -> HousingPurchaseSagaDTO:
            """Creates a valid, new saga DTO in the 'STARTED' state."""
            ...

        def place_saga_in_system(self, saga: HousingPurchaseSagaDTO, system: ISettlementSystem) -> None:
            """Injects a saga directly into the SettlementSystem's registry."""
            ...
            
        def get_saga_from_system(self, saga_id: str, system: ISettlementSystem) -> Optional[HousingPurchaseSagaDTO]:
            """Retrieves a saga's current state from the system."""
            ...
    ```
-   **Key Test Cases**:
    1.  **Test DTI Failure**: Use the helper to create a saga for a highly indebted household. `place_saga_in_system`. Advance the simulation. **Assert** the final saga status is `"LOAN_REJECTED"` and no assets have moved.
    2.  **Test Successful Purchase**: Use a valid household. `place_saga_in_system`. Advance the simulation by several ticks. **Assert** the final saga status is `"COMPLETED"`, the property is transferred, and the mortgage exists.
    3.  **Test Mid-flight Ownership Change (Compensation)**:
        a. `place_saga_in_system` for a valid purchase to get it to `LOAN_APPROVED` state.
        b. Manually transfer the target property to another agent.
        c. Advance the simulation.
        d. **Assert** the final saga status is `"FAILED_COMPENSATED"` and the buyer's down payment was not taken.

---

## 5. Configuration

The following fields **MUST** be added to `config/economy_params.yaml`:

```yaml
regulations:
  # Maximum Loan-to-Value ratio for mortgages. 80% LTV means 20% down payment required.
  max_ltv_ratio: 0.8
  # Maximum Debt-to-Income ratio. All debt payments cannot exceed this fraction of gross income.
  max_dti_ratio: 0.4
```

---

## 6. Response to Pre-flight Audit

-   **`SettlementSystem` Primacy**: **ADDRESSED**. This design exclusively uses the `SettlementSystem` as the saga coordinator.
-   **Modification Complexity**: **MITIGATED**. The saga logic will be encapsulated in a new, dedicated method (`_process_sagas`) within the `SettlementSystem`. State transitions are managed via the `status` field, isolating this flow from existing settlement types (e.g., order matching).
-   **Testability Risk**: **ADDRESSED**. The mandatory `SagaTestHelper` is a core part of this specification and provides the necessary tooling for isolated, state-specific testing, de-risking the implementation.
-   **SRP**: **ENFORCED**. The detailed state machine explicitly defines the one-way flow of command from `DecisionUnit` to `SettlementSystem`, preserving the strict roles of all involved components.
