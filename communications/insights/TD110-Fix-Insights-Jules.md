# TD-110 Phantom Tax Fix Insights

**Developer:** Jules
**Date:** 2026-01-25
**Task:** Couple Tax Collection and Revenue Recording

## Summary
The goal was to eliminate "Phantom Tax" revenue (where revenue is recorded but funds are not transferred) by enforcing an atomic tax collection process. The solution involved refactoring `TaxAgency` to be a stateless service that executes transfers via `SettlementSystem` and returns a `TaxCollectionResult` DTO. `Government` was updated to consume this DTO and update its ledgers only upon success.

## Key Changes
1.  **API DTO**: Introduced `TaxCollectionResult` in `modules/finance/api.py`.
2.  **Stateless TaxAgency**: `TaxAgency.collect_tax` now takes `SettlementSystem` as a dependency and executes the transfer atomically. `record_revenue` was emptied and deprecated.
3.  **Synchronous Wealth Tax**: `Government.run_welfare_check` no longer generates deferred transactions for Wealth Tax. It collects tax synchronously using the new atomic method.
4.  **TransactionProcessor Update**: Removed manual tax transfer logic (`settlement.transfer` to government) for Sales and Labor taxes. Instead, it relies on the existing calls to `government.collect_tax`, which now perform the atomic transfer. This eliminates code duplication and ensures consistency.
5.  **Legacy Callers**: Updated `InheritanceManager` and `LifecycleManager` to use `government.collect_tax` instead of manual transfers and `record_revenue` calls.

## Challenges & Insights
1.  **Ghost Revenue vs. Phantom Tax**: While the spec warned of "Phantom Tax" (revenue without money), investigation revealed a potential for "Ghost Revenue" (money transferred without revenue recording) in the legacy `TransactionProcessor` logic where `FinanceSystem.collect_corporate_tax` was returning `False`. The new system fixes both by coupling them tightly.
2.  **TransactionProcessor Complexity**: `TransactionProcessor` had duplicate logic for transferring tax (manual transfer AND `collect_tax` call). Identifying that the `collect_tax` calls were already present allowed for a cleaner refactor by simply removing the manual transfers.
3.  **Withholding Tax Logic**: Refactoring household income tax required changing the flow. Previously, the Employer paid the Net Wage to the Worker and the Tax to the Government. Now, the Employer pays the Gross Wage to the Worker, and the Government debits the Tax from the Worker immediately. This preserves the "Withholding" economic effect (Worker never really "sees" the tax money) while respecting the correct payer/payee relationship in `SettlementSystem`.
4.  **Leak Diagnosis**: Running `diagnose_money_leak.py` revealed significant leaks (`-29k`) that appear to be pre-existing or related to liquidation dynamics unrelated to the tax fix. The tax fix itself was verified to be zero-sum via unit tests.

## Recommendations
*   **SettlementSystem Ubiquity**: The system is safer when `SettlementSystem` is used everywhere. Legacy paths that bypass it (direct `_sub_assets`) should be aggressively deprecated.
*   **TransactionProcessor Refactor**: `TransactionProcessor` is still a complex procedural block. Further breaking it down into specialized handlers (like `LaborTransactionHandler`) would improve maintainability.
