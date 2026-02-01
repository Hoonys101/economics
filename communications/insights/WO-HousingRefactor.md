# Mission Insight Report: WO-HousingRefactor

## Technical Debt & Architectural Gaps

### 1. Registry vs. Handler Responsibility
The original specification mandates that the `TransactionManager` calls `Registry.update_ownership` to handle state changes (ownership, mortgage ID). However, the current `TransactionProcessor` implementation (the acting manager) does **not** invoke the `Registry` in its execution loop. It only delegates to the specific `ITransactionHandler`.

**Consequence:**
To ensure functionality, the `HousingTransactionHandler` had to implement `_apply_housing_effects` locally, duplicating the logic found in `Registry._handle_housing_registry`. This violates the Single Responsibility Principle (SRP) but was necessary to ensure the transaction actually updates the simulation state.

**Recommendation:**
Refactor `TransactionProcessor` to explicitly call `Registry.update_ownership` after a successful handler execution, or officially deprecate the `Registry`'s update methods in favor of handler-encapsulated logic (as seen in `GoodsTransactionHandler`).

### 2. Bank Loan Disbursement Logic
The draft specification assumed `Bank.create_loan` (implemented as `grant_loan`) would allow directing funds immediately to Escrow. However, the existing `Bank.grant_loan` implementation automatically credits the loan principal to the **borrower's deposit account**.

**Adaptation:**
The `HousingTransactionHandler` saga was adapted to transfer the loan proceeds from the `Buyer` (who received the funds from the bank) to `Escrow`, rather than a direct Bank->Escrow transfer. This maintains financial integrity (zero-sum) but differs slightly from the idealized flow in the spec.

### 3. Missing Mortgage ID in Registry
The existing `Registry._handle_housing_registry` did not account for `mortgage_id` updates. This was patched in `simulation/systems/registry.py` to check `tx.metadata` for the ID.

## Verification
- Unit tests (`tests/market/test_housing_transaction_handler.py`) verify the Saga pattern, including compensation (rollback) logic for failures at Down Payment, Mortgage, or Disbursement stages.
- Registry tests (`tests/systems/test_registry_housing.py`) confirm the `mortgage_id` update logic works when invoked.
- Integration tests (`tests/unit/test_transaction_processor.py`) confirm the new handler is correctly registered and dispatched.
