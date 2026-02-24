# 🐙 Code Review Report: Financial Integrity & Saga Recovery (WO-LIQUID-W2-FINANCE)

## 1. 🔍 Summary
This PR successfully addresses multiple systemic financial integrity issues: it refactors the M2 calculation to isolate System Debt, fixes the deflationary "penny shaving" bias in market matching, eliminates double-expense counting for raw material purchases, and hardens the `CommandService` rollback and `SagaOrchestrator` lifecycle management. 

## 2. 🚨 Critical Issues
*   **None Found**: No security violations, hardcoded paths, or Zero-Sum breaches were detected. The transition from hardcoded `0.03` base rates to configuration-driven values (`economy_params.bank.base_rate`) is a positive security and configuration purity improvement.

## 3. ⚠️ Logic & Spec Gaps
*   **None Found**: The implementations strictly follow the intended architectural refactoring.
    *   The `calculate_total_money` explicitly returns a dictionary separating `DEFAULT_CURRENCY` from `SYSTEM_DEBT`, preventing soft budget deficits from masking the actual M2 supply.
    *   Replacing integer division (`//`) with `int(round(...))` in `MatchingEngine` correctly stops the persistent destruction of fractional pennies.
    *   Filtering out raw materials from `record_expense` in `GoodsTransactionHandler` accurately reflects Asset Swaps (Cash to Inventory) and prevents P&L distortion prior to actual COGS realization.

## 4. 💡 Suggestions
*   **Minor Suggestion for `calculate_total_money`**: The return type was changed to `Dict[str, int]`. Ensure that downstream consumers (diagnostics or audit scripts) that strictly expect `CurrencyCode` enums are aware of the `"SYSTEM_DEBT"` string key to avoid potential `KeyError` or type mismatch issues during strict type-checking, though the handling in `get_total_system_money_for_diagnostics` is already robust.
*   **GoodsTransactionHandler `sector` Check**: The check `hasattr(buyer, "sector")` works perfectly for Firms, but in a strictly typed system, checking `isinstance(buyer, ISectorAgent)` (if available) might provide stronger guarantees than `hasattr`.

## 5. 🧠 Implementation Insight Evaluation
*   **Original Insight**: 
    > *   **M2 Definition Refinement**: The `calculate_total_money` logic was overhauled to explicitly separate **System Debt**... from **Circulating Money** (M2).
    > *   **Protocol-Driven Rollback**: The `CommandService` rollback logic was hardened by enforcing the `IRestorableRegistry` protocol. We removed brittle `hasattr` checks...
    > *   **Accounting Gap (Asset Swaps)**: A subtle accounting flaw was identified where raw material purchases by Firms were being double-counted as expenses...
    > *   **Market Float Truncation**: The `MatchingEngine` (both Stock and OrderBook) was refactored to use `int(round(...))` instead of integer truncation (`//`) for mid-price calculations.
*   **Reviewer Evaluation**: The insight is exceptionally detailed and accurate. It captures a critical architectural distinction between an Asset Swap (Balance Sheet) and an Expense (P&L), which is a common pitfall in economic simulations. Identifying the deflationary bias caused by floor division (`//`) is also a high-value discovery. The insights are technically sound and directly reflect the code changes.

## 6. 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md`
*   **Draft Content**:
```markdown
### [WO-LIQUID-W2-FINANCE] Deflationary Bias and P&L Distortion Fixes
- **현상 (Phenomenon)**: 
  1. The total M2 supply was artificially shrinking, triggering false-positive leak alarms. 
  2. Firms purchasing raw materials exhibited distorted P&L statements with abnormally high expenses.
- **원인 (Cause)**: 
  1. Mid-price calculations in the `MatchingEngine` used integer truncation (`//`), systematically destroying fractions of pennies on every trade. Additionally, negative balances from System Agents (Soft Budgets) were improperly netted against circulating money.
  2. Raw material purchases were immediately recorded as an expense during the transaction settlement, and then again as COGS during production.
- **해결 (Solution)**: 
  1. Replaced truncation with `int(round(...))` for market matching. Refactored M2 calculation to strictly separate positive `DEFAULT_CURRENCY` balances from negative `SYSTEM_DEBT`.
  2. Updated `GoodsTransactionHandler` to treat raw material purchases as pure Asset Swaps (Cash -> Inventory), bypassing `record_expense`.
- **교훈 (Lesson)**: Always distinguish between Balance Sheet operations (Asset Swaps) and Income Statement operations (Expenses) during transaction settlement. Furthermore, when dealing with integers representing pennies, explicit rounding is required to prevent systemic value leaks over millions of transactions.
```

## 7. ✅ Verdict
**APPROVE**