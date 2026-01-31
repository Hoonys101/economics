# Insight: WO-HousingRefactor

## Issue: Orphaned Housing Transaction Logic

### Observation
During the refactor to "interact with RealEstateMarket", it was discovered that `HousingSystem.process_transaction` was effectively "dead code" (orphaned) in the current `TransactionManager` execution flow.

### Root Cause
The `TransactionManager` (the new 6-layer architecture component) iterates through transactions and delegates them to handlers or default transfer logic.
- `HousingSystem` logic for transactions (`process_transaction`) was never registered as a handler.
- The `Housing` market produces transactions with `transaction_type="housing"`.
- `TransactionManager` treats "housing" transactions as default generic transfers (Cash Transfer + Registry Update).

### Consequence
- **Mortgage Logic Bypassed**: The crucial logic for calculating LTV, granting loans, and creating deposits (Fractional Reserve Banking) was completely skipped for new house purchases.
- **Housing Transactions were Cash-Only**: Agents were effectively buying houses with cash only, bypassing the credit system entirely.
- **Inconsistent State**: `unit.mortgage_id` was never updated for new purchases.

### Resolution Plan
1.  **Extract Logic**: Move the `process_transaction` logic from `HousingSystem` to a new `HousingTransactionHandler` implementing `ISpecializedTransactionHandler`.
2.  **Register Handler**: Register this handler in `TransactionManager` for "housing" transactions.
3.  **Refactor Registry**: Update `Registry` to correctly handle `housing` item IDs (`unit_{id}`) and update agent property lists (ownership, homelessness status), ensuring the "Non-financial State" is correctly committed.
4.  **Decouple**: `HousingSystem` becomes a passive system for recurring events (rent/foreclosure), while `HousingTransactionHandler` manages the active transaction flow.
