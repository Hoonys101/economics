# Spec: Housing Transaction Handler

## 1. Overview

This document specifies the design for the `HousingTransactionHandler`, a specialized transaction handler responsible for processing real estate sales. This component is critical to fixing the "Mortgage System Bypass" (WO-HousingRefactor) identified in the Handover Report.

The handler will orchestrate an atomic, multi-step transaction involving a buyer, a seller, and the banking system to ensure that a housing unit sale correctly includes a down payment, the creation of a mortgage, and the final settlement of funds. It will follow the established saga pattern seen in the `TransactionManager` for `goods` to ensure zero-sum integrity and system stability.

## 2. Module & File Location

- **Spec:** `design/3_work_artifacts/specs/housing_transaction_handler_spec.md`
- **API Definition:** `modules/market/api.py`
- **Implementation:** `modules/market/handlers/housing_transaction_handler.py`
- **Configuration:** `config/economy_params.yaml` (new `housing` section)

## 3. Interface Specification (`api.py`)

The public contract will be defined in `modules/market/api.py`.

```python
# modules/market/api.py
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol, TypedDict

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.models import Transaction
    from simulation.core_agents import Household

# --- Data Transfer Objects (DTOs) ---

class HousingConfigDTO(TypedDict):
    """Configuration parameters for housing market transactions."""
    max_ltv_ratio: float
    mortgage_term_ticks: int
    # Note: Interest rate is handled by the banking/lending system config

# --- Interfaces ---

class ISpecializedTransactionHandler(Protocol):
    """
    Interface for handlers that manage specific, complex transaction types.
    This is a pre-existing interface that we will implement.
    """
    def handle(
        self,
        tx: Transaction,
        buyer: Household,
        seller: "Agent", # Can be Household or Firm
        state: SimulationState
    ) -> bool:
        """
        Executes the specialized transaction logic.
        Returns True on success, False on failure.
        """
        ...

class IHousingTransactionHandler(ISpecializedTransactionHandler, Protocol):
    """Explicit protocol for the housing transaction handler."""
    ...

```

## 4. Detailed Design: `HousingTransactionHandler`

The handler will be a stateless class implementing the `IHousingTransactionHandler` interface.

### 4.1. Pseudo-code for `handle()` method

```python
# In HousingTransactionHandler.handle(tx, buyer, seller, state)

# 1. Initialization & Validation
# --------------------------------------------------
get settlement_system from state.settlement_system
get bank from state.bank
get escrow_agent from state.escrow_agent
get config from state.config.housing # New HousingConfigDTO
get real_estate_units from state.real_estate_units

# Validate transaction data
parse unit_id from tx.item_id (e.g., "unit_123" -> 123)
get unit from real_estate_units using unit_id
if not buyer or not seller or not unit:
    log_error("Invalid participants or unit for housing transaction.")
    return False

# 2. Financial Calculation
# --------------------------------------------------
sale_price = tx.price
max_loan_amount = sale_price * config.max_ltv_ratio
down_payment = sale_price - max_loan_amount

if buyer.assets < down_payment:
    log_info(f"Buyer {buyer.id} has insufficient funds for down payment.")
    return False

# 3. Atomic Settlement Saga
# --------------------------------------------------
# Step A: Secure Buyer's Down Payment in Escrow
memo_down_payment = f"escrow_hold:down_payment:{tx.item_id}"
is_down_payment_secured = settlement_system.transfer(
    buyer, escrow_agent, down_payment, memo_down_payment
)

if not is_down_payment_secured:
    log_warning("Failed to secure down payment in escrow.")
    return False

# --- From here on, failures require compensation/reversal ---

# Step B: Create Mortgage with Bank
memo_loan_creation = f"mortgage_application:{tx.item_id}"
new_loan = bank.create_loan(
    borrower_id=buyer.id,
    principal=max_loan_amount,
    term=config.mortgage_term_ticks,
    memo=memo_loan_creation
)

if not new_loan:
    log_warning("Bank rejected mortgage application.")
    # COMPENSATE: Return down payment to buyer
    settlement_system.transfer(
        escrow_agent, buyer, down_payment, "escrow_reversal:loan_rejected"
    )
    return False

# Step C: Disburse Loan Principal to Escrow
memo_loan_disbursement = f"escrow_hold:loan_disbursement:{tx.item_id}"
is_loan_disbursed = settlement_system.transfer(
    bank, escrow_agent, max_loan_amount, memo_loan_disbursement
)

if not is_loan_disbursed:
    log_critical("Failed to disburse loan from bank to escrow.")
    # COMPENSATE: Cancel the newly created loan and return down payment
    bank.cancel_loan(new_loan.id)
    settlement_system.transfer(
        escrow_agent, buyer, down_payment, "escrow_reversal:disbursement_failed"
    )
    return False

# Step D: Pay Seller the Full Sale Price from Escrow
memo_final_settlement = f"final_settlement:{tx.item_id}"
is_seller_paid = settlement_system.transfer(
    escrow_agent, seller, sale_price, memo_final_settlement
)

if not is_seller_paid:
    log_critical("CRITICAL: Failed to pay seller from escrow. Funds are stuck!")
    # COMPENSATE: This is a critical failure. Revert everything possible.
    # 1. Revert loan disbursement from escrow back to bank
    settlement_system.transfer(
        escrow_agent, bank, max_loan_amount, "reversal:seller_payment_failed"
    )
    # 2. Cancel the loan
    bank.cancel_loan(new_loan.id)
    # 3. Return down payment to buyer
    settlement_system.transfer(
        escrow_agent, buyer, down_payment, "reversal:seller_payment_failed"
    )
    return False

# 4. Success
# --------------------------------------------------
# The TransactionManager will handle calling registry.update_ownership,
# which needs to be aware of the 'housing' transaction type to:
# - Set unit.owner_id = buyer.id
# - Set unit.mortgage_id = new_loan.id
# - Move unit from seller.properties to buyer.properties
log_info("Housing transaction successful.")
return True
```

