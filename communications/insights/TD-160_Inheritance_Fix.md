# Insight: TD-160 Inheritance & TD-192 Audit

## 1. Inheritance Manager Fix (TD-160)
The current `InheritanceManager` correctly creates a `LegacySettlementAccount` which captures the deceased's portfolio. However, the escheatment logic (transfer to Government when no heirs) relies on `SettlementSystem.execute_settlement` iterating over the `distribution_plan` to find the Government.

**Issue**: If the deceased has 0 cash, `InheritanceManager` adds nothing to `distribution_plan` (because `if cash > 0`). Consequently, `SettlementSystem.execute_settlement` has an empty plan to iterate over, and the loop that checks `if account.is_escheatment` and triggers `recipient.receive_portfolio` is never entered.

**Solution**: Force the Government into the `distribution_plan` (with 0.0 cash) when there are no heirs, even if cash is 0. This ensures `SettlementSystem` visits the Government entry and triggers the portfolio transfer.

## 2. ActionProcessor Refactor (TD-192 / Task 2)
The task requested replacing direct asset modifications in `ActionProcessor` with `SettlementSystem` calls.
An audit of `ActionProcessor` (wrapper) and `TransactionProcessor` (dispatcher) and its handlers (`FinancialTransactionHandler`, `AssetTransferHandler`, `MonetaryHandler`, `StockTransactionHandler`, `GovernmentSpendingHandler`) revealed that **they already use `SettlementSystem`**.
- `settlement_system.transfer(...)` and `settlement_system.settle_atomic(...)` are consistently used for cash/value transfers.
- Direct property modification (`.assets +=`) was not found in these handlers (except for read operations).
- Direct modification of `shares_owned` (inventory) in `StockTransactionHandler` is appropriate as `SettlementSystem` handles cash, while handlers manage specific asset registries (unless using `receive_portfolio` which is specific to inheritance).

**Conclusion**: No refactoring of `ActionProcessor` is required as it complies with the requirement. The "audit" mentioned in the task draft likely referred to confirming this state or referred to `TickOrchestrator` (which the draft recommended NOT refactoring).
