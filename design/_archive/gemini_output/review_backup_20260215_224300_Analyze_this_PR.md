# Code Review Report

## 🔍 Summary
Refactoring of financial DTOs and Engines from `float` to `int` (pennies) to ensure Zero-Sum integrity. Covers `Firm`, `Finance`, `Sales`, `Production`, `HR`, and `Settlement` modules.

## 🚨 Critical Issues
*   **Unit Mismatch Risk (Inflation Bug)**: In `simulation/firms.py` line ~1017:
    ```python
    unit_cost_estimate=int(self.finance_engine.get_estimated_unit_cost(self.finance_state, item_id, self.config) * 100),
    ```
    If `FinanceEngine` logic uses `FinanceState` (which now stores `int` pennies for `revenue`, `expenses`, etc.) to calculate cost, `get_estimated_unit_cost` likely returns **pennies**. Multiplying by 100 again would effectively inflate the cost estimate by 100x (e.g., 1000 pennies cost becomes 100,000). Verify if `get_estimated_unit_cost` returns dollars or pennies. If it returns pennies, remove `* 100`.

## ⚠️ Logic & Spec Gaps
*   **SalesEngine Return Type**: In `simulation/components/engines/sales_engine.py`, `adjust_marketing_budget` calculates `target_budget` using `revenue_this_turn * new_rate` (int * float = float).
    ```python
    target_budget = revenue_this_turn * new_rate
    ```
    Ensure the return statement (not shown in diff) casts this to `int` before returning `MarketingAdjustmentResultDTO(new_budget=...)`. If not, this violates the new DTO contract.

## 💡 Suggestions
*   **Explicit Return Typing**: Ensure all Engine methods explicitly returning DTOs with `int` fields perform the `int()` cast at the return statement to catch any lingering float math.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: "The core simulation models and Data Transfer Objects (DTOs) have been successfully migrated from `float` to `int`... Aligns with Zero-Sum Integrity."
*   **Reviewer Evaluation**: The insight accurately reflects the scope. However, it should explicitly mention the risk of "Double Conversion" (multiplying by 100 on already-converted values) as a key lesson for future migrations. The note about `IBank` protocol updates is valuable.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/1_governance/architecture/standards/FINANCIAL_INTEGRITY.md`
*   **Draft Content**:
    ```markdown
    ### Data Type Standard (2026-02 Update)
    All financial values (prices, balances, costs, revenues) must be stored and transmitted as **Integers (Pennies)** to prevent floating-point drift.
    - **Models & DTOs**: Use `int`.
    - **Calculations**: Perform multiplication/division using floats if necessary, but cast to `int` immediately upon completion (floor/round).
    - **Migration Watchout**: When converting legacy code, verify that values coming from updated DTOs (already pennies) are not multiplied by 100 again (Double Conversion).
    ```

## ✅ Verdict
**REQUEST CHANGES**

The potential 100x inflation bug in `Firm.py` (Unit Mismatch) must be verified and fixed before merging. The `SalesEngine` return type should also be double-checked.