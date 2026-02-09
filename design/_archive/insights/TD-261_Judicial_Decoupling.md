# TD-261 Judicial System Decoupling: Technical Insights

## 1. Problem Phenomenon
The `Bank` service (`simulation/bank.py`) was exhibiting tight coupling between financial logic and governance/penal consequences. Specifically, the `_handle_default` method was responsible for both:
1.  **Financial Accounting**: Writing off the loan (Credit Destruction).
2.  **Punitive Measures**: Applying XP penalties, freezing credit, and seizing assets/shares.

This violated the "Separation of Concerns" principle and made the `Bank` difficult to test and maintain. It also created a circular dependency risk if the Bank needed to know about governance concepts (like XP) which might eventually depend on the Bank.

## 2. Root Cause Analysis
-   **Monolithic Design**: Early simulation design centralized "consequence management" in the entity that triggered the event (the Bank), rather than delegating it.
-   **Lack of Event Infrastructure**: There was no mechanism to broadcast `LoanDefaulted` events to other interested parties.
-   **Legacy Tests**: Unit tests (`tests/unit/test_bank.py`) were tightly coupled to the internal implementation of `Bank`, accessing private attributes like `loans` (which didn't strictly exist on the class anymore due to delegation to `LoanManager`) and asserting side effects directly.

## 3. Solution Implementation Details
We introduced an Event-Driven Architecture to decouple these concerns.

### 3.1. Infrastructure
-   **EventBus**: Created `modules/system/event_bus/` to handle synchronous event publication and subscription.
-   **DTOs**: Defined `LoanDefaultedEvent` in `modules/events/dtos.py` to carry context (agent ID, amount, loan ID) without passing heavy objects.

### 3.2. Judicial System
-   **New Component**: Created `JudicialSystem` (`modules/governance/judicial/`), implementing `IJudicialSystem`.
-   **Responsibility**: It subscribes to `LOAN_DEFAULTED`. Upon receiving the event, it:
    1.  Applies XP Penalty (via `IEducated` protocol).
    2.  Freezes Credit (via `ICreditFrozen` protocol).
    3.  Seizes Shares (via `IShareholderRegistry` and `IPortfolioHandler`).
    4.  Executes Asset Seizure (via `ISettlementSystem` transfer from debtor to creditor).

### 3.3. Bank Refactoring
-   **Event Emission**: `Bank._handle_default` now constructs and emits a `LoanDefaultedEvent` via the injected `EventBus`.
-   **Pure Financial Logic**: The Bank retains responsibility for "Credit Destruction" (writing off the bad debt from the money supply) as this is a core monetary function. It delegates all punitive and recovery actions to the Judicial System.

### 3.4. Test Updates
-   **Fixed Legacy Tests**: `tests/unit/test_bank.py` was updated to mock the `EventBus` and verify event emission instead of checking for side effects on agent state.
-   **New Verification**: Added `tests/unit/governance/test_judicial_system.py` to verify the penalty logic in isolation.
-   **Audit Script**: Created `audits/audit_consequences.py` to simulate a full default cycle and verify that the system correctly applies penalties when an event is published.

## 4. Lessons Learned & Technical Debt
-   **Test Fragility**: The existing `test_bank.py` was accessing attributes that didn't exist (`bank.loans`), likely passing due to some dynamic mocking or legacy environment state in previous runs. Strict dependency injection and mocking `LoanManager` state proved more robust.
-   **Protocol Runtime Checks**: We relied on `@runtime_checkable` protocols (`IFinancialEntity`, `IPortfolioHandler`). Ensuring mocks in tests satisfy these checks (via inheritance or correct attribute structure) is critical.
-   **Asset Seizure Complexity**: Asset seizure logic has edge cases (e.g., partial seizure). The current implementation seizes *all* liquid assets up to the default amount (or total assets if less). This matches the original behavior but could be refined in future Governance iterations.
