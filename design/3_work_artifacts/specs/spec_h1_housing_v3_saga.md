# Spec: Atomic Housing Purchase via Settlement Saga

- **Mission**: Implement a fully atomic, multi-tick housing purchase process that incorporates macro-prudential regulations (LTV/DTI).
- **Objective**: Leverage the existing `SettlementSystem` as a Saga coordinator to ensure transactional integrity, preventing financial leaks and inconsistent state during property acquisition. This resolves the core transactional risk of `Phase 32`.

---

## 1. API Definition (`modules/market/housing_purchase_api.py`)

This API introduces the necessary DTOs and interfaces to manage the housing purchase saga.

### DTOs

```python
from typing import TypedDict, List, Optional, Literal, Union
from modules.household.dtos import HouseholdStateDTO
from modules.housing.dtos import HousingMarketSnapshotDTO
from modules.finance.dtos import LoanDTO # Assumed from project structure

# Pre-existing DTO from spec_td065, used as input to the saga
class HousingOfferRequestDTO(TypedDict):
    household_state: HouseholdStateDTO
    housing_market_snapshot: HousingMarketSnapshotDTO

# Pre-existing DTO from spec_td065, represents the planner's output
class HousingDecisionDTO(TypedDict):
    decision_type: Literal["MAKE_OFFER", "RENT", "STAY", "DO_NOTHING"]
    target_property_id: Optional[int]
    offer_price: Optional[float]
    # The loan application is now part of the saga, not the initial decision
    
# NEW DTOs for the Saga Pattern

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

class HousingPurchaseSagaDTO(TypedDict):
    """
    The stateful object representing a single housing purchase transaction.
    This will be managed by the SettlementSystem.
    """
    saga_id: str
    saga_type: Literal["HOUSING_PURCHASE"]
    status: Literal[
        "STARTED",
        "LOAN_APPLICATION_PENDING",
        "LOAN_APPROVED",
        "LOAN_REJECTED",
        "PROPERTY_TRANSFER_PENDING",
        "COMPLETED",
        "FAILED_COMPENSATED"
    ]
    current_step: int
    data: HousingPurchaseSagaDataDTO
```

### Interfaces

```python
from abc import ABC, abstractmethod
from .dtos import HousingOfferRequestDTO, HousingDecisionDTO, HousingPurchaseSagaDTO, MortgageApplicationDTO
from modules.finance.dtos import LoanDTO

class IHousingPlanner(ABC):
    """
    Stateless interface for making housing decisions (unchanged from spec_td065).
    """
    @abstractmethod
    def evaluate_housing_options(self, request: HousingOfferRequestDTO) -> HousingDecisionDTO:
        ...

class ILoanMarket(ABC):
    """
    Interface for the LoanMarket, now including regulatory checks.
    """
    @abstractmethod
    def apply_for_mortgage(self, application: MortgageApplicationDTO) -> Optional[LoanDTO]:
        """
        Processes a mortgage application.
        - Enforces hard LTV/DTI limits from SimulationConfig.
        - Returns a new LoanDTO if approved, None otherwise.
        """
        ...

class ISettlementSystem(ABC):
    """
    Interface for the system that guarantees atomic, multi-step transactions.
    """
    @abstractmethod
    def submit_saga(self, saga: HousingPurchaseSagaDTO) -> bool:
        """
        Submits a new saga to be processed.
        """
        ...
```

---

## 2. Saga Process Specification ("Settlement Saga")

The purchase process is a Saga coordinated by the `SettlementSystem`, ensuring atomicity across multiple simulation ticks. This reuses the established `SettlementSystem` pattern, as mandated by the architecture.

### Saga States & Flow

- **Initiation (`DecisionUnit`)**:
    1.  `DecisionUnit` calls `HousingPlanner.evaluate_housing_options()`.
    2.  If the decision is `MAKE_OFFER`, the `DecisionUnit` **does not** create orders directly.
    3.  Instead, it constructs the `HousingPurchaseSagaDTO` with `status="STARTED"` and `current_step=0`.
    4.  It submits this DTO to the `SettlementSystem`.

