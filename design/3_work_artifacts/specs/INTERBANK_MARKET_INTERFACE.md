# Design Spec: Interbank Market Protocol

**Mission Key**: `phase32_interbank_market`
**Document Status**: `DRAFT`

## 1. Overview & Purpose

This document outlines the architecture and API for the `InterbankMarket`, a new system for Phase 32. Its purpose is to facilitate short-term, overnight lending between `Bank` entities. This system is critical for allowing banks to manage their liquidity and meet reserve requirements, creating a more dynamic and realistic financial system.

The `InterbankMarket` will operate as a centralized coordinator, strictly adhering to the project's established "Sacred Sequence" of atomic, zero-sum transactions. All fund movements will be orchestrated by this module and executed exclusively through the `SettlementSystem`.

## 2. Architecture & Principles

The `InterbankMarket` is designed as a standalone system that **coordinates**, but is not part of, individual `Bank` instances. This avoids overloading the `Bank` class and respects the Single Responsibility Principle.

### 2.1. Core Architectural Principles
- **`SettlementSystem` Supremacy**: All transfers of funds (loan principal, interest payments) **must** be delegated to the `SettlementSystem`. The market only generates transaction *intents*; it never directly modifies an agent's assets.
- **Settle-then-Record (Two-Phase Commit)**: The state of a loan is only finalized *after* the `SettlementSystem` confirms the successful execution of the underlying financial transfer. This is managed via a `PENDING` -> `ACTIVE` state transition.
- **Decoupling**: The market maintains its own registry of participating banks (as `IFinancialEntity` objects) and does not require access to the global `agents_dict`.
- **Zero-Sum Integrity**: The market is a closed loop. It facilitates transfers between banks but does not interact with minting/burning authorities like the `Government` or `CentralBank`.

### 2.2. High-Level Workflow
1.  **Registration**: `Bank` instances register themselves with the `InterbankMarket` at the start of a simulation.
2.  **Market Operations (per tick)**:
    a. Banks submit `InterbankLoanRequestDTO`s (if they need liquidity) and `InterbankLoanOfferDTO`s (if they have excess reserves).
    b. The `InterbankMarket.process_market()` method matches offers to requests.
    c. For each match, it creates a `InterbankLoanDTO` in a `PENDING` state and returns a `Transaction` intent to the main simulation loop.
3.  **Settlement**: The main loop sends these intents to the `SettlementSystem`.
4.  **State Finalization**: The main loop calls back to the `InterbankMarket` with the settlement results, which then updates the loan statuses from `PENDING` to `ACTIVE` (on success) or `FAILED` (on failure).
5.  **Repayment**: On the due tick, `InterbankMarket.process_repayments()` generates repayment transaction intents, which follow the same settlement and finalization flow.

## 3. API & Interface Specification (`api.py`)

The public interface for the interbank market will be defined in `modules/finance/interbank_market/api.py`.

```python
from typing import TypedDict, List, Optional, Protocol
from modules.finance.api import IFinancialEntity, ITransaction

# --- Data Transfer Objects (DTOs) ---

class InterbankLoanRequestDTO(TypedDict):
    """A request from a bank to borrow funds."""
    borrowing_bank_id: str
    amount: float
    # The maximum annual interest rate the borrower is willing to pay.
    max_rate: float
    request_tick: int

class InterbankLoanOfferDTO(TypedDict):
    """An offer from a bank to lend funds."""
    lending_bank_id: str
    amount: float
    # The minimum annual interest rate the lender is willing to accept.
    min_rate: float
    offer_tick: int

class InterbankLoanDTO(TypedDict):
    """Represents a finalized interbank loan agreement."""
    loan_id: str
    lending_bank_id: str
    borrowing_bank_id: str
    principal: float
    annual_interest_rate: float
    origination_tick: int
    due_tick: int
    # Status MUST follow the Settle-then-Record principle.
    status: str # 'PENDING', 'ACTIVE', 'REPAID', 'DEFAULTED', 'FAILED'
    settlement_tx_id: Optional[str] # Links to the settlement transaction

# --- Service Interface ---

class IInterbankMarket(Protocol):
    """
    Coordinates overnight lending between registered banking institutions.
    """

    def register_bank(self, bank: IFinancialEntity) -> None:
        """Adds a bank to the market's registry."""
        ...

    def submit_loan_request(self, request: InterbankLoanRequestDTO) -> None:
        """Submits a borrowing request for the current tick."""
        ...

    def submit_loan_offer(self, offer: InterbankLoanOfferDTO) -> None:
        """Submits a lending offer for the current tick."""
        ...

    def process_market(self, current_tick: int) -> List[ITransaction]:
        """
        Matches outstanding offers and requests, creates PENDING loans,
        and returns a list of transaction intents for the settlement system.
        """
        ...

    def process_repayments(self, current_tick: int) -> List[ITransaction]:
        """
        Identifies loans due for repayment and returns transaction intents
        for principal + interest.
        """
        ...

    def update_loan_statuses(self, successful_txs: List[ITransaction], failed_txs: List[ITransaction]) -> None:
        """
        Callback from the main simulation loop after settlement.
        Finalizes loan states from PENDING to ACTIVE or FAILED.
        Updates repaid loans to REPAID or DEFAULTED.
        """
        ...
```

## 4. Detailed Design & Logic

### 4.1. Component: `InterbankMarket`

