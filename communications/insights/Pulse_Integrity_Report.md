# Technical Insight Report: Operation Pulse Integrity

## 1. Problem Phenomenon
During stress testing (Tick 1-100), the simulation exhibited severe monetary instability:
*   **M2 Leak:** Significant positive M2 drift (leak) detected, reaching ~177k by Tick 90 in early runs.
*   **Crash:** A `TypeError` at Tick 50 (NULL seller_id) and other crashes related to inheritance and database logging.
*   **Ghost Agents:** Dead agents remained in the `currency_holders` list, causing their assets to be counted in M2 even after liquidation/inheritance.

## 2. Root Cause Analysis
### 2.1 M2 Leak & Double Counting
The primary M2 leak was caused by a combination of:
*   **Bank Reserves Double Counting:** M2 was calculated as `M0 + Deposits`, but M0 implicitly included Bank Reserves (since Bank was a currency holder). Since Deposits are backed by Reserves, adding both doubles the count of that money.
*   **Implicit Transfers:** Bank withdrawals and deposits updated logical balances but didn't always physically transfer cash between `Bank.wallet` and `Customer.wallet` in a strictly synchronized way (fixed by handler registration).
*   **Profit Remittance:** Bank profits (interest income) were accumulated but not remitted to the Government, effectively creating a sink or source depending on how M2 was tracked vs. authorized delta.

### 2.2 Ghost Agents (Lifecycle Management)
*   The `TickOrchestrator` rebuilt the `currency_holders` list every tick by iterating over `state.agents`.
*   However, `state.agents` often retained references to inactive/dead agents for transactional history or logging.
*   This caused dead agents to be re-added to the M2 calculation, leading to "Zombie Money" being counted.

### 2.3 Crashes
*   **Tick 50 NULL seller_id:** `InheritanceManager` assigned `None` to `seller_id` for system-mediated transfers, violating database `NOT NULL` constraints.
*   **Logging Crash:** Passing a `dict` (M2 breakdown) to a SQL logger expecting a `float` or JSON string caused a `sqlite3` error.

## 3. Solution Implementation Details
### 3.1 Strict Currency Registry
*   Implemented `StrictCurrencyRegistry` pattern in `WorldState.py`.
*   Introduced `_currency_holders_set` for O(1) membership tracking.
*   Added `register_currency_holder` and `unregister_currency_holder` methods.
*   Updated `TickOrchestrator` to **stop rebuilding** the list every tick. It now relies on `LifecycleManager` to maintain the list incrementally.

### 3.2 Immediate Lifecycle Suture
*   Updated `LifecycleManager` to call `state.unregister_currency_holder(agent)` **immediately** upon agent death or liquidation.
*   This eliminates the "Ghost Agent" window where dead agents could be counted in M2.

### 3.3 M2 Formula Correction
*   Updated `EconomicIndicatorTracker.py` to strictly implement the formula: `M2 = (M0 - Bank Reserves) + Deposits`.
*   This ensures that `M0` correctly represents the Monetary Base (Circulation + Reserves), while `M2` correctly represents Broad Money (Circulation + Deposits).

### 3.4 Transaction Handlers
*   Registered `bank_profit_remittance` handler to ensure bank profits move to Government.
*   Registered `deposit` and `withdrawal` handlers to ensure physical cash movement accompanies logical deposit updates.

## 4. Lessons Learned & Technical Debt
*   **Lesson:** "Rebuilding from source" (like `_rebuild_currency_holders`) is dangerous if the source (`state.agents`) has a different lifecycle (e.g., archival retention) than the derived list (`active_currency_holders`). Strict, event-driven maintenance is safer for critical registries.
*   **Lesson:** M2 definitions must be explicit about "Reserves" vs. "Circulation". Ambiguity leads to double-counting.
*   **Tech Debt:** `SettlementSystem` still has some abstraction leaks (direct property access).
*   **Tech Debt:** `WorldState` is becoming a God Class; `StrictCurrencyRegistry` logic could be extracted to a standalone component.
*   **Residual Drift:** A small residual M2 drift (~1.6% of total) persists, likely due to `bond_repayment` transactions between Government and Commercial Bank not being tracked as M2 contraction in `MonetaryLedger`. Future work should tag these transactions explicitly.
