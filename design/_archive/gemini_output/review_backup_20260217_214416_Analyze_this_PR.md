# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR successfully refactors the Market Matching Engines (`OrderBookMatchingEngine`, `StockMatchingEngine`) to strictly use **Integer Pennies** for price discovery and settlement, resolving the critical technical debt `TD-MKT-FLOAT-MATCH`. It introduces a robust "Dual-Precision" model where `Transaction.total_pennies` serves as the Single Source of Truth (SSoT) for financial settlement, while `Transaction.price` (float) is retained for backward compatibility with UI and Legacy Agents. Extensive test updates and a comprehensive Insight Report confirm the stability of this migration.

## 🚨 Critical Issues
*None detected.* The changes adhere to strict Security and Zero-Sum standards.

## ⚠️ Logic & Spec Gaps
*None detected.* The implementation aligns perfectly with the "Penny Standard" and handling of legacy DTOs via `convert_legacy_order_to_canonical` is pragmatic.

## 💡 Suggestions
*   **Monitor Heuristic Conversion**: The helper `convert_legacy_order_to_canonical` uses a heuristic (`if isinstance(raw_price, float): ... * 100`) to convert legacy orders. Ensure that no legacy systems are passing "Pennies as Float" (e.g., passing `100.0` meaning 100 pennies), as this logic would convert it to `10000` pennies ($100). The current assumption is `Float = Dollars`.

## 🧠 Implementation Insight Evaluation

*   **Original Insight**:
    > "The `OrderBookMatchingEngine` and `StockMatchingEngine` now operate exclusively on `int` pennies... `Transaction` model now carries `total_pennies: int` as the Single Source of Truth... A critical decision was made to ensure `Transaction.price` represents Dollars (float)..."

*   **Reviewer Evaluation**:
    The insight accurately captures the architectural shift. The distinction between **Settlement Truth** (Pennies) and **Display Truth** (Dollars) is a crucial design pattern that prevents "Financial Dust" while maintaining usability. The report correctly identifies the risks associated with Legacy DTO conversion.

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_HISTORY.md`

```markdown
### 2026-02-17: Market Precision Refactor (TD-MKT-FLOAT-MATCH)
- **Problem**: `MatchingEngine` used floating-point arithmetic for price discovery, leading to micro-penny rounding errors and potential Zero-Sum violations.
- **Resolution**:
  - Adopted **Penny Standard**: All matching logic now uses `int` pennies.
  - **Dual-Precision Transactions**: `Transaction` object now holds `total_pennies` (SSoT for Settlement) and `price` (Float for Display).
  - **Legacy Bridge**: Implemented `CanonicalOrderDTO` adapter to seamlessly convert legacy Float/Dollar inputs to Integer/Penny outputs.
- **Key Artifacts**: `communications/insights/market-precision-refactor.md`
```

## ✅ Verdict
**APPROVE**

The PR is architecturally sound, enforces financial integrity via integer math, and maintains excellent backward compatibility. The tests are comprehensive, and the documentation is complete.