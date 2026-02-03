# Spec: Finance System Refactor (TD-197 & TD-207)

**Version**: 1.0
**Date**: 2026-02-03
**Author**: Gemini Scribe

## 1. Overview & Goals

This document specifies the architectural changes required to address two critical technical debt items: **TD-197 (Final Burial of HousingManager)** and **TD-207 (Atomic Loan Staging)**. The current `SettlementSystem` has become a "God Class," handling financial transfers, housing transaction orchestration, and estate settlements. This violates the Single Responsibility Principle and creates tight coupling that hinders modularity.

The goals of this refactor are:
1.  **Decouple Housing Logic**: Extract the housing transaction saga state machine from `SettlementSystem` into a dedicated orchestrator, formally burying the legacy `HousingManager`'s responsibilities (TD-197).
2.  **Isolate Loan Staging**: Implement a new `LoanStagingArea` to manage the lifecycle of approved-but-unfunded loans, ensuring financial statistics (like M2) are only updated upon actual fund transfer (TD-207).
3.  **Refine SettlementSystem**: Refocus `SettlementSystem` on its core, audited responsibility: executing atomic, zero-sum financial operations.

## 2. Solution Part 1: Housing Saga Orchestrator (TD-197)

To resolve TD-197, we will introduce a new, dedicated system for managing the complex state machine of housing transactions.

### 2.1. System Design: `HousingSagaOrchestrator`

-   **Responsibility**: This new system will be the sole owner of the housing purchase saga lifecycle. It will contain the state (`active_sagas`) and the processing logic currently located in `SettlementSystem.process_sagas`.
-   **Dependencies**:
    -   It will be a client of the `ISettlementSystem` to execute financial transfers (down payments, mortgage disbursements).
    -   It will depend on an `IAgentProvider` interface to retrieve agent objects, breaking the "God Object" dependency on the global `simulation_state`.
    -   It will use the existing `HousingTransactionSagaHandler` to execute individual saga steps.

### 2.2. `SettlementSystem` Refactoring

The following members and methods will be **removed** from `SettlementSystem`:
-   `active_sagas: Dict[UUID, HousingTransactionSagaStateDTO]`
-   `submit_saga(self, saga: Any) -> bool`
-   `process_sagas(self, simulation_state: Any) -> None`
-   `find_and_compensate_by_agent(self, agent_id: int, ...) -> None`

`SettlementSystem` will revert to being a stateless (or near-stateless) service for financial transfers and estate settlement execution.

## 3. Solution Part 2: Atomic Loan Staging Area (TD-207)

To resolve TD-207, we will introduce a system to buffer approved loans before funding.

### 3.1. System Design: `LoanStagingArea`

-   **Responsibility**: This system acts as a temporary holding area for loan agreements that have been approved by a lender but not yet funded. Its primary purpose is to decouple loan approval from the atomic funding event.
-   **State**: It will maintain a dictionary of `LoanStageDTO` objects, representing loans awaiting funding.
-   **Client Relationship**: The `LoanStagingArea` will be a **client** of the `ISettlementSystem`. It will not have its own ledger.
-   **Workflow**:
    1.  A lender agent (e.g., a Bank) approves a loan and calls `LoanStagingArea.stage_loan()`, passing the loan details.
    2.  The `TickOrchestrator` calls `LoanStagingArea.process_staged_loans()` at the appropriate time.
    3.  For each staged loan, the `LoanStagingArea` calls `ISettlementSystem.transfer()` to move funds from the lender to the borrower.
    4.  **Critical**: It must handle transfer failures (e.g., lender has insufficient funds at the time of processing, a risk highlighted by the "Seamless Payments" feature audit). A failed transfer will result in the loan being marked as `FAILED` or rescheduled, preventing money supply corruption.

## 4. API & Interface Definitions

The following new API files and interfaces will be created.

### 4.1. `modules/finance/housing_saga_api.py`

```python
# modules/finance/housing_saga_api.py
from typing import Protocol, Any, Dict, Optional
from uuid import UUID

from modules.common.dtos import AgentId
from modules.finance.dtos import HousingTransactionSagaStateDTO

class IAgentProvider(Protocol):
    """
    An interface to abstract the retrieval of agent objects, breaking the
    dependency on the global simulation_state.
    """
    def get_agent(self, agent_id: AgentId) -> Optional[Any]:
        """Retrieves an agent by its ID."""
        ...

class IHousingSagaOrchestrator(Protocol):
    """
    Orchestrates the lifecycle of complex, multi-step housing transactions.
    """
    active_sagas: Dict[UUID, HousingTransactionSagaStateDTO]

    def submit_saga(self, saga_dto: HousingTransactionSagaStateDTO) -> bool:
        """
        Submits a new housing transaction saga to be processed.
        Returns True on successful submission.
        """
        ...

    def process_sagas(self) -> None:
        """
        Processes all active sagas, advancing their state machines.
        This should be called once per simulation tick.
        """
        ...

    def compensate_by_agent(self, agent_id: AgentId) -> None:
        """
        Finds all sagas involving a specific agent and triggers compensation
        (rollback) for them. Used when an agent unexpectedly dies or is removed.
        """
        ...
```

### 4.2. `modules/finance/loan_staging_api.py`

