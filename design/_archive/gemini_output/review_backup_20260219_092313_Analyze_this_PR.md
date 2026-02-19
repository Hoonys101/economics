# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**. 
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

# 🛡️ Code Review Report

## 🔍 Summary
This PR implements "Dual-Precision" integer math across the Commerce, Goods, Labor, and Settlement systems, establishing `total_pennies` as the Single Source of Truth (SSoT) for financial transactions. It includes refactoring of transaction handlers to prioritize integer math and fallback mechanisms for legacy floating-point compatibility, supported by a new suite of hardening tests.

## 🚨 Critical Issues
*None detected.*

## ⚠️ Logic & Spec Gaps
1.  **Unsafe Truncation in HousingHandler (`modules/market/handlers/housing_transaction_handler.py` - Line ~67)**:
    *   **Defect**: The fallback logic for legacy transactions uses `sale_price = int(tx.price * tx.quantity * 100)`.
    *   **Risk**: This creates a truncation risk (e.g., `29.99999` becoming `29` pennies) due to floating-point drift, which violates the mission's core objective of "preventing truncation errors" via "Explicit Rounding".
    *   **Requirement**: This must be changed to use `round_to_pennies(...)` to match the robust implementation in `GoodsTransactionHandler` and `LaborTransactionHandler`.

## 💡 Suggestions
1.  **Import Consistency**: Import `round_to_pennies` in `modules/market/handlers/housing_transaction_handler.py` and apply it to the fallback calculation.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: "Explicit Rounding: CommerceSystem and TransactionProcessor were refactored to use `round_to_pennies(price * quantity * 100)`... This prevents truncation errors".
*   **Reviewer Evaluation**: The insight accurately reflects the architectural intent and the changes in most modules. However, the implementation in `HousingTransactionHandler` deviates from this standard (using `int()` instead of `round`), which undermines the integrity claimed in the report.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
| **TD-MKT-FLOAT-MATCH** | Markets | **Market Precision Leak**: `MatchingEngine` and Handlers updated to use Integer Math (`total_pennies`). | **Critical**: Financial Halo. | **Resolved** |
```

## ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

*Reason: The `HousingTransactionHandler` introduces a truncation risk by using raw `int()` casting instead of the required `round_to_pennies()` helper, directly contradicting the financial integrity standards established in this PR.*