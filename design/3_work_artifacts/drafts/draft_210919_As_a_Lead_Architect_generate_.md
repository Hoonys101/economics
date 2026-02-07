# Spec: Bank Decomposition and Facade

- **Date**: 2026-02-07
- **Author**: Scribe (Gemini)
- **Related Debt**: TD-274, TD-275, TD-276

## 1. Overview

This document outlines the technical specification for refactoring the monolithic `Bank` class into a Facade. Core responsibilities will be delegated to two new stateful components: `LoanManager` and `DepositManager`. This addresses critical technical debt (TD-274), purifies responsibilities, and introduces formal reserve ratio controls, aligning with the project's architectural principles.

---

## 2. Architectural Decisions & Risk Mitigation

This design explicitly incorporates the findings from the pre-flight audit:

1.  **Pattern Adoption (Stateful Components)**: We will adopt the existing "Stateful Component" pattern for consistency. `LoanManager` and `DepositManager` will be initialized with a reference to the parent `Bank` instance. To manage coupling, this parent reference **MUST** be typed as a new `IBankFacade` interface, exposing only necessary methods (`get_liquid_reserves`, `get_settlement_system`, `get_current_tick`).

2.  **Responsibility Demarcation (Default Penalties)**:
    - `LoanManager`: Responsible for tracking loan health, identifying defaults, and emitting a `LoanDefaultedEvent`. It does **not** apply penalties.
    - `Bank (Facade)`: Acts as an orchestrator. It listens for `LoanDefaultedEvent` and applies the consequential penalties (e.g., updating `credit_frozen_until_tick`), thus isolating financial logic from judicial logic.

3.  **Circular Dependency Prevention**: To prevent runtime import cycles, all components (`LoanManager`, `DepositManager`) **MUST** use `if TYPE_CHECKING:` blocks when defining the type hint for the parent `IBankFacade`.

4.  **Encapsulation & Interaction Protocol**:
    - Direct agent manipulation is **prohibited**.
    - All monetary transfers (repayments, interest) **MUST** be executed via the `ISettlementSystem` interface obtained from the `IBankFacade`.
    - The `payment_callback` function in `run_tick` is **abolished**.

---

## 3. Interface & DTO Definitions (`api.py`)

The following definitions will be added to `modules/finance/api.py`.

```python
# modules/finance/api.py

from typing import Protocol, Dict, Any, List, Optional, Tuple, TypedDict, TYPE_CHECKING
from modules.system.api import CurrencyCode

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem

# --- DTOs & Events ---

class LoanApplicationDTO(TypedDict):
    borrower_id: str
    amount: float
    interest_rate: float
    borrower_profile: Optional['BorrowerProfileDTO']
    # ... other relevant fields

class LoanDefaultedEvent(TypedDict):
    type: str # "default"
    loan_id: str
    borrower_id: int
    amount_defaulted: float

class InterestPaymentEvent(TypedDict):
    type: str # "interest_payment"
    loan_id: str
    borrower_id: int
    amount: float

class LoanRepaymentEvent(TypedDict):
    type: str # "repayment"
    loan_id: str
    borrower_id: int
    amount: float

class DepositInterestEvent(TypedDict):
    depositor_id: int
    amount: float
    currency: CurrencyCode

# --- Facade Interface (for Components) ---

class IBankFacade(Protocol):
    """
    Interface exposing Bank services to its internal components,
    preventing circular dependencies and uncontrolled state access.
    """
    @property
    def id(self) -> int: ...

    def get_liquid_reserves(self, currency: CurrencyCode) -> float: ...
    def get_settlement_system(self) -> Optional['ISettlementSystem']: ...
    def get_current_tick(self) -> int: ...
    def get_base_rate(self) -> float: ...
    def get_config(self, key: str, default: Any) -> Any: ...

# --- Component Interfaces ---

class ILoanManager(Protocol):
    def __init__(self, facade: IBankFacade): ...
    def create_loan(self, borrower_id: int, amount: float, interest_rate: float, start_tick: int, term_ticks: int, created_deposit_id: Optional[str]) -> str: ...
    def repay_loan(self, loan_id: str, amount: float) -> bool: ...
    def get_loan_by_id(self, loan_id: str) -> Optional[Dict]: ...
    def get_loans_for_agent(self, agent_id: int) -> List[Dict]: ...
    def service_loans(self, current_tick: int) -> List[Union[InterestPaymentEvent, LoanDefaultedEvent, LoanRepaymentEvent]]: ...
    def terminate_loan(self, loan_id: str) -> Optional[float]: ...

class IDepositManager(Protocol):
    def __init__(self, facade: IBankFacade): ...
    def create_deposit(self, depositor_id: int, amount: float, rate: float, currency: CurrencyCode) -> str: ...
    def withdraw(self, depositor_id: int, amount: float, currency: CurrencyCode) -> bool: ...
    def get_balance(self, agent_id: int) -> float: ...
    def get_total_deposits(self, currency: CurrencyCode) -> float: ...
    def calculate_interest(self, current_tick: int) -> List[DepositInterestEvent]: ...
    def remove_deposit_match(self, depositor_id: int, amount: float) -> bool: ...

```