#### Logic: `process_market(current_tick)` (Pseudo-code)
```pseudo
function process_market(current_tick):
  // 1. Setup
  requests = get_and_clear_pending_requests()
  offers = get_and_clear_pending_offers()
  matched_transactions = []

  // 2. Matching Algorithm (Simple Example: sort by rate)
  sort offers by min_rate ascending
  sort requests by max_rate descending

  // 3. Iterate and Match
  for each req in requests:
    for each offer in offers:
      if offer.amount > 0 and req.amount > 0 and offer.min_rate <= req.max_rate:
        // Match found
        match_amount = min(req.amount, offer.amount)
        agreed_rate = (req.max_rate + offer.min_rate) / 2 // Simple midpoint rate

        // Create a pending loan object
        loan = create_interbank_loan_dto(
          lender=offer.lending_bank_id,
          borrower=req.borrowing_bank_id,
          amount=match_amount,
          rate=agreed_rate,
          status='PENDING',
          current_tick=current_tick
        )
        add_loan_to_market_registry(loan)

        // Generate settlement transaction intent
        tx_intent = create_settlement_transaction(
          debit_agent_id=offer.lending_bank_id,
          credit_agent_id=req.borrowing_bank_id,
          amount=match_amount,
          memo=f"Interbank Loan {loan.loan_id} Principal"
        )
        // Link transaction to loan for status update later
        loan.settlement_tx_id = tx_intent.id
        matched_transactions.append(tx_intent)

        // Update amounts for further matching
        req.amount -= match_amount
        offer.amount -= match_amount

  return matched_transactions
```

#### Logic: `update_loan_statuses(...)` (Pseudo-code)
```pseudo
function update_loan_statuses(successful_txs, failed_txs):
  for tx in successful_txs:
    loan = find_loan_by_settlement_tx_id(tx.id)
    if loan is found:
      if loan.status == 'PENDING':
        loan.status = 'ACTIVE'
        log(f"Loan {loan.id} is now ACTIVE.")
      else: // Repayment succeeded
        loan.status = 'REPAID'
        log(f"Loan {loan.id} has been REPAID.")

  for tx in failed_txs:
    loan = find_loan_by_settlement_tx_id(tx.id)
    if loan is found:
      if loan.status == 'PENDING':
        loan.status = 'FAILED'
        log(f"Loan {loan.id} FAILED settlement.")
      else: // Repayment failed
        loan.status = 'DEFAULTED'
        log(f"Loan {loan.id} has DEFAULTED.")
```

### 4.2. Exception Handling
- **Settlement Failure**: Handled gracefully by the `update_loan_statuses` callback. A failed settlement for a `PENDING` loan moves it to `FAILED`, preventing inconsistent state.
- **Repayment Default**: A failed settlement for a repayment moves the loan to `DEFAULTED`. This allows for tracking bank insolvency and systemic risk.

## 5. Verification Plan

- **Test Case 1 (Happy Path)**: A bank requests funds, another offers them, the market matches, `SettlementSystem` succeeds, the loan becomes `ACTIVE`, and is later `REPAID` successfully.
- **Test Case 2 (Settlement Failure)**: Lender makes an offer but has insufficient funds when settlement is attempted. The loan status transitions `PENDING` -> `FAILED`.
- **Test Case 3 (Repayment Default)**: Borrower's loan is due but it has insufficient funds to repay. The loan status transitions to `DEFAULTED`.
- **Test Case 4 (Complex Market)**: Multiple requests and offers with varying rates and amounts are processed, ensuring the matching algorithm correctly prioritizes and fulfills them.
- **Test Case 5 (Partial Fulfillment)**: A large request is partially fulfilled by a smaller offer.

## 6. Mocking Guide
- Tests will require mock `Bank` objects that implement the `IFinancialEntity` protocol (`id`, `assets`, `deposit`, `withdraw`).
- A mock `SettlementSystem` will be essential to simulate both successful and failed transfers, allowing for verification of the `update_loan_statuses` logic.
- **Do not** use `MagicMock`. Create simple dataclasses or stub classes that fulfill the `IFinancialEntity` contract to ensure type safety.

## 7. Risk & Impact Audit

This design explicitly addresses the risks identified in the pre-flight audit.

- **[MITIGATED] SRP Violation**: The `InterbankMarket` is a new, separate module, preventing further bloat in the `Bank` class.
- **[MITIGATED] `SettlementSystem` Supremacy**: All fund movements are exclusively handled by generating transaction intents for the `SettlementSystem`.
- **[MITIGATED] Atomicity & Settle-then-Record**: The `PENDING` -> `ACTIVE`/`FAILED` state transition, driven by a callback after settlement, ensures atomicity and prevents inconsistent states.
- **[MITIGATED] Coupling**: The market is decoupled from global state, interacting only with registered `IFinancialEntity` instances.
- **[ACCEPTED] Increased Orchestration Complexity**: The main simulation loop (`TickScheduler`) must now manage the two-phase commit cycle (generate intents, settle, update state). This is an accepted and necessary trade-off to guarantee financial integrity and architectural correctness.
- **[NEW RISK] Race Conditions**: Submitting requests/offers and processing the market must happen in a clearly defined order within a single tick to prevent race conditions. The `process_market` method should consume all pending requests/offers for that tick in one atomic step.

## 8. Mandatory Reporting
Jules implementing this module must document any discovered technical debt or insights in `communications/insights/phase32_interbank_market.md`. This includes challenges with the `TickScheduler` orchestration, difficulties in mocking, or limitations in the current `IFinancialEntity` interface.