```python
# modules/finance/loan_staging_api.py
from typing import Protocol, List, Optional, Literal
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from modules.common.dtos import AgentId
from simulation.finance.api import ITransaction

LoanPurpose = Literal["mortgage", "business", "personal", "other"]
LoanStageStatus = Literal["PENDING", "PROCESSED", "FAILED"]

@dataclass
class LoanStageDTO:
    """
    Data Transfer Object representing a loan approved by a lender but
    not yet funded.
    """
    stage_id: UUID = field(default_factory=uuid4)
    lender_id: AgentId
    borrower_id: AgentId
    amount: float
    purpose: LoanPurpose
    memo: str
    status: LoanStageStatus = "PENDING"
    tick_staged: int

class ILoanStagingArea(Protocol):
    """
    Manages the lifecycle of approved but not-yet-funded loans, decoupling
    approval from the atomic funding event.
    """
    def stage_loan(self, loan_dto: LoanStageDTO) -> UUID:
        """
        Adds a new loan to the staging area.
        Returns the unique ID for the staged loan.
        """
        ...

    def process_staged_loans(self, tick: int) -> List[ITransaction]:
        """
        Attempts to fund all PENDING loans in the staging area by calling
        the SettlementSystem.

        Returns a list of successful transaction records.
        """
        ...

    def get_staged_loan(self, stage_id: UUID) -> Optional[LoanStageDTO]:
        """Retrieves a staged loan by its ID."""
        ...
```

### 4.3. `simulation/finance/api.py` (Updated `ISettlementSystem`)

The `ISettlementSystem` interface will be simplified, with saga-related methods removed.

```python
# simulation/finance/api.py (snippet)

class ISettlementSystem(Protocol):
    """
    Centralized system for handling all atomic financial transfers and
    estate settlements. Enforces zero-sum integrity.
    """
    # ... (submit_saga, process_sagas, find_and_compensate_by_agent are REMOVED)

    def transfer(
        self,
        debit_agent: IFinancialEntity,
        credit_agent: IFinancialEntity,
        amount: float,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0
    ) -> Optional[ITransaction]:
        """
        Executes an atomic transfer from debit_agent to credit_agent.
        Returns a Transaction object (truthy) on success, None (falsy) on failure.
        """
        ...

    def settle_atomic(
        self,
        debit_agent: IFinancialEntity,
        credits_list: List[Tuple[IFinancialEntity, float, str]],
        tick: int
    ) -> bool:
        ...

    # ... other transfer/settlement methods remain ...
```

## 5. Verification Plan & Mocking Strategy

-   **`HousingSagaOrchestrator` Tests**:
    -   Unit tests will verify the state machine logic.
    -   Dependencies (`ISettlementSystem`, `IAgentProvider`, `IHousingTransactionSagaHandler`) will be mocked.
    -   An integration test will use a real `HousingTransactionSagaHandler` and a mock `ISettlementSystem` to verify the components work together.
-   **`LoanStagingArea` Tests**:
    -   Unit tests will verify that loans can be staged, processed, and their status updated correctly.
    -   The `ISettlementSystem` dependency will be mocked to simulate both successful and failed transfers. Tests must assert that the `LoanStageDTO` status is correctly set to `PROCESSED` on success and `FAILED` on failure.
-   **`SettlementSystem` Tests**:
    -   Existing tests for `transfer` and other core financial methods remain vital.
    -   Tests related to saga processing should be migrated to test the `HousingSagaOrchestrator`.
-   **Mocking Data**:
    -   **Use Golden Fixtures**: Tests should leverage existing `conftest.py` fixtures like `golden_households` and `golden_firms` as agent instances wherever possible, as mandated by project protocol. Avoid `MagicMock` for agent simulation.

## 6. Risk & Impact Audit (Post-Design)

This design directly addresses the risks identified in the pre-flight audit:

-   ✅ **(TD-197) God Class / Housing Logic**: The `HousingSagaOrchestrator` extracts the stateful saga logic, cleaning up `SettlementSystem` and providing a clear, decoupled home for housing transaction management.
-   ✅ **(TD-197) God Object Dependency**: The `IAgentProvider` interface eliminates the direct dependency on `simulation_state`, improving testability and modularity.
-   ✅ **(TD-207) Atomic Staging**: The `LoanStagingArea` is defined as a client of `SettlementSystem`, ensuring all fund movements occur through the audited, zero-sum atomic transfer methods. This preserves M2 integrity.
-   ✅ **(TD-207) Seamless Payment Risk**: The specification for `LoanStagingArea` explicitly requires it to handle transfer failures from `SettlementSystem`, mitigating the risk of a lender's funds being insufficient at the time of processing.
-   ✅ **Circular Dependencies**: The proposed architecture is directional and avoids circular dependencies:
    -   `HousingSagaOrchestrator` -> `ISettlementSystem`
    -   `LoanStagingArea` -> `ISettlementSystem`
-   **Test Impact**: Significant. Tests for `SettlementSystem`'s saga functionality must be moved and adapted for the new `HousingSagaOrchestrator`. This is a necessary consequence of the refactoring.

## 7. Implementation Plan

1.  **Phase 1: API & Scaffolding**
    -   Create the new API files: `housing_saga_api.py` and `loan_staging_api.py`.
    -   Update `simulation/finance/api.py`.
    -   Create skeleton implementations of `HousingSagaOrchestrator` and `LoanStagingArea`.
2.  **Phase 2: Logic Migration & Implementation**
    -   Move saga-related state and logic from `SettlementSystem` to `HousingSagaOrchestrator`.
    -   Implement the `LoanStagingArea` logic, including failure handling for transfers.
3.  **Phase 3: Integration & Test Migration**
    -   Update the `TickOrchestrator` (or equivalent main loop) to call the new systems.
    -   Migrate and update all relevant tests.
    -   Remove the legacy code from `SettlementSystem`.
4.  **Phase 4: Final Burial**
    -   Delete the now-empty `HousingManager` module if it still exists.

---
**[Jules Insight Logging]**: This refactoring effort will create significant churn in the finance module. It is critical that all related tests are migrated and pass before merging to prevent regressions in financial atomicity. A dedicated test plan for verifying zero-sum transfers during housing sagas and loan processing is recommended. This insight is logged under `communications/insights/TD197-207-Refactor.md`.
