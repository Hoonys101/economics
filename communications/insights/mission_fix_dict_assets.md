# Fix TypeError in Orchestration and Systems due to Multi-Currency Assets

## Phenomenon
A `TypeError: unsupported operand type(s) for /: 'dict' and 'float'` was reported in `simulation/orchestration/utils.py` at line 97. This occurred when the code attempted to divide `firm.assets` (which had become a dictionary `{CurrencyCode: float}` in Phase 33) by `firm.total_shares` (a float). Similar type incompatibility issues were identified in `GoodsTransactionHandler` during solvency checks and in `TickOrchestrator` during economic tracking.

## Root Cause
1.  **Legacy Float Assumption:** Much of the legacy simulation logic assumed `agent.assets` (or `.balance`) was a simple `float` representing USD.
2.  **Partial Migration to Multi-Currency:** Phase 33 introduced multi-currency support, changing `assets` to a `Dict[CurrencyCode, float]` or `MultiCurrencyWalletDTO`. While core systems were updated, peripheral logic in orchestration, handlers, and reporting was not fully audited for this type change.
3.  **Ambiguous Type Handling:** `GoodsTransactionHandler` compared `buyer.assets` directly with `total_cost` (float), which fails when `assets` is a dictionary.

## Solution
1.  **Safe Asset Extraction in Utils:** Updated `simulation/orchestration/utils.py` to check if `assets` is a dictionary. If so, it extracts the value for `DEFAULT_CURRENCY` (defaulting to 0.0) before performing the division for stock price calculation.
2.  **Currency-Aware Solvency Check:** Updated `simulation/systems/handlers/goods_handler.py` to identify the transaction currency (or fallback to default) and look up the specific balance in the buyer's asset dictionary for comparison against the cost.
3.  **Scalar Money Supply for Tracker:** Updated `simulation/orchestration/tick_orchestrator.py` to convert the total money supply dictionary into a scalar value (USD/Default) using `state.get_total_system_money_for_diagnostics(DEFAULT_CURRENCY)` before passing it to `EconomicIndicatorTracker.track`, ensuring compatibility with the tracker's expected input.

## Lessons Learned
*   **Type Audits are Critical:** When changing the type of a core field like `assets`, a comprehensive audit (using `grep` or static analysis) of all usages is required, especially in "peripheral" code like utils, logging, and legacy handlers.
*   **Defensive Coding:** Logic that interacts with potentially polymorphic fields (legacy float vs. new dict) should implement defensive type checks (`isinstance`) during the transition period.
*   **Scalar Conversion for Reporting:** Reporting tools and trackers often expect scalar values. Explicit conversion layers should be used at the interface between the core multi-currency engine and legacy reporting systems.
