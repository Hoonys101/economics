# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR implements the **Penny Standard** across `OrderBookMatchingEngine` and `StockMatchingEngine`, migrating price discovery and settlement from floating-point arithmetic to integer `pennies`. It introduces `CanonicalOrderDTO.price_pennies` and `Transaction.total_pennies` as the Single Source of Truth (SSoT), updating handlers to prefer these integer values.

## 🚨 Critical Issues
*   None. (Security and Hardcoding checks passed).

## ⚠️ Logic & Spec Gaps
*   **Adapter Inconsistency (Bug Risk)**: In `modules/market/api.py`, the `convert_legacy_order_to_canonical` function exhibits inconsistent behavior:
    *   **Dict Path**: `isinstance(raw_price, float)` inputs are multiplied by 100 (`int(raw_price * 100)`), correctly assuming Dollars to Pennies conversion.
    *   **Object Path (`StockOrder`)**: `int(order.price)` is used directly. If a legacy `StockOrder` has `price=45.0` (Dollars), it converts to `45` pennies ($0.45) instead of `4500` pennies ($45.00). The test `test_convert_stock_order` in `test_market_adapter.py` confirms this behavior (`price=45.0` -> `price_pennies=45`), which contradicts `test_stock_market.py` where `45.0` corresponds to `4500` pennies. This needs to be harmonized or explicitly documented if `StockOrder` is guaranteed to be pennies-only (which `test_market_adapter.py` usage suggests otherwise).

## 💡 Suggestions
*   **Fix Adapter Logic**: Harmonize the `StockOrder` object conversion logic to match the Dictionary logic (check type, multiply by 100 if float) or verify intent.
*   **Display Price Scaling**: Since `Transaction.price` is now calculated as `total_pennies / quantity`, the "Display Price" has effectively scaled up by 100 (e.g., $1.00 -> 100.0). Consider dividing by 100.0 for the `price` field if it is intended for UI/Legacy Agent compatibility (Dollars), while keeping `total_pennies` for settlement. Currently, `Transaction.price` has changed semantics (Dollars -> Cents).

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: Defined in `communications/insights/market-precision-refactor.md`. Mentions the Penny Standard adoption, DTO migration, and the "Scale Discrepancy" where `Transaction.price` is now pennies.
*   **Reviewer Evaluation**: The insight accurately captures the architectural shift. The identification of the "Scale Discrepancy" is crucial. The risk assessment regarding legacy agents is valid and high-priority. The report is well-structured and evidenced.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
| **TD-MKT-FLOAT-MATCH** | Markets | **Market Precision Leak**: `MatchingEngine` uses `float` for price discovery. Violates Zero-Sum. | **Critical**: Financial Halo. | **Resolved** |
```

## ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

**Reason**: The **Adapter Inconsistency** in `modules/market/api.py` regarding `StockOrder` conversion (Line 118) creates a high risk of value destruction (99% value loss) during migration if legacy objects holding float Dollar values are passed. This must be fixed or clarified before merging. Additionally, ensure the `communications/insights/market-precision-refactor.md` file is staged (it appears to be, but confirming).