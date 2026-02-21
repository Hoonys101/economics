# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR aligns the `DebtServicingEngine` and associated unit tests with the **Penny Standard** (Integer Arithmetic).
1.  **Engine Fix**: `DebtServicingEngine` now correctly divides `interest_pennies` by 100.0 when setting the `price` field (which is a float display value), ensuring `Transaction.price` represents Dollars while `Transaction.total_pennies` represents the integer core.
2.  **Test Updates**: Multiple unit tests (`test_finance_engines.py`, `test_double_entry.py`, etc.) were updated to assert against `total_pennies` instead of `price`, eliminating fragility caused by float comparisons and enforcing the integer-first architecture.
3.  **Mock Sync**: `test_government_fiscal_policy.py` mock updated to support `issue_treasury_bonds_synchronous`.

## 🚨 Critical Issues
*   None.

## ⚠️ Logic & Spec Gaps
*   None. The logic changes strictly adhere to `FINANCIAL_INTEGRITY.md` standards.

## 💡 Suggestions
*   **Future Refactoring**: Consider making `Transaction.price` a computed property `@property def price(self): return self.total_pennies / 100.0` to preventing future desynchronization where an engine sets `price` incorrectly.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "Strict Penny/Dollar Separation: The codebase is moving towards a strict separation where internal value tracking uses integer pennies (`total_pennies`), and floating-point dollars (`price`) are primarily for display or derived representation."
*   **Reviewer Evaluation**:
    *   **Valid & High Value**: The insight correctly identifies the root cause of the test failures (semantic mismatch between "Pennies" and "Dollars" in the `price` field).
    *   **Standardization**: It effectively highlights the architectural rule that `price` is a *derivative* of `total_pennies`, not the source of truth.

## 📚 Manual Update Proposal (Draft)

*   **Target File**: `design/1_governance/architecture/standards/FINANCIAL_INTEGRITY.md`
*   **Draft Content**:

```markdown
### 4. Transaction Object Protocol (Price vs. Pennies)
- **Source of Truth**: The `total_pennies` (int) field is the ABSOLUTE reference for value.
- **Display Value**: The `price` (float) field is strictly for display/logging and MUST be calculated as `total_pennies / 100.0`.
- **Validation**: Engines creating transactions MUST ensure `int(price * 100) == total_pennies` (allow for minor float epsilon if strictly necessary, but prefer integer derivation).
- **Testing**: Unit tests MUST assert against `total_pennies`, not `price`, to avoid floating-point assertion errors and ensure integer precision.
```

## ✅ Verdict
**APPROVE**