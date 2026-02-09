# Design Document: TD-261 Judicial System Decoupling

## 1. Introduction

- **Purpose**: This document outlines the design for refactoring the `Bank` service to resolve technical debt **TD-261**. The core objective is to separate pure financial logic from governance-related consequences (e.g., XP penalties, reputation loss) by introducing a new `JudicialSystem`.
- **Scope**: This refactoring impacts the `Bank` service, introduces a new `JudicialSystem` and an `EventBus`, and requires modifications to existing tests that rely on the coupled behavior.
- **Goals**:
    - Achieve "Interface Purity" for all financial services.
    - Decouple the `finance` domain from the `governance` domain.
    - Establish a robust, event-driven architecture for handling cross-domain side effects.
    - Prevent circular dependencies.
    - Ensure transactional integrity through a reconciliation mechanism.

## 2. System Architecture (High-Level)

The current monolithic behavior will be replaced by an event-driven, decoupled architecture.

**Current State (Problem):**
```
[Agent] -> [BankService.record_default()] -> (Records financial default AND applies XP penalty directly)
```

**Proposed State (Solution):**
```
                                        +----------------+
                                        |    EventBus    |
                                        +-------+--------+
                                                | 3. Listens for Event
+---------------------+      +----------------+ | +------------------+
| BankService         |----->| LoanDefaulted  | | | JudicialSystem   |
| (Financial Logic)   |  2.  | Event (DTO)    |---> | (Governance Logic) |
+---------------------+ Emits|                |   +------------------+
          ^           |      +----------------+             | 4. Applies Penalty
          | 1. Record |                                     | 5. Seizes Assets (optional)
          |    Default|                                     |
+---------------------+                                     v
| Agent               | <-----------------------+  [FinancialSystem Interface]
+---------------------+
```

1.  An `Agent`'s action causes a financial event (e.g., loan default) within the `BankService`.
2.  The `BankService` records the financial state change and **emits a detailed `LoanDefaultedEvent` DTO** to a central `EventBus`. Its responsibility ends here.
3.  The `JudicialSystem`, a subscriber to the `EventBus`, receives the event.
4.  The `JudicialSystem` processes the event and applies the appropriate non-financial consequence (e.g., XP penalty).
5.  If financial action is required (e.g., asset seizure), the `JudicialSystem` issues a command through a generic `IFinancialSystem` interface, avoiding a direct dependency on the `BankService`.

---

## 3. Detailed Design

### 3.1. DTOs: Event Contracts

New event DTOs will be defined, likely in `modules/events/dtos.py`.

```python
# modules/events/dtos.py

from typing import TypedDict, Literal

class LoanDefaultedEvent(TypedDict):
    event_type: Literal["LOAN_DEFAULTED"]
    tick: int
    agent_id: int
    loan_id: str
    defaulted_amount: float

class InsolvencyDeclaredEvent(TypedDict):
    event_type: Literal["INSOLVENCY_DECLARED"]
    tick: int
    agent_id: int
    total_debt: float
    total_assets: float

# A union type for all financial events
FinancialEvent = LoanDefaultedEvent | InsolvencyDeclaredEvent
```

### 3.2. Interfaces (`api.py`)

#### a) Event Bus (`modules/system/event_bus/api.py`)

```python
# modules/system/event_bus/api.py

from typing import Protocol, Callable, List
from modules.events.dtos import FinancialEvent

# Type for a function that handles an event
EventHandler = Callable[[FinancialEvent], None]

class IEventBus(Protocol):
    """A central mediator for publishing and subscribing to system events."""

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribes a handler to a specific event type."""
        ...

    def publish(self, event: FinancialEvent) -> None:
        """Publishes an event to all subscribed handlers."""
        ...
```

#### b) Purified Bank Interface (`modules/finance/bank/api.py`)

The `IBank` interface will be cleansed of any consequence-related logic.

```python
# modules/finance/bank/api.py
# (Assuming other DTOs like LoanDTO are defined elsewhere)

from typing import Protocol
# ... other imports

class IBank(Protocol):
    """Purely financial operations for a commercial bank."""

    def record_default(self, loan_id: str) -> None:
        """
        Records a loan as defaulted.
        This action MUST emit a LoanDefaultedEvent.
        It MUST NOT apply any penalties directly.
        """
        ...

    def declare_insolvency(self, agent_id: int) -> None:
        """
        Declares an agent as insolvent based on their balance sheet.
        This action MUST emit an InsolvencyDeclaredEvent.
        """
        ...

    # ... other pure financial methods like open_account, issue_loan, etc.
```

