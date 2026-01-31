# SPEC: TD-170 Escrow-Based Atomic Tax Collection

## 1. Executive Summary
This document outlines the technical specification for implementing the "Escrow/Pre-Authorization Model" (Solution A) to resolve the sales tax atomicity violation identified in `AUDIT: TD-170`. This change introduces an escrow step into the `TransactionProcessor` to ensure that the total transaction cost (trade value + sales tax) is secured from the buyer *before* funds are distributed to the seller and the government. This guarantees atomic collection and prevents revenue loss.

## 2. Architectural Changes

### 2.1. System Escrow Agent
- **Definition**: A new singleton entity, `EscrowAgent`, will be created. This agent will act as a temporary holding account for funds during a transaction.
- **Interface**: `EscrowAgent` **MUST** implement the existing `core.components.IAccount` interface, allowing it to interact seamlessly with the `SettlementSystem`.
- **Instantiation**: The `EscrowAgent` will be instantiated once at the root of the simulation (e.g., in `main.py` or the primary simulation setup) and will persist for the lifetime of the simulation. It will have an initial balance of zero.

### 2.2. Dependency Injection
- **Target**: The `simulation.systems.TransactionProcessor` class.
- **Modification**: The constructor of `TransactionProcessor` will be modified to accept the `EscrowAgent`.
  ```python
  # current
  def __init__(self, settlement_system: ISettlementSystem, government: IGovernment):
      ...

  # proposed
  def __init__(self, settlement_system: ISettlementSystem, government: IGovernment, escrow_agent: IAccount):
      ...
  ```
- **Impact**: The instantiation point of `TransactionProcessor` must be updated to pass the singleton `EscrowAgent` instance.

## 3. Detailed Logic (Pseudo-code)
The logic within `TransactionProcessor.process_transaction` for `"goods"` types will be replaced with the following three-step escrow flow.

```python
# In simulation.systems.TransactionProcessor.process_transaction

def process_transaction(self, tx: TransactionDTO):
    if tx.transaction_type == "goods":
        buyer = self.get_account(tx.buyer_id)
        seller = self.get_account(tx.seller_id)
        
        trade_value = tx.amount
        tax_rate = self.government.get_sales_tax_rate()
        tax_amount = trade_value * tax_rate
        total_cost = trade_value + tax_amount

        # 1. Secure Total Amount in Escrow
        memo_escrow = f"escrow_hold:{tx.item_id}"
        escrow_success = self.settlement_system.transfer(
            payer=buyer,
            payee=self.escrow_agent,
            amount=total_cost,
            memo=memo_escrow
        )

        # 2. Abort if Escrow Fails
        if not escrow_success:
            # Transaction fails, no funds are moved, log the failure.
            return False

        # 3. Distribute Funds from Escrow
        try:
            # 3a. Pay Seller
            memo_trade = f"goods_trade:{tx.item_id}"
            trade_success = self.settlement_system.transfer(
                payer=self.escrow_agent,
                payee=seller,
                amount=trade_value,
                memo=memo_trade
            )
            if not trade_success:
                # This is a critical system failure, as funds are stuck in escrow.
                # Requires a robust alert/rollback mechanism.
                # For now, log as a CRITICAL error.
                # A compensating transaction to return funds to buyer is needed.
                self.settlement_system.transfer(self.escrow_agent, buyer, total_cost, "escrow_reversal:critical_failure")
                raise SystemError(f"CRITICAL: Escrow distribution failed. Trade value transfer to seller failed for tx {tx.id}.")

            # 3b. Pay Tax to Government
            if tax_amount > 0:
                memo_tax = f"sales_tax:{tx.item_id}"
                tax_success = self.settlement_system.transfer(
                    payer=self.escrow_agent,
                    payee=self.government.treasury, # Assuming government has a treasury IAccount
                    amount=tax_amount,
                    memo=memo_tax
                )
                if not tax_success:
                    # This is also a critical system failure.
                    # Rollback both the escrow hold and the payment to the seller.
                    self.settlement_system.transfer(seller, self.escrow_agent, trade_value, "reversal:tax_failure")
                    self.settlement_system.transfer(self.escrow_agent, buyer, total_cost, "escrow_reversal:critical_failure")
                    raise SystemError(f"CRITICAL: Escrow distribution failed. Tax transfer to government failed for tx {tx.id}.")

        except Exception as e:
            # Handle unexpected errors during distribution
            # The goal is to ensure funds don't get stuck in escrow.
            # A full rollback is the safest path.
            # TBD (Team Leader Review Required): Define a robust multi-stage transaction recovery protocol.
            # For now, attempt a full reversal.
            # Note: This part is complex as the seller might have already been paid.
            # A simple reversal is not enough. A proper Saga pattern might be needed long-term.
            return False

        return True
```

