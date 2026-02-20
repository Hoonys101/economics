# 🐙 Gemini CLI System Prompt: Git Reviewer

## 📝 Code Review Report

### 1. 🔍 Summary
This PR addresses **TD-AI-DEBT-AWARE** by introducing debt visibility to the Firm's decision-making engines. It expands `FinanceStateDTO` to include `total_debt_pennies` and `average_interest_rate`, updates `Firm` to populate these from the Bank via a strictly typed interface, and refactors `FirmSystem2Planner` (AI) and `FinanceEngine` (Execution) to account for interest expenses and distress conditions (Altman Z-Score logic).

### 2. 🚨 Critical Issues
*   None. The changes adhere to security standards, and the explicit integer quantization (`int(debt_status.total_outstanding_debt * 100)`) prevents floating-point drift in the financial core.

### 3. ⚠️ Logic & Spec Gaps
*   **Magic Numbers in FinanceEngine**: The `FinanceEngine` introduces hardcoded logic:
    *   `365` (Daily interest divisor)
    *   `1.8` (Altman Z-Score Distress Threshold)
    *   `0.05` / `0.005` (Repayment Rates)
    *   While functionally correct, these should ideally be moved to `FirmConfigDTO` or a central `EconomyConstants` file to allow for future tuning without code changes.

### 4. 💡 Suggestions
*   **Local Import Smell**: The local import `from simulation.loan_market import LoanMarket` in `Firm._update_debt_status` is a known workaround for circular dependencies. Consider extracting a shared `ILoanMarket` interface (Protocol) in `modules/market/api.py` that exposes the `bank` property, allowing `Firm` to depend on the interface rather than the concrete class.

### 5. 🧠 Implementation Insight Evaluation
*   **Original Insight**: *[Debt Blindness in Firm AI ... Root Cause: `FinanceStateDTO` lacked `total_debt_pennies` ... Resolution: We enforced strict type checking using `isinstance` against `IBank` (Protocol) ...]*
*   **Reviewer Evaluation**: The insight is **High Quality**. It correctly identifies the architectural root cause (DTO boundary data loss) rather than just fixing the symptom. It also honestly documents the "Protocol Purity & Circular Dependencies" trade-off, which is crucial for future maintainers. The "Penny Standard" adherence verification is also a strong point.

### 6. 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
### ID: TD-AI-DEBT-AWARE
- **Title**: AI Constraint Blindness (Log Spam)
- **Symptom**: AI proposes aggressive investments while in a debt spiral.
- **Risk**: Inefficient decision-making. AI fails to "learn" the barrier.
- **Solution**: [RESOLVED] Added `total_debt_pennies` and `average_interest_rate` to `FinanceStateDTO`. `FirmSystem2Planner` now includes interest expense in NPV calculations. `FinanceEngine` implements distress-based repayment logic (Altman Z-score).
- **Status**: Audit Done (Ready to Archive)
```

### 7. ✅ Verdict
**APPROVE**

The PR effectively resolves the debt blindness issue with safe, typed changes. The architectural compromise (local import) is documented and acceptable for this iteration. Test coverage confirms the fix.