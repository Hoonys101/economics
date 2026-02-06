```markdown
# Spec: Settlement System & Saga Orchestration Refactor (TD-253)

## 1. Project Overview

- **Goal**: Address critical technical debt (TD-253, TD-254, TD-255, TD-258) by refactoring the `SettlementSystem` God Class.
- **Scope**:
    1.  Decouple Saga orchestration logic from the transactional kernel.
    2.  Introduce a dedicated `MonetaryLedger` to correctly track money supply changes.
    3.  Enforce strict `IFinancialEntity` interface contracts, eliminating `hasattr` checks.
- **Key Features**:
    - New `SagaOrchestrator` Service.
    - New `MonetaryLedger` Service.
    - Slimmed, purely transactional `SettlementSystem`.
    - `FinancialEntityAdapter` for backward compatibility during transition.

## 2. Component & API Design

### 2.1. `SagaOrchestrator` Service
This service becomes the single source of truth for managing long-running business transactions (Sagas).

-   **Location**: `modules/finance/sagas/orchestrator.py`
-   **Responsibilities**:
    -   Manages the state of all active sagas (`active_sagas`).
    -   Drives saga state transitions via `process_sagas`.
    -   Provides an interface for submitting new sagas.
    -   Handles saga compensation logic, including lookups by agent ID.
-   **Dependencies (Injected)**:
    -   `simulation_state: ISimulationState` (For handler instantiation, to be minimized).
-   **Proposed API (`ISagaOrchestrator`)**:
    ```python
    class ISagaOrchestrator(Protocol):
        def submit_saga(self, saga: HousingTransactionSagaStateDTO) -> bool: ...
        def process_sagas(self) -> None: ...
        def find_and_compensate_by_agent(self, agent_id: int, handler: IHousingTransactionSagaHandler) -> None: ...
        def get_active_sagas(self) -> Dict[UUID, HousingTransactionSagaStateDTO]: ...
    ```

### 2.2. `MonetaryLedger` Service
This service is responsible for observing and recording events that impact the M2 money supply without being a direct mint/burn action by the Central Bank.

-   **Location**: `modules/finance/kernel/ledger.py`
-   **Responsibilities**:
    -   Provides a dedicated interface for logging credit expansion/destruction.
    -   Creates standardized `Transaction` records for monetary policy observation.
    -   Ensures that saga handlers and other domain logic do not manually inject transactions into the global state (`TD-258`).
-   **Dependencies (Injected)**:
    -   `transaction_log: List[Transaction]` (A reference to the simulation's central transaction list).
    -   `time_oracle: ITimeOracle` (To get the current tick).
-   **Proposed API (`IMonetaryLedger`)**:
    ```python
    class IMonetaryLedger(Protocol):
        def record_credit_expansion(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None: ...
        def record_credit_destruction(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None: ...
    ```

### 2.3. `SettlementSystem` (Refactored)
The kernel is reduced to its core responsibility: executing atomic transfers.

-   **Location**: `simulation/systems/settlement_system.py`
-   **Responsibilities**:
    -   Atomically execute all financial transfers (1-to-1, 1-to-many, multi-party).
    -   Handle inheritance and liquidation asset distribution.
    -   Enforce zero-sum integrity for all its operations.
    -   **It will be completely unaware of Sagas.**
-   **API Changes (`ISettlementSystem`)**:
    -   **REMOVED**: `submit_saga`, `process_sagas`, `find_and_compensate_by_agent`, `active_sagas`.
    -   **UNCHANGED (Conceptually)**: `transfer`, `settle_atomic`, `execute_multiparty_settlement`, `create_and_transfer`, etc.
    -   **INTERNAL CHANGE**: `_execute_withdrawal` will be refactored to use the `FinancialEntityAdapter`.

### 2.4. `FinancialEntityAdapter` Utility
A transitional component to bridge legacy agent classes with the strict `IFinancialEntity` interface.

-   **Location**: `modules/finance/kernel/adapters.py`
-   **Responsibilities**:
    -   Wrap any agent-like object.
    -   Expose the methods defined in `IFinancialEntity` (`deposit`, `withdraw`, `get_balance`).
    -   Internally, it will contain the `hasattr` logic previously in `SettlementSystem` to find the correct asset attribute (`wallet`, `finance.balance`, `assets`, etc.).
-   **Usage**:
    ```python
    # Inside SettlementSystem._execute_withdrawal
    adapted_agent = FinancialEntityAdapter(agent)
    if adapted_agent.get_balance() < amount:
        # ... failure logic
    adapted_agent.withdraw(amount)
    ```

## 3. Logic and Pseudo-code

### 3.1. `HousingTransactionSagaHandler` Refactor
The handler no longer creates `Transaction` objects directly. It calls the new `IMonetaryLedger`.

```python
# In HousingTransactionSagaHandler._handle_escrow_locked

class HousingTransactionSagaHandler(IHousingTransactionSagaHandler):
    def __init__(self, simulation: ISimulationState):
        self.simulation = simulation
        self.settlement_system: ISettlementSystem = simulation.settlement_system
        self.monetary_ledger: IMonetaryLedger = simulation.monetary_ledger # Injected
        # ... other services

    def _handle_escrow_locked(self, saga: HousingTransactionSagaStateDTO) -> HousingTransactionSagaStateDTO:
        # ... setup transfers ...
        success = self.settlement_system.execute_multiparty_settlement(transfers, self.simulation.time)

        if success:
            # OLD CODE (to be removed)
            # tx_credit = Transaction(...)
            # self.simulation.world_state.transactions.append(tx_credit)

            # NEW CODE
            if principal > 0:
                self.monetary_ledger.record_credit_expansion(
                    amount=principal,
                    saga_id=saga['saga_id'],
                    loan_id=saga['mortgage_approval']['loan_id'],
                    reason="mortgage_disbursal"
                )

            saga['status'] = "TRANSFER_TITLE"
            return saga
        else:
            saga['error_message'] = "Settlement failed"
            return self.compensate_step(saga)

    def _reverse_settlement(self, saga: HousingTransactionSagaStateDTO):
        # ... setup reverse transfers ...
        self.settlement_system.execute_multiparty_settlement(transfers, self.simulation.time)

        # NEW CODE
        if principal > 0:
            self.monetary_ledger.record_credit_destruction(
                amount=principal,
                saga_id=saga['saga_id'],
                loan_id=saga['mortgage_approval']['loan_id'],
                reason="mortgage_rollback"
            )
```

### 3.2. `SagaOrchestrator` Implementation Sketch

```python
# In modules/finance/sagas/orchestrator.py

class SagaOrchestrator(ISagaOrchestrator):
    def __init__(self, simulation_state: ISimulationState):
        self._sim = simulation_state
        self.active_sagas: Dict[UUID, HousingTransactionSagaStateDTO] = {}

    def process_sagas(self) -> None:
        if not self.active_sagas:
            return

        # The handler requires the simulation state to access various services.
        # This is a known dependency smell (God object), but fixing it is
        # out of scope for this refactor.
        handler = HousingTransactionSagaHandler(self._sim)

        for saga_id, saga in list(self.active_sagas.items()):
            # ... identical logic from SettlementSystem.process_sagas ...
            # ... including agent liveness checks, exception handling, and cleanup ...
            updated_saga = handler.execute_step(saga)
            self.active_sagas[saga_id] = updated_saga
            if updated_saga['status'] in ["COMPLETED", "FAILED_ROLLED_BACK"]:
                del self.active_sagas[saga_id]

    # ... implementation for submit_saga, find_and_compensate_by_agent ...
```

## 4. Verification Plan
1.  **Unit Tests**:
    -   `TestSettlementSystem`: Verify that all saga-related methods are gone and that `transfer` still works. Tests for `_execute_withdrawal` should be updated to use agents that conform to `IFinancialEntity` and mock the adapter.
    -   `TestSagaOrchestrator`: New test suite to verify saga submission, processing of terminal states (COMPLETED, FAILED), and compensation triggering.
    -   `TestMonetaryLedger`: New test suite to verify that `record_credit_expansion` creates the correct `Transaction` object and appends it to the log.
    -   `TestHousingTransactionSagaHandler`: Update tests to mock `IMonetaryLedger` and verify it's called instead of `transactions.append`.
2.  **Integration Tests**:
    -   The existing `stress_test_validation` which tracks housing market sagas tick-by-tick will be the primary validation mechanism. The final state and transaction logs must be identical post-refactor, with the only difference being the `transaction_type` or `memo` of the monetary policy logs.

## 5. Mocking Guide
-   All new tests MUST use dependency injection and mock the new interfaces (`ISagaOrchestrator`, `IMonetaryLedger`).
-   Tests for components that depend on `SettlementSystem` will continue to mock `ISettlementSystem` as before.
-   The `golden_households` and `golden_firms` fixtures will be used to test the `FinancialEntityAdapter` to ensure it works with both legacy and modern agent structures.

## 6. Risk & Impact Audit

-   **Risk**: **Monetary Policy Logging (`TD-258`)**. The initial plan to reuse `create_and_transfer` was flawed and would have broken zero-sum accounting.
    -   **Mitigation**: This spec introduces the `IMonetaryLedger` interface, which correctly isolates the act of *observing and logging* credit expansion from the act of *minting* currency. This resolves the architectural conflict.
-   **Risk**: **Circular Dependencies**. Moving `process_sagas` but leaving `find_and_compensate_by_agent` in `SettlementSystem` would create a dependency loop.
    -   **Mitigation**: This spec mandates moving **all** saga-related state and logic (`active_sagas`, `process_sagas`, `submit_saga`, `find_and_compensate_by_agent`) into the `SagaOrchestrator`, ensuring `SettlementSystem` is fully decoupled and ignorant of sagas.
-   **Risk**: **Abstraction Leaks (`TD-254`)**. Immediately enforcing `IFinancialEntity` would break legacy agents.
    -   **Mitigation**: This spec explicitly prescribes the use of a `FinancialEntityAdapter` as an interim step. This contains the `hasattr` logic, allowing `SettlementSystem` to be cleaned while providing a backward-compatible path for older components. This bounds the technical debt and makes future refactoring of agents manageable.
-   **Risk**: **God Class Proliferation**. The new `SagaOrchestrator` could inherit the high coupling of its predecessor.
    -   **Mitigation**: While the orchestrator will initially be passed the full `simulation` object to maintain compatibility with `HousingTransactionSagaHandler`, this spec acknowledges it as a remaining debt. The defined `ISagaOrchestrator` interface is minimal, paving the way for future refactoring where specific services (`ISettlementSystem`, `IPropertyRegistry`, etc.) are injected directly into handlers.

## 7. Mandatory Reporting Verification
-   Insights, design choices, and identified sub-debts from this refactoring process will be logged in `communications/insights/TD-253_Settlement_Refactor.md`. This ensures knowledge capture and informs future architectural decisions.
```

```python
# new file: modules/finance/kernel/api.py
from typing import Protocol, Dict, Any, List, Tuple
from uuid import UUID

from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO, IHousingTransactionSagaHandler
from modules.system.api import CurrencyCode
from simulation.finance.api import ITransaction, IFinancialEntity

# DTOs and other necessary imports would go here

# --- 1. Saga Orchestration ---

class ISagaOrchestrator(Protocol):
    """
    Manages the lifecycle of long-running, multi-step business transactions (Sagas).
    This service is the single source of truth for saga state.
    """

    def submit_saga(self, saga: HousingTransactionSagaStateDTO) -> bool:
        """Submits a new saga to be processed."""
        ...

    def process_sagas(self) -> None:
        """
        Iterates through all active sagas and executes their next step.
        This is the main entry point called by the simulation's tick orchestrator.
        """
        ...

    def find_and_compensate_by_agent(self, agent_id: int, handler: IHousingTransactionSagaHandler) -> None:
        """
        Finds all sagas involving a specific agent and triggers their compensation/rollback.
        Used for cleanup when an agent is removed from the simulation (e.g., death).
        """
        ...

    def get_active_sagas(self) -> Dict[UUID, HousingTransactionSagaStateDTO]:
        """Returns a view of the currently active sagas."""
        ...


# --- 2. Monetary Policy Ledger ---

class IMonetaryLedger(Protocol):
    """
    An observational service that records events impacting the money supply (M2)
    which are not direct mint/burn actions by the Central Bank.
    e.g., fractional reserve banking via mortgage disbursal.
    """

    def record_credit_expansion(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None:
        """
        Records that new credit has been extended, increasing the money supply.
        This creates an observational Transaction record, it does not move funds.
        """
        ...

    def record_credit_destruction(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None:
        """
        Records that credit has been paid back or rolled back, decreasing the money supply.
        This creates an observational Transaction record.
        """
        ...


# --- 3. Refactored Settlement System ---

class ISettlementSystem(Protocol):
    """
    The transactional kernel for all financial operations. It is stateless regarding
    high-level business processes like Sagas. Its sole focus is on the atomic
    execution of fund transfers.
    """

    # --- Core Transfer APIs (Unchanged) ---
    def transfer(
        self,
        debit_agent: IFinancialEntity,
        credit_agent: IFinancialEntity,
        amount: float,
        memo: str,
        tick: int,
        currency: CurrencyCode = ...,
    ) -> ITransaction | None: ...

    def settle_atomic(
        self,
        debit_agent: IFinancialEntity,
        credits_list: List[Tuple[IFinancialEntity, float, str]],
        tick: int,
    ) -> bool: ...

    def execute_multiparty_settlement(
        self,
        transfers: List[Tuple[IFinancialEntity, IFinancialEntity, float]],
        tick: int,
    ) -> bool: ...

    # --- Mint/Burn APIs (Unchanged) ---
    def create_and_transfer(
        self,
        source_authority: IFinancialEntity,
        destination: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int,
        currency: CurrencyCode = ...,
    ) -> ITransaction | None: ...

    def transfer_and_destroy(
        self,
        source: IFinancialEntity,
        sink_authority: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int,
        currency: CurrencyCode = ...,
    ) -> ITransaction | None: ...

    # --- Other Settlement Logic (Unchanged) ---
    def record_liquidation(self, ...) -> None: ...
    def create_settlement(self, ...) -> Any: ...
    def execute_settlement(self, ...) -> List[ITransaction]: ...
    def verify_and_close(self, ...) -> bool: ...

    # ... other methods remain ...

    # --- REMOVED METHODS ---
    # def submit_saga(...)
    # def process_sagas(...)
    # def find_and_compensate_by_agent(...)

```