---

## 4. Component & Facade Design

### 4.1. `LoanManager` Component

-   **Responsibilities**: Manages the entire lifecycle of loans: creation, servicing (interest calculation, repayment tracking), and default identification.
-   **State**: Holds a collection of all active and defaulted loans.
-   **Pseudo-code (`service_loans`)**:

    ```python
    # In LoanManager
    def service_loans(self, current_tick: int) -> List[Event]:
        events = []
        settlement_system = self.facade.get_settlement_system()

        for loan in self.active_loans:
            if loan.is_due_for_interest(current_tick):
                interest_due = loan.calculate_interest()

                if not settlement_system:
                    # Log critical failure if no settlement system
                    continue

                # Request transfer via settlement system
                tx_successful = settlement_system.transfer(
                    from_agent_id=loan.borrower_id,
                    to_agent_id=self.facade.id,
                    amount=interest_due,
                    memo=f"Loan Interest {loan.id}"
                )

                if tx_successful:
                    loan.record_interest_payment(interest_due)
                    events.append(InterestPaymentEvent(...))
                else:
                    loan.record_failed_payment()
                    if loan.is_in_default():
                        default_amount = loan.get_outstanding_balance()
                        self.move_to_defaulted(loan)
                        events.append(LoanDefaultedEvent(
                            borrower_id=loan.borrower_id,
                            amount_defaulted=default_amount
                        ))
        return events
    ```

### 4.2. `DepositManager` Component

-   **Responsibilities**: Manages all customer deposits, including creation, balance tracking, and interest calculation. Enforces reserve requirements.
-   **State**: Holds a collection of all deposit accounts.
-   **Pseudo-code (`can_support_new_credit`)**: This method is key for reserve control.

    ```python
    # In DepositManager
    def get_total_deposits(self, currency: CurrencyCode) -> float:
        # Sum of all balances in the specified currency
        return sum(d.balance for d in self.deposits if d.currency == currency)

    # In Bank (Facade), orchestrating the check
    def grant_loan(self, ...):
        # 1. Credit Assessment (as before)

        # 2. Reserve Check (Orchestrated by Facade)
        reserve_ratio = self.get_config("reserve_req_ratio", 0.1)
        total_deposits = self.deposit_manager.get_total_deposits(DEFAULT_CURRENCY)
        liquid_reserves = self.wallet.get_balance(DEFAULT_CURRENCY)

        # The bank must have enough reserves to cover the required fraction of its liabilities (deposits)
        # AFTER creating the new loan/deposit.
        if liquid_reserves < (total_deposits + amount) * reserve_ratio:
            logger.info(f"LOAN_DENIED | Insufficient reserves to create {amount} credit.")
            return None

        # 3. Create Deposit & Loan (delegating to managers)
        deposit_id = self.deposit_manager.create_deposit(...)
        loan_id = self.loan_manager.create_loan(...)
        # ...
    ```

