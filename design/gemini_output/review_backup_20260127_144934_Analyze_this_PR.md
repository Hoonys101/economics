# 🔍 Git Diff Review: Fractional Reserve Banking

---

### 1. 🔍 Summary
This Pull Request fundamentally overhauls the banking system by implementing a fractional reserve model. Banks now create new money (endogenous money) when granting loans, rather than lending from existing funds. This is a significant and realistic architectural shift, supported by a new `CreditScoringService` to manage risk.

### 2. 🚨 Critical Issues

1.  **[CRITICAL] Money Leak in `void_loan` Method**
    -   **File**: `simulation/bank.py`
    -   **Method**: `void_loan`
    -   **Problem**: If the system attempts to roll back a loan and cannot find the *exact* deposit to delete, it logs a warning and then `pass`-es. However, it still proceeds to delete the loan asset (`del self.loans[loan_id]`) and reduce the total money supply (`self.government.total_money_issued -= amount`).
    -   **Impact**: The deposit (a liability for the bank) remains on the books while the corresponding asset (the loan) is removed. This breaks the bank's balance sheet. More importantly, the system's tracked money supply decreases, but the actual money (the deposit) still exists, creating a **system-wide money leak**.
    -   **Fix**: The `else: pass` block must be replaced. The operation should either raise a critical error or implement a more robust fallback to find and reduce the borrower's total deposit balance by the loan amount. The liability **must** be reversed.

2.  **[CRITICAL] Duplicate Code File**
    -   **File**: `simulation/bank_void_method.py`
    -   **Problem**: This new file is a complete duplicate of the `void_loan` method already implemented in `simulation/bank.py`.
    -   **Impact**: This introduces redundant code, which will lead to maintenance issues and confusion.
    -   **Fix**: The file `simulation/bank_void_method.py` must be deleted.

### 3. ⚠️ Logic & Spec Gaps

1.  **Brittle Deposit Rollback Mechanism**
    -   **File**: `simulation/bank.py`
    -   **Method**: `void_loan`
    -   **Problem**: The logic to find the deposit to reverse (`for dep_id, deposit in self.deposits.items(): ...`) relies on matching the borrower ID and the exact loan amount. This is brittle. If the borrower performs any other transaction between the loan creation and the rollback, this search could fail or target the wrong deposit.
    -   **Impact**: This increases the risk of triggering the critical issue mentioned above.

### 4. 💡 Suggestions

1.  **Robust Loan-Deposit Linking**
    -   To fix the brittle rollback mechanism, consider linking the loan directly to the deposit it creates. When a `Loan` is created, store the ID of the new `Deposit` object within the `Loan` object itself (e.g., `new_loan.created_deposit_id = ...`).
    -   This would allow the `void_loan` method to precisely and reliably target the correct deposit for deletion without any searching.

2.  **Refine Zero-Income DTI Logic**
    -   **File**: `modules/finance/credit_scoring.py`
    -   **Method**: `assess_creditworthiness`
    -   **Suggestion**: The logic for handling zero-income applicants is functionally correct but complex (`dti = float('inf')` followed by `dti = 0.0`). This could be simplified. A clearer approach would be to have a dedicated check at the beginning: if `gross_income` is 0, any loan request for more than 0 without sufficient collateral is likely to be rejected. The current logic achieves this through the "Unsecured Cap" check, but simplifying the DTI calculation itself would improve readability.

### 5. 🧠 Manual Update Proposal
-   **Target File**: `design/manuals/ECONOMIC_INSIGHTS.md`
-   **Update Content**: The proposed addition explaining "Fractional Reserve Banking & Endogenous Money" is **excellent**. It is clear, accurate, and perfectly captures the essence of the architectural change. This should be merged as-is.

---

### 6. ✅ Verdict

**REQUEST CHANGES**

This is a well-structured and important feature. However, the critical money leak bug in the `void_loan` method is a blocker for any economic simulation. The system's integrity relies on fixing this zero-sum violation. Once the critical issues are resolved, this will be a fantastic addition to the project.
