# Technical Specification: Bond Repayment Refactor

## 1. Overview & Goals

This document outlines the technical specification for refactoring the `bond_repayment` process to resolve a critical architectural flaw ("Dueling Ledgers") and to accurately model the distinct economic effects of principal repayment versus interest payment.

- **Goal 1: Single Source of Truth.** Eliminate the "Dueling Ledgers" anti-pattern. The `MonetaryLedger` component will become the sole authority for tracking monetary aggregates (money creation/destruction). The `MonetaryTransactionHandler` will be made stateless regarding these metrics.
- **Goal 2: Accurate Economic Modeling.** Decompose `bond_repayment` transactions to distinguish between `principal` (which is destroyed when paid to the Central Bank) and `interest` (which is transferred, not destroyed).
- **Goal 3: Enhance Data Contracts.** Introduce a structured DTO for bond repayments to create a clear, type-safe data contract, moving away from ambiguous `Transaction` fields.

## 2. Phase 1: Data Model Enhancement (DTO Definition)

The existing `Transaction` model is insufficient. We will introduce a new, explicit Data Transfer Object (DTO) to carry the necessary details.

### 2.1. `BondRepaymentDetailsDTO`

A new `TypedDict` will be defined in `modules/government/api.py` to structure the repayment data.

```python
# In: modules/government/api.py
from typing import TypedDict, Optional

class BondRepaymentDetailsDTO(TypedDict):
    principal: float
    interest: float
    bond_id: str # Reference to the bond being serviced
```

### 2.2. Transaction `metadata` Field

The `Transaction` object's `metadata` field will be used to carry an instance of `BondRepaymentDetailsDTO`. Code that creates `bond_repayment` transactions **MUST** now populate this field.

**Example `Transaction` instance:**

```python
details = BondRepaymentDetailsDTO(principal=1000.0, interest=50.0, bond_id="GOV-001")

bond_repayment_tx = Transaction(
    # ... other fields like buyer_id, seller_id ...
    transaction_type="bond_repayment",
    item_id=details['bond_id'],
    quantity=1, # Quantity is now 1 unit of "repayment"
    price=details['principal'] + details['interest'], # Price remains total value for settlement
    metadata={"repayment_details": details}
)
```

## 3. Phase 2: Refactor `MonetaryTransactionHandler` (Stateless Execution)

The handler's responsibility will be reduced to only executing transfers, making it stateless.

### 3.1. `handle()` Method Modification

File: `simulation/systems/handlers/monetary_handler.py`

**Current (Flawed) Logic:**

```python
elif tx_type in ["bond_repayment", "omo_sale"]:
    # QT: Agent (Buyer) -> CB (Seller)
    # Burning: Money goes to CB and disappears.
    success = context.settlement_system.transfer(
        buyer, seller, trade_value, tx_type
    )
    if success and context.central_bank and seller.id == context.central_bank.id:
        if hasattr(context.government, "total_money_destroyed"):
            context.government.total_money_destroyed += trade_value # <-- CRITICAL FLAW TO BE REMOVED
```

**Proposed (Corrected) Logic:**

The logic for `bond_repayment` will be simplified to a standard transfer. The direct manipulation of `government.total_money_destroyed` **MUST be removed**.

```python
# In MonetaryTransactionHandler.handle()

# ... other tx_types ...

elif tx_type in ["bond_repayment", "omo_sale"]:
    # The handler's only job is to ensure the total payment is transferred.
    # The MonetaryLedger is responsible for interpreting the monetary impact.
    # The direct manipulation of `government.total_money_destroyed` is removed.
    success = context.settlement_system.transfer(
        buyer, seller, trade_value, tx_type
    )

    # NO MORE CONDITIONAL CHECKS OR LEDGER MANIPULATION HERE.
    # The handler is now stateless regarding monetary aggregates.

# ... The rest of the file ...
```

## 4. Phase 3: Refactor `MonetaryLedger` (Single Source of Truth)

The `MonetaryLedger` will be updated to correctly interpret the new, detailed `bond_repayment` transaction structure.

### 4.1. `process_transactions()` Method Modification

File: `modules/government/components/monetary_ledger.py`

**Current (Flawed) Logic:**

```python
elif tx.transaction_type in ["bond_repayment", "omo_sale"]:
    if str(tx.seller_id) == str(ID_CENTRAL_BANK):
        is_contraction = True
```

**Proposed (Corrected) Logic:**

The logic will be updated to inspect the `metadata` for `repayment_details`. Only the `principal` amount will be counted as a monetary contraction (destruction).

