File: modules/finance/sagas/housing_api.py
```python
from typing import TypedDict, Literal, Optional, Protocol, List, Dict, Union
from uuid import UUID
from dataclasses import dataclass
from modules.finance.api import MortgageApplicationDTO
from modules.simulation.api import AgentID

# --- DTOs for Saga State & Payloads ---

@dataclass(frozen=True)
class MortgageApprovalDTO:
    """
    Represents the confirmed details of an approved mortgage.
    """
    loan_id: str  # Bank-issued unique loan identifier (string)
    lien_id: str  # Registry-issued unique lien identifier
    approved_principal: float
    monthly_payment: float

@dataclass(frozen=True)
class SagaParticipantDTO:
    """
    Unified context for any agent participating in a Saga.
    Resolves ID desync between Household (household_id) and Firm/Agent (id).
    """
    agent_id: AgentID
    monthly_income: float
    existing_monthly_debt: float
    liquid_assets: float # Added for solvency checks during saga
    is_human: bool = False # Optional metadata for decision logic

@dataclass
class HousingTransactionSagaStateDTO:
    """
    State object for the multi-tick housing purchase Saga.
    Refactored to use unified SagaParticipantDTO for strict typing.
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
        "FAILED_ROLLED_BACK",
        "CANCELLED"             # Added to support cancellation logic
    ]
    buyer_context: SagaParticipantDTO
    seller_context: SagaParticipantDTO
    property_id: int
    offer_price: float
    down_payment_amount: float

    # State-specific payloads, populated as the saga progresses
    loan_application: Optional[MortgageApplicationDTO] = None
    mortgage_approval: Optional[MortgageApprovalDTO] = None

    # Tracking IDs for compensation
    staged_loan_id: Optional[str] = None

    # Error logging
    error_message: Optional[str] = None
    last_processed_tick: int = 0
    logs: List[str] = None

# --- System Interfaces ---

class IProperty(Protocol):
    id: int
    owner_id: int
    is_under_contract: bool
    liens: List[str]

class IPropertyRegistry(Protocol):
    """
    Interface for a system managing property ownership and status.
    Alias or refinement of IRealEstateRegistry for the Saga context.
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

File: design/3_work_artifacts/specs/lane2_lifecycle_saga_spec.md
```markdown
# Lane 2 Specification: Lifecycle & Saga Unification

## 1. Overview
This specification addresses two critical structural flaws identified in the Lane 2 Audit:
1.  **Ghost Firm Race Condition**: A temporal coupling issue where firms are funded before being registered, causing settlement failures.
2.  **Saga Participant ID Desync**: Inconsistent DTO schemas for Saga participants causing runtime errors and convoluted fallback logic in the Orchestrator.

The goal is to enforce a strict **Instantiate -> Register -> Fund** lifecycle and unify the Saga data model.

## 2. Architecture & Design Changes

### 2.1. Atomic Registration Protocol (Simulation)
We define a strict protocol for adding agents to the simulation.
-   **Current State**: Ad-hoc appending to `simulation.firms` and `simulation.agents`.
-   **New State**: `Simulation.register_agent(agent: IAgent)`
    -   Must add to global `agents` map (Lookup).
    -   Must add to type-specific lists (`firms`, `households`) (Iteration).
    -   Must be called **BEFORE** any financial interaction.

### 2.2. Firm Creation Sequence (Refactor)
The `FirmSystem.spawn_firm` method will be reordered:
1.  **Instantiation**: Create `Firm` object (Balance = 0).
2.  **Registration**: Call `simulation.register_agent(new_firm)`.
    -   *Checkpoint*: Firm exists in `simulation.agents` and can be looked up by `SettlementSystem`.
3.  **Funding**: Call `settlement_system.transfer(founder, new_firm, capital)`.
    -   *Logic*: Settlement system resolves `new_firm.id` successfully.
4.  **Activation**: Firm is now live.

### 2.3. Unified Saga DTO
We introduce `SagaParticipantDTO` to replace `HouseholdSnapshotDTO` and `HousingSagaAgentContext` within the Saga scope. This forces `buyer_context.agent_id` and `seller_context.agent_id` to be structurally identical.

## 3. Implementation Steps

### Step 1: DTO Unification (Breaking Change)
-   **Target**: `modules/finance/sagas/housing_api.py`
-   **Action**: Replace `buyer_context` and `seller_context` types with `SagaParticipantDTO`.
-   **Impact**: This will break `SagaOrchestrator` and `HousingTransactionSagaHandler` immediately. This is intentional.