#### c) New Judicial System Interface (`modules/governance/judicial/api.py`)

```python
# modules/governance/judicial/api.py

from typing import Protocol
from modules.events.dtos import FinancialEvent
from modules.finance.api import IFinancialSystem

class IJudicialSystem(Protocol):
    """Handles the consequences of events based on simulation rules."""

    def __init__(self, financial_system: IFinancialSystem):
        """
        Injects a generic financial system interface to prevent circular deps.
        """
        ...

    def handle_financial_event(self, event: FinancialEvent) -> None:
        """
        Primary entry point for processing events from the EventBus.
        This method will delegate to specific handlers based on event_type.
        """
        ...

    def apply_default_penalty(self, agent_id: int, defaulted_amount: float) -> None:
        """Applies non-financial penalties for a loan default."""
        ...

    def execute_asset_seizure(self, agent_id: int, amount: float) -> None:
        """Uses the injected financial_system to seize assets."""
        ...
```

### 3.3. Pseudo-code Logic

**BankService Implementation Snippet:**

```python
# In a class implementing IBank (e.g., BankService)
# self.event_bus: IEventBus is injected

def record_default(self, loan_id: str) -> None:
    # 1. Perform internal financial accounting for the default
    loan = self.loans.get(loan_id)
    # ... logic to mark loan as defaulted, update ledgers ...
    defaulted_amount = loan.principal_due

    # 2. Create and publish the event
    event = LoanDefaultedEvent(
        event_type="LOAN_DEFAULTED",
        tick=self.simulation_tick,
        agent_id=loan.borrower_id,
        loan_id=loan_id,
        defaulted_amount=defaulted_amount
    )
    self.event_bus.publish(event)

    # NO MORE PENALTY LOGIC HERE
```

**JudicialSystem Implementation Snippet:**

```python
# In a class implementing IJudicialSystem
# self.financial_system: IFinancialSystem is injected

def handle_financial_event(self, event: FinancialEvent) -> None:
    if event['event_type'] == 'LOAN_DEFAULTED':
        # Delegate to specific handler
        self.apply_default_penalty(
            agent_id=event['agent_id'],
            defaulted_amount=event['defaulted_amount']
        )
    elif event['event_type'] == 'INSOLVENCY_DECLARED':
        # ... handle insolvency, potentially triggering asset seizure
        self.execute_asset_seizure(
            agent_id=event['agent_id'],
            amount=... # Calculate seizure amount
        )

def apply_default_penalty(self, agent_id: int, defaulted_amount: float) -> None:
    # Logic to apply XP penalty, reputation loss, etc.
    reputation_manager.decrease_rep(agent_id, amount=defaulted_amount * 0.1)
    # ...

def execute_asset_seizure(self, agent_id: int, amount: float) -> None:
    # Use the generic interface to command a financial action
    source_agent_wallet = self.wallet_provider.get_wallet(agent_id)
    treasury_wallet = self.wallet_provider.get_wallet(ID_GOVERNMENT)

    self.financial_system.transfer(
        debit_agent=source_agent_wallet,
        credit_agent=treasury_wallet,
        amount=amount,
        memo=f"ASSET_SEIZURE:{agent_id}"
    )
```

## 4. Technical Considerations & Risk Mitigation

This section directly addresses the findings of the pre-flight audit.

-   **Technology Stack**: Python, introducing a simple pub-sub `EventBus` implementation.
-   **Performance**: The `EventBus` will be synchronous for simplicity. Performance impact is negligible for the current scale.
-   **Security**: N/A.
-   **Error Handling**: Event handlers must be robust. An unhandled exception in a handler should be logged but not crash the main simulation loop.

### 4.1. Risk: Circular Dependency

-   **Mitigation**: This is solved by the proposed architecture.
    1.  The `BankService` depends on `IEventBus`, not `IJudicialSystem`.
    2.  The `JudicialSystem` depends on `IEventBus` and the generic `IFinancialSystem`. It has no knowledge of the concrete `BankService`.
    - This unidirectional flow (`Bank` -> `Bus` <- `Judicial`) prevents import cycles.

### 4.2. Risk: Transactional Integrity

-   **Mitigation**: A full Saga pattern or persistent queue is overkill. We will implement an **End-of-Tick Reconciliation Audit**.
    -   A new script, `audits/audit_consequences.py`, will be created.
    -   It will run after each simulation tick (or as a post-run analysis).
    -   It will query the event log and the state of all agents to ensure that for every `LoanDefaultedEvent` logged, a corresponding penalty (e.g., XP reduction) has been applied.
    -   Discrepancies will be logged as critical errors, ensuring simulation rule violations do not go unnoticed.