## 5. Exception Handling

- **Insufficient Funds:** The transaction is cleanly aborted before any transfers if the buyer cannot afford the down payment.
- **Loan Rejection:** The down payment held in escrow is immediately and atomically returned to the buyer.
- **Disbursement/Settlement Failure:** The saga includes compensating transactions (reversals) to unwind the process and return all parties to their original state, preventing money leaks. A critical log is emitted if funds cannot be returned from escrow.

## 6. Verification Plan

1.  **Unit Tests:** Create `tests/market/test_housing_transaction_handler.py`.
    - Mock `SettlementSystem`, `Bank`, and `SimulationState`.
    - **Test Case 1 (Success):** Verify that with sufficient funds and a successful loan application, all `settlement.transfer` calls are made correctly and the handler returns `True`.
    - **Test Case 2 (Fail - Down Payment):** Verify that if `buyer.assets < down_payment`, the handler returns `False` and no transfers are attempted.
    - **Test Case 3 (Fail - Loan Rejected):** Mock `bank.create_loan` to return `None`. Verify the down payment is reversed from escrow to the buyer and the handler returns `False`.
    - **Test Case 4 (Fail - Seller Payment):** Mock the final `settlement.transfer` to the seller to return `False`. Verify all compensating transfers are called to revert the loan and down payment.

2.  **Integration Tests:**
    - Update `tests/systems/test_transaction_manager.py` to include a test where a 'housing' transaction is processed.
    - This requires registering a mock `HousingTransactionHandler` with the `TransactionManager` during test setup.

3.  **End-to-End Verification:**
    - Run the `trace_leak.py` script after implementation to ensure zero-sum integrity is maintained.
    - Run a small-scale simulation to confirm a household can successfully buy a house, a mortgage appears in the bank's ledger, and the seller's and buyer's assets change correctly.

## 7. Mocking Guide

- **Use Existing Fixtures:** Leverage `golden_households` and `golden_firms` from `tests/conftest.py` for buyers and sellers.
- **No `MagicMock`:** Do not manually create mocks for agents.
- **New Fixtures:** A new fixture, `golden_real_estate_units`, may be required in `conftest.py` to provide testable housing units.
- **Dependency Mocks:** Standard `pytest-mock` `mocker` can be used for `Bank`, `SettlementSystem`, and `SimulationState` dependencies within unit tests.

## 8. 🚨 Risk & Impact Audit (Addressing Pre-flight Concerns)

- **Missing "Orphaned" Logic:** **Acknowledged.** This spec implements the required logic from scratch as it was not present in the provided code.
- **Dependency Management:** **Addressed.** The handler is designed to be stateless and receives all dependencies via the `SimulationState` object passed to `handle()`, adhering to `TDL-029`.
- **Single Responsibility Principle:** **Addressed.** The logic is encapsulated in the new `HousingTransactionHandler`, separate from `HousingSystem`. This handler must be registered with the `TransactionManager` during simulation setup.
- **Zero-Sum Integrity:** **Addressed.** The design mandates the use of `SettlementSystem` for all monetary transfers and incorporates a saga pattern with compensating transactions to prevent money leaks, in line with the passing `trace_leak.py` requirement.
- **Configuration Management:** **Addressed.** The design specifies a new `HousingConfigDTO` and assumes parameters like `max_ltv_ratio` will be loaded from the unified config system, avoiding magic numbers as per `TD-166`.
- **Schema Change Notice**: A new `Loan` object will be created and associated with a `RealEstateUnit`. The `RealEstateUnit` model must have a `mortgage_id: Optional[int]` field. The `Registry` must be updated to handle this state change upon a successful `housing` transaction.