```python
# In MonetaryLedger.process_transactions()
from modules.system.constants import ID_CENTRAL_BANK

for tx in transactions:
    # ... existing logic for other tx types ...

    # 4. CB Selling & Bond Repayments (Contraction)
    elif tx.transaction_type in ["bond_repayment", "omo_sale"]:
        # Check if the payment is going to the Central Bank
        if str(tx.seller_id) == str(ID_CENTRAL_BANK):
            repayment_details = tx.metadata.get("repayment_details") if hasattr(tx, 'metadata') else None

            if repayment_details:
                # **Correct Accounting**: Only the principal is destroyed.
                principal_to_destroy = repayment_details.get("principal", 0.0)
                if principal_to_destroy > 0:
                    is_contraction = True
                    contraction_amount = principal_to_destroy
                # The 'interest' portion is a pure transfer and does not count as destruction.
                # It's income for the Central Bank, but doesn't change M2.
            else:
                # **Legacy Fallback**: If details are missing, revert to old behavior but log a warning.
                # This ensures backward compatibility during transition but flags areas needing updates.
                logger.warning(
                    f"Transaction {tx.id} of type '{tx.transaction_type}' is missing 'repayment_details' in metadata. "
                    f"Treating full amount as contraction based on legacy logic."
                )
                is_contraction = True
                contraction_amount = tx.price * tx.quantity

    # ... existing logic for applying is_expansion/is_contraction flags ...
    # Ensure the correct amount is used when applying contraction.

    if is_expansion:
        # ... as before
    elif is_contraction:
        # **MODIFICATION**: Use the determined contraction_amount
        amount = contraction_amount if 'contraction_amount' in locals() and contraction_amount is not None else tx.price * tx.quantity
        if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0.0
        if cur not in self.total_money_destroyed: self.total_money_destroyed[cur] = 0.0

        self.credit_delta_this_tick[cur] -= amount
        self.total_money_destroyed[cur] += amount
        logger.debug(f"MONETARY_CONTRACTION | {tx.transaction_type}: {amount:.2f} {cur}")
        contraction_amount = None # Reset for next loop iteration
```

## 5. Phase 4: Update Transaction Creation Logic

All code responsible for creating `bond_repayment` transactions **MUST** be located and updated to use the new `BondRepaymentDetailsDTO` and populate the `transaction.metadata` field. This is likely within the `Government` or `Firm` agent classes. A project-wide search for `"bond_repayment"` is required.

## 6. Verification Plan

- **Step 1: Unit Tests for `MonetaryLedger`**
  - Create mock `Transaction` objects with the new `metadata` structure.
  - Test that `process_transactions` correctly identifies the `principal` amount for destruction and ignores the `interest` amount.
  - Test the legacy fallback by passing a transaction without the new metadata and asserting a warning is logged.

- **Step 2: Update `scripts/trace_leak.py`**
  - Modify the script to correctly calculate the `authorized_delta`. It should now query the `MonetaryLedger` after transactions are processed.
  - The script's final integrity check `leak = delta - authorized_delta` will now be a precise validation of the new, correct accounting.

- **Step 3: Integration Testing**
  - Run a full simulation tick where a `bond_repayment` occurs.
  - Use `trace_leak.py` to confirm that the total money supply decreases by exactly the `principal` amount and that there is no "leak."
  - Manually inspect logs to ensure the `MonetaryLedger` reports the correct contraction amount.

## 7. Risk & Impact Audit (Addressing Pre-flight Concerns)

- **[ADDRESSED] Dueling Ledgers:** The `MonetaryTransactionHandler` is now stateless, and `MonetaryLedger` is the single source of truth. The `government.total_money_destroyed` attribute will be deprecated and removed in a subsequent task.
- **[ADDRESSED] Implicit Data Model:** The `BondRepaymentDetailsDTO` provides a clear, explicit data model for repayments, enforced via the `metadata` field.
- **[ADDRESSED] Tight Coupling:** The handler no longer has fragile dependencies on the `Government` agent's internal state.
- **[MITIGATED] Test Breakage:** This plan explicitly calls for updating `trace_leak.py` and creating new unit tests. The legacy fallback in `MonetaryLedger` provides a temporary bridge to prevent catastrophic failure of all old tests, but they should be progressively updated.

## 8. Mandatory Reporting Verification

During the analysis for this specification, the core architectural flaw of "Dueling Ledgers" was identified and targeted for resolution. This insight is critical for long-term system stability. A corresponding entry will be logged in `communications/insights/SPEC-Bond-Repayment-Refactor.md`, detailing the risk of stateful handlers and the importance of single-source-of-truth components.

---
# API Definition: `modules/government/api.py`

```python
"""
Defines the public API for the Government module, including DTOs for inter-module communication.
"""
from typing import TypedDict, Optional

# ======================================================================================
# DTOs (Data Transfer Objects)
# ======================================================================================

class BondRepaymentDetailsDTO(TypedDict):
    """
    A structured object carrying the details of a bond repayment.
    This DTO is expected to be present in the 'metadata' field of a 'bond_repayment' Transaction.
    
    Attributes:
        principal: The portion of the payment that constitutes principal repayment.
                   This amount is subject to monetary destruction if paid to the Central Bank.
        interest: The portion of the payment that constitutes an interest payment.
                  This is treated as a standard transfer and is not destroyed.
        bond_id: A unique identifier for the bond being serviced.
    """
    principal: float
    interest: float
    bond_id: str


# ======================================================================================
# INTERFACES (Future Use)
# ======================================================================================

# No new interfaces are defined in this refactor, but this would be the location for them.
# For example:
#
# from abc import ABC, abstractmethod
#
# class IGovernmentLedger(ABC):
#
#     @abstractmethod
#     def get_total_debt(self) -> float:
#         ...
#
#     @abstractmethod
#     def get_tax_revenue_this_tick(self) -> float:
#         ...

pass

```