### 4.3. Risk: Test Fragility and Refactoring

-   **Mitigation**: A phased testing strategy is required.
    1.  **Unit Tests**:
        -   Modify `BankService` tests. Instead of asserting a penalty was applied, they will now assert that `event_bus.publish()` was called with the correct `LoanDefaultedEvent` DTO. A mock `EventBus` will be injected for this.
        -   Create new unit tests for `JudicialSystem`. These tests will pass mock `FinancialEvent` DTOs to `handle_financial_event` and assert that the correct penalties are calculated and that `financial_system.transfer()` is called correctly.
    2.  **Integration Tests**:
        -   Existing integration tests that check for both financial state and consequences in one step will be rewritten.
        -   They will now orchestrate the full flow: trigger the bank action, then inspect the agent's state to confirm the consequence was applied by the `JudicialSystem`. This verifies the event bus wiring.

## 5. Mocking Guide & Verification

- **Golden Data**: No changes are required for existing `golden_households` or `golden_firms` fixtures, as they represent agent state, not service behavior.
- **Test Implementation**:
    - For `BankService` unit tests, a `MagicMock(spec=IEventBus)` is acceptable.
    - For `JudicialSystem` unit tests, `MagicMock(spec=IFinancialSystem)` should be used.
- **Verification Plan**:
    1. Implement the `IEventBus`, `IJudicialSystem`, and related DTOs.
    2. Refactor `BankService` to emit events.
    3. Implement `JudicialSystem` to handle events.
    4. Refactor tests according to the strategy in 4.3.
    5. Create the `audits/audit_consequences.py` script.
    6. Run a full simulation and verify the audit passes with zero discrepancies.

## 6. Mandatory Reporting Verification

- **Insight Logging**: All findings, design trade-offs, and discovered complexities during the implementation of this refactoring will be logged in `communications/insights/TD-261_Judicial_Decoupling.md`. This includes any challenges with the `EventBus` implementation or test refactoring. The creation of this report is a required deliverable for this task.

---
# API Definition: `modules/governance/judicial/api.py`

```python
from typing import Protocol
from modules.events.dtos import FinancialEvent
from modules.finance.api import IFinancialSystem

class IJudicialSystem(Protocol):
    """
    Handles the consequences of events based on simulation rules.
    It subscribes to the EventBus and acts upon financial events
    to enforce governance and legal statutes.
    """

    def __init__(self, financial_system: IFinancialSystem):
        """
        Initializes the JudicialSystem.

        Args:
            financial_system: A generic financial system interface used to
                              execute financial commands (e.g., asset seizure)
                              without creating a circular dependency on the Bank.
        """
        ...

    def handle_financial_event(self, event: FinancialEvent) -> None:
        """
        Primary entry point for processing events from the EventBus.
        This method delegates to specific handlers based on the event's type.
        """
        ...

    def apply_default_penalty(self, agent_id: int, defaulted_amount: float) -> None:
        """
        Applies non-financial penalties for a loan default, such as
        reducing reputation or experience points.
        """
        ...

    def execute_asset_seizure(self, agent_id: int, amount: float) -> None:
        """
        Uses the injected financial_system to seize assets from an agent's
        account and transfer them to a designated entity (e.g., government treasury).
        """
        ...

```
# API Definition: `modules/system/event_bus/api.py`

```python
from typing import Protocol, Callable, List, TypeVar, Generic
from modules.events.dtos import FinancialEvent

# A generic event type
E = TypeVar('E')

# A generic handler for a given event type
EventHandler = Callable[[E], None]

class IEventBus(Protocol, Generic[E]):
    """
    A central mediator for publishing and subscribing to system events.
    This implementation is generic but will be used with FinancialEvent
    in the current context.
    """

    def subscribe(self, event_type: str, handler: EventHandler[E]) -> None:
        """
        Subscribes a handler to a specific event type.

        Args:
            event_type: The identifier for the event (e.g., "LOAN_DEFAULTED").
            handler: The function to be called when the event is published.
        """
        ...

    def publish(self, event: E) -> None:
        """
        Publishes an event to all subscribed handlers.
        The event object is expected to have an 'event_type' attribute
        or be a dictionary with an 'event_type' key.

        Args:
            event: The event object to be broadcast.
        """
        ...

```