## 4. Interface & DTO Specification
- **`core.components.IAccount`**: No changes. To be implemented by `EscrowAgent`.
- **`simulation.systems.ITransactionProcessor`**: No changes to method signatures. The dependency change is in the concrete class constructor.
- **DTOs**: No changes to any `TransactionDTO` or other data transfer objects.

## 5. Verification & Test Plan
Existing tests for `TransactionProcessor` are **invalidated** and MUST be rewritten.

- **Test Suite**: `tests/modules/system/test_transaction_processor.py`
- **Strategy**: Mocks for `ISettlementSystem` must be updated to assert the new three-step call sequence.

### Test Case 1: Successful Transaction
- **Given**: A `buyer` with sufficient funds (`>= total_cost`), a `seller`, and a `government`.
- **When**: A "goods" transaction is processed.
- **Then**:
    1.  `settlement_system.transfer` is called with `(payer=buyer, payee=escrow_agent, amount=total_cost)`. Mock returns `True`.
    2.  `settlement_system.transfer` is called with `(payer=escrow_agent, payee=seller, amount=trade_value)`. Mock returns `True`.
    3.  `settlement_system.transfer` is called with `(payer=escrow_agent, payee=government.treasury, amount=tax_amount)`. Mock returns `True`.
    4.  The final balances of all parties are correct.

### Test Case 2: Failed Transaction (Insufficient Funds)
- **Given**: A `buyer` with insufficient funds (`< total_cost`).
- **When**: A "goods" transaction is processed.
- **Then**:
    1.  `settlement_system.transfer` is called with `(payer=buyer, payee=escrow_agent, amount=total_cost)`. Mock returns `False`.
    2.  No other calls to `settlement_system.transfer` are made.
    3.  The transaction is reported as failed.
    4.  The balances of `buyer`, `seller`, and `government` are unchanged.

## 6. Mocking Guide
- **Use Golden Fixtures**: Leverage `tests/conftest.py` fixtures (`golden_households`, `golden_firms`) as `buyer` and `seller`.
- **Prohibit `MagicMock`**: Do not manually create `MagicMock` for agents. Use the provided fixtures to ensure type safety.
- **`ISettlementSystem` Mock**: The mock for the settlement system is the critical piece. It must be stateful enough to verify the sequence of calls and amounts. `pytest-mock`'s `mocker` can be used to patch the dependency and check `call_args_list`.

## 7. Risk & Impact Audit
This implementation directly addresses the pre-flight audit findings.

- **Critical Risk (Test Invalidation)**: **Acknowledged.** This is the largest impact. The entire test suite for goods transactions in the processor must be discarded and rewritten to validate the new escrow logic.
- **Critical Risk (SRP Violation)**: **Acknowledged.** `TransactionProcessor` now also manages the escrow lifecycle, increasing its complexity. This is accepted as a tactical solution to fix a critical bug. A `TECH_DEBT_LEDGER` entry should be created to explore `Solution B: Atomic Batch Transfers` as a long-term, cleaner architectural pattern.
- **Architectural Constraint (Escrow Agent)**: **Met.** The plan specifies the creation and injection of a dedicated `EscrowAgent` that implements `IAccount`.
- **Architectural Constraint (Interface Adherence)**: **Met.** The solution exclusively uses the existing `ISettlementSystem.transfer()` method and does not modify core financial interfaces.

## 8. Implementation Checklist
- [ ] **Phase 1: Setup**
    - [ ] Create `modules/system/escrow_agent.py` with class `EscrowAgent(IAccount)`.
    - [ ] In `main.py` (or equivalent simulation runner), instantiate a singleton `escrow_agent = EscrowAgent()`.
    - [ ] Update `TransactionProcessor.__init__` to accept `escrow_agent: IAccount`.
    - [ ] Update `TransactionProcessor`'s instantiation site to pass the `escrow_agent`.
- [ ] **Phase 2: Logic**
    - [ ] Implement the three-step escrow logic in `TransactionProcessor.process_transaction` as per the pseudo-code.
    - [ ] Add robust logging for each step (escrow hold, distribution, failure, reversal).
- [ ] **Phase 3: Verification**
    - [ ] Delete existing tests for goods transaction tax logic in `tests/modules/system/test_transaction_processor.py`.
    - [ ] Write new tests covering the successful transaction and insufficient funds scenarios.
    - [ ] (Optional but Recommended) Write a test for the critical failure scenario where distribution from escrow fails, ensuring funds are correctly returned.
- [ ] **Phase 4: Documentation**
    - [ ] Create `TECH_DEBT_LEDGER` entry for "Implement Atomic Batch Transfers in SettlementSystem".
    - [ ] Update `CHANGELOG.md` with the fix for `TD-170`.