### 4.3. `Bank` Facade

-   **Responsibilities**:
    -   Acts as the single public entry point for banking services.
    -   Initializes and holds `LoanManager` and `DepositManager`.
    -   Implements `IBankFacade` for its components.
    -   Orchestrates complex workflows in `run_tick` by reacting to events from managers.
    -   Handles default penalties and other cross-cutting concerns.
-   **Pseudo-code (`run_tick`)**:

    ```python
    # In Bank class
    def run_tick(self, agents_dict: Dict, current_tick: int):
        self.current_tick_tracker = current_tick
        generated_transactions = []

        # --- 1. Service Loans (Delegate and React) ---
        loan_events = self.loan_manager.service_loans(current_tick)
        for event in loan_events:
            if event['type'] == 'interest_payment':
                # Create transaction for reporting
                generated_transactions.append(Transaction(...))
                # Update bank's internal profit tracking
                self.net_profit_this_tick += event['amount']

            elif event['type'] == 'default':
                # Create credit destruction transaction for reporting
                generated_transactions.append(Transaction(...))

                # !! PENALTY LOGIC REMAINS IN FACADE !!
                agent = agents_dict.get(event['borrower_id'])
                if agent:
                    # Apply penalties (e.g., freeze credit, reduce XP)
                    self.apply_default_penalties(agent, event)
                    # Attempt to recover assets (delegating seizure to SettlementSystem)
                    recovery_tx = self.recover_assets_on_default(agent, event)
                    if recovery_tx:
                        generated_transactions.append(recovery_tx)

        # --- 2. Pay Deposit Interest (Delegate and React) ---
        deposit_interest_events = self.deposit_manager.calculate_interest(current_tick)
        for event in deposit_interest_events:
            agent = agents_dict.get(event['depositor_id'])
            if agent:
                # Use settlement system to pay interest
                tx_successful = self.settlement_system.transfer(self, agent, event['amount'], "Deposit Interest")
                if tx_successful:
                    # Create transaction for reporting
                    generated_transactions.append(Transaction(...))
                    self.net_profit_this_tick -= event['amount']

        # --- 3. Profit Remittance (as before) ---
        # ...

        return generated_transactions
    ```

---

## 5. Verification Plan

1.  **Unit Tests**:
    -   `LoanManager`: Test `service_loans` by providing a mock `IBankFacade` and `ISettlementSystem`. Verify that correct events are emitted for successful and failed payments.
    -   `DepositManager`: Test `calculate_interest` and `get_total_deposits`.
2.  **Integration Tests**:
    -   Test the `Bank` facade's `grant_loan` method to ensure the reserve ratio check is correctly orchestrated between the facade and the `DepositManager`.
    -   Test the full `run_tick` cycle, using `golden_households` and `golden_firms` fixtures, to verify that events from managers are correctly handled and lead to the expected state changes and transactions.
3.  **Golden Data**: Existing fixtures (`golden_households`, `golden_firms`) will be used as the basis for integration tests to ensure behavior remains consistent.

---

## 6. Risk & Impact Audit

-   **Risk**: Tight coupling between components and the facade.
    -   **Mitigation**: Strict enforcement of the `IBankFacade` interface. Code reviews must reject any direct access to the parent's internal state.
-   **Risk**: Logic errors in the new orchestration layer (`Bank.run_tick`).
    -   **Mitigation**: Extensive integration testing covering all event types (`default`, `interest_payment`, etc.) to ensure the facade reacts correctly.
-   **Impact**: High. This is a core refactoring of the economic engine. It will touch `Bank`, `Government` (profit remittance), and all agent interaction points with the bank. The `ISettlementSystem` becomes even more critical.

---

## 7. Mandatory Reporting Verification

-   An insight report summarizing the architectural decisions and risk mitigations for this decomposition has been created at `communications/insights/TD-274_Decomposition.md`. This is a hard requirement for proceeding with implementation.