- **Execution (`SettlementSystem` within the `TickOrchestrator` phases):**

    - **Step 1: `LOAN_APPLICATION_PENDING` (Tick T)**
        - **Action**: The `SettlementSystem` picks up the `STARTED` saga. It invokes `ILoanMarket.apply_for_mortgage()` with the `MortgageApplicationDTO` from the saga data.
        - **State Change**: `status` -> `LOAN_APPLICATION_PENDING`.

    - **Step 2: `LOAN_APPROVED` / `LOAN_REJECTED` (Tick T+1, or later)**
        - **Action**: The system checks the outcome of the loan application. The `LoanMarket` will have processed it, enforcing LTV/DTI checks against `SimulationConfig` values.
        - **State Change (Success)**: If a `LoanDTO` was created, update saga: `status` -> `LOAN_APPROVED`, `approved_loan_id` is set.
        - **State Change (Failure)**: If `None` was returned (LTV/DTI fail), update saga: `status` -> `LOAN_REJECTED`. The saga terminates. No compensation is needed as no assets have moved.

    - **Step 3: `PROPERTY_TRANSFER_PENDING` (Tick T+1, same tick as loan approval)**
        - **Action**: For an `LOAN_APPROVED` saga, the `SettlementSystem` executes the financial and property transfers **within one of its atomic settlement phases**.
            - Debit buyer's account for `down_payment`.
            - Credit seller's account for `offer_price`.
            - Activate the `Loan` (credit buyer's account for `loan_principal`).
            - Transfer `property_id` from seller to buyer in the `Registry`.
        - **State Change**: `status` -> `PROPERTY_TRANSFER_PENDING`.

    - **Step 4: `COMPLETED` (Tick T+2)**
        - **Action**: The system verifies the successful transfer from the previous tick.
        - **State Change**: `status` -> `COMPLETED`. The saga is archived.

- **Compensation (Rollback)**:
    - The `SettlementSystem` is already built for atomicity. If Step 3 fails for any reason (e.g., seller no longer owns property), the entire settlement block for that saga is rolled back. No partial state is committed.
    - The saga status is then moved to `FAILED_COMPENSATED` and archived.

---

## 3. Component Responsibility & Audit Compliance

This design directly addresses the pre-flight audit findings:

- **`HousingPlanner`**: Remains stateless and confined to decision logic, satisfying **SRP**. It does not know the Saga exists.
- **`DecisionUnit`**: Acts as the Saga initiator only. It is fire-and-forget. The Saga's state machine is fully encapsulated within the **`SettlementSystem`**, preventing logic bleed.
- **`LoanMarket`**: Is the designated **gatekeeper for LTV/DTI enforcement**, as required.
- **`SettlementSystem`**: Fulfills its role as the project's **master of atomic transactions**, now extended to coordinating Sagas. This reuses the **`SettlementSystem` Precedent** and integrates seamlessly with the **"Ordered Universe"** tick sequence.

---

## 4. Verification Plan

The `scripts/verify_housing_transaction_integrity.py` script will be updated to validate the Saga flow.

- **Goal**: Prove that the housing purchase saga is atomic and correctly handles both success and failure paths.
- **Methodology**:
    1.  Initialize a simulation.
    2.  Force a household to initiate a housing purchase.
    3.  Query the `SettlementSystem` to find the `HousingPurchaseSagaDTO`.
- **Success Criteria (Assertions)**:
    1.  **ASSERT `Saga Initiation`**: A saga is created with `status="STARTED"`.
    2.  **ASSERT `Loan Pending`**: The saga moves to `status="LOAN_APPLICATION_PENDING"` in the same tick.
    3.  **ASSERT `Loan Rejection (DTI Fail)`**:
        - Configure a household with high existing debt.
        - Trigger a purchase.
        - **Assert** the saga moves to `status="LOAN_REJECTED"`.
        - **Assert** no change in household assets or property ownership.
    4.  **ASSERT `Atomic Transfer (Success)`**:
        - Use a valid applicant.
        - **Assert** the saga moves through `LOAN_APPROVED` and `PROPERTY_TRANSFER_PENDING` to `COMPLETED`.
        - **Assert** property ownership is transferred, assets are debited correctly, and a `Mortgage` liability exists.

---

## 5. Risk & Impact Audit

-   **Transactional Integrity**: **MITIGATED**. By delegating coordination to the existing, trusted `SettlementSystem`, we avoid creating a new, bespoke, and likely buggy transaction manager. The risk is shifted to correct implementation of the saga *within* the proven system.
-   **Test Impact**: **ADDRESSED**. The complexity of mocking a multi-step saga is acknowledged. A `SagaTestHelper` will be developed. It will provide functions like `create_and_place_saga_in_state(system, state, data)` to allow unit tests to target specific steps (e.g., test the property transfer logic) without running the full simulation cycle. This protects the "Operation Green Light" objective.
-   **Dependencies**: This work remains dependent on a functional `LoanMarket` and `Registry`.
-   **Configuration**: The `economy_params.yaml` must be extended with:
    - `regulations.max_ltv_ratio: 0.8` (Loan-to-Value)
    - `regulations.max_dti_ratio: 0.4` (Debt-to-Income)