### Step 2: Orchestrator Refactoring
-   **Target**: `modules/finance/sagas/orchestrator.py`
-   **Action**:
    -   Remove the "Dict Compatibility Hack" (L65-83).
    -   Remove `getattr` fallbacks (L93-104).
    -   Implement strict DTO usage: `buyer_id = saga.buyer_context.agent_id`.
    -   Update `submit_saga` to validate `SagaParticipantDTO` structure.

### Step 3: Firm Lifecycle Repair
-   **Target**: `simulation/systems/firm_management.py`
-   **Action**:
    -   Move `simulation.firms.append(new_firm)` and `simulation.agents[new_firm.id] = new_firm` **BEFORE** `settlement_system.transfer`.
    -   Ensure `new_firm` is fully initialized (except capital) before registration.

### Step 4: Test Suite Realignment
-   **Impacted Tests**:
    -   `tests/modules/finance/test_saga_orchestrator.py`: Mock payloads must be updated to use `SagaParticipantDTO`.
    -   `tests/simulation/systems/test_firm_management.py`: Verify spawning doesn't raise `Destination account does not exist`.

## 4. Verification Plan

### 4.1. New Test Cases
```python
def test_spawn_firm_registration_order(simulation, firm_system, wealthy_household):
    # Setup: Mock Settlement System to fail if agent not found in registry
    simulation.settlement_system.transfer.side_effect = lambda s, d, a, m, t: \
        _verify_agent_exists(d.id, simulation.agents)
    
    # Act
    firm = firm_system.spawn_firm(simulation, wealthy_household)
    
    # Assert
    assert firm is not None
    assert firm.id in simulation.agents
```

### 4.2. Existing Test Impact
-   **DTO Updates**: All tests instantiating `HousingTransactionSagaStateDTO` must be updated.
-   **Mock Updates**: Mocks of `Simulation` in `test_firm_management.py` must support the `agents` dict lookup if they didn't already.

## 5. Technical Debt Ledger Audit

| ID | Status | Note |
| :--- | :--- | :--- |
| **TD-ARCH-STARTUP-RACE** | **RESOLVED** | Registration-First pattern enforced. |
| **TD-FIN-SAGA-ORPHAN** | **RESOLVED** | Unified DTO prevents participant ID loss. |
| **TD-ARCH-ORCH-HARD** | **RESOLVED** | Orchestrator fragility reduced by removing dynamic fallback logic. |

## 6. Risk Assessment
-   **Breaking Change**: The DTO change is incompatible with any serialized Sagas from previous runs (not an issue for in-memory simulation, but relevant for checkpoints).
-   **Mitigation**: Clear old checkpoints or implement a migration script if persistence is active.

```

File: communications/insights/lane2-structural-spec.md
```markdown
# Insight Report: Lane 2 Structural Spec (Lifecycle & Sagas)

## 1. Architectural Insights
-   **Lifecycle Sequencing**: The previous failure to enforce "Register before Interact" was a fundamental violation of the Actor Model. Agents cannot receive messages (money) before they exist in the address book (registry).
-   **DTO Purity**: The `SagaOrchestrator` was carrying significant complexity solely to support malformed or inconsistent input data. By enforcing strict DTOs upstream, we reduce the complexity of the critical path (Orchestrator) and move validation to the boundary.

## 2. Regression Analysis
-   **Potential Breakage**: `tests/modules/finance/test_saga_orchestrator.py` will fail compilation/execution because `HousingTransactionSagaStateDTO` signature has changed.
-   **Fix Strategy**: 
    -   Construct `SagaParticipantDTO` instances in the test setup.
    -   Replace dictionary-based mock payloads with typed DTOs where possible.
-   **Potential Breakage**: `simulation/systems/firm_management.py` logic inversion might fail if `simulation.agents` is not a mutable dict in some mock contexts.
-   **Fix Strategy**: Ensure `Simulation` mocks in `conftest.py` provide a real `dict` for `agents`.

## 3. Technology Debt Updates
-   **Resolved**: `TD-ARCH-STARTUP-RACE` (Ghost Firm Registry)
-   **Resolved**: `TD-FIN-SAGA-ORPHAN` (Saga Participant Drift)
-   **Resolved**: `TD-ARCH-ORCH-HARD` (Orchestrator Fragility - Partial)

## 4. Implementation Directives
-   **Do not rely on `getattr`**: The new `SagaOrchestrator` implementation must assume `saga.buyer_context.agent_id` exists. If it doesn't, let it raise `AttributeError` during development to catch the bug, rather than silencing it.
-   **Atomic Register**: If `register_agent` fails, the `spawn_firm` process must abort *before* transferring money.
```