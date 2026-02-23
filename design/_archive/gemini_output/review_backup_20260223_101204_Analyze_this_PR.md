# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR implements a comprehensive realignment of the Finance Module's API and DTOs, strictly enforcing the **Penny Standard (Integer Arithmetic)** across all financial transactions and state objects. It consolidates DTOs into `modules/finance/dtos.py`, removes legacy floating-point definitions, and updates core systems (`Bank`, `FinanceSystem`, `Government`) to comply with the new integer-based contracts.

## 🚨 Critical Issues
*   None found. The changes consistently enforce the Penny Standard and do not appear to introduce new security vulnerabilities or hardcoded secrets.

## ⚠️ Logic & Spec Gaps
*   **`simulation/bank.py` (Line ~278)**: There are leftover comments and dead code questioning the conversion logic (`# Convert back to pennies... No, outstanding_balance is float.`).
    ```python
    +             total_debt = int(sum(l.outstanding_balance for l in loans) * 100) # Convert back to pennies for total? No, outstanding_balance is float.
    +             # Wait, total_outstanding_pennies should be int.
    +             # loans has remaining_principal_pennies.
    +             total_debt_pennies = sum(l.remaining_principal_pennies for l in loans)
    ```
    The variable `total_debt` appears unused as `DebtStatusDTO` uses `total_debt_pennies`. These comments and the unused calculation should be removed for cleanliness.
*   **`simulation/loan_market.py` (Line ~292)**: The conversion `loan_amount_pennies = int(order.quantity * 100)` assumes `order.quantity` is always in Dollars (float). While likely correct for legacy compatibility, strictly typed systems should ideally verify if the Order has a `monetary_amount` field (from `CanonicalOrderDTO`) before falling back to this heuristic.

## 💡 Suggestions
*   **Cleanup**: Remove the "thinking aloud" comments in `simulation/bank.py` to maintain code professionalism.
*   **Validation**: In `LoanBookingEngine`, ensure that passing `quantity=application.amount_pennies` (e.g., 50000) and `price=1.0` to the `Transaction` object is semantically intended for "Credit Creation" items. It implies 50,000 units of credit at $1/unit, which balances correctly ($50,000 value), but differs from the "Quantity = 1, Price = Amount" pattern used elsewhere. Consistency here aids future auditing.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: The insight report `MISSION_finance_api_dto.md` correctly identifies the "DTO Consolidation" and "Integer Pennies Standard" as key architectural wins. It also transparently notes the "Regression Analysis" regarding `ImportError` fixes.
*   **Reviewer Evaluation**: The report is accurate and reflects the actual changes. The "Test Evidence" section provides confidence in the refactoring's stability.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
### ID: TD-FIN-FLOAT-CLEANUP
- **Title**: Legacy Float Cleanup (Finance)
- **Symptom**: Core finance engines previously relied on floating-point DTOs (`LoanInfoDTO`), risking precision errors.
- **Risk**: Financial drift over long-running simulations.
- **Solution**: Refactored `FinanceSystem`, `Bank`, and `Government` to use `LoanDTO` and `int` pennies exclusively.
- **Status**: RESOLVED (Mission: Finance API Realignment)
```

## ✅ Verdict
**APPROVE**

The PR successfully enforces the Penny Standard across the critical Finance domain without introducing visible security or logic regressions. The cleanup suggestions are minor and do not block the merge. The inclusion of `MISSION_finance_api_dto.md` satisfies the protocol requirements.