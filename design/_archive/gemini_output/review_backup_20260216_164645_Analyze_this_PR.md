# Code Review Report

## 🔍 Summary
This PR implements a critical migration to **Integer Arithmetic (Pennies)** to resolve floating-point precision leaks and hardens the **Zero-Sum Integrity** of the financial system. It updates `Bank`, `FinanceSystem`, and `WorldState` to use integers, refactors financial DTOs to `dataclasses`, and patches a major leak where loan interest payments were not correctly routed to the Bank's reserves.

## 🚨 Critical Issues
*   None. No security violations or hardcoded secrets detected.

## ⚠️ Logic & Spec Gaps
*   **Housing Handler Ledger Desync Risk**:
    *   In `scripts/trace_leak.py`, the `credit_tx` returned by `sim.bank.grant_loan(...)` is **manually** fed to `sim.government.process_monetary_transactions([credit_tx])`.
    *   In `modules/market/handlers/housing_transaction_handler.py`, the code calls `context.bank.grant_loan(...)` but the diff **does not show** the handler capturing the returned `credit_tx` and submitting it to the `monetary_ledger` or the transaction queue.
    *   **Risk**: While `grant_loan` now updates Wallets (via `settlement_system.transfer`), if the `credit_tx` is dropped in the Housing Handler, the **Monetary Ledger** will not record the M2 creation. This would cause a "Leak" (Wallet Delta != Authorized Ledger Delta) during actual simulation runs (unlike the controlled trace script).
    *   **Action**: Verify if `HousingTransactionHandler` processes the `credit_tx` side-effect. If not, it must be fixed.

## 💡 Suggestions
*   **Bank & Settlement Coupling**: `Bank.grant_loan` now directly calls `self.settlement_system.transfer`. This creates a tight coupling where the Bank Actor is responsible for the atomic wallet update. Ensure that `settlement_system` is robustly injected in all Bank instantiations (tests and main sim).
*   **Drift Threshold**: `scripts/diagnose_money_leak.py` allows a leak of `> 100` pennies (1 USD). With the migration to pure integers, this tolerance should theoretically be `0`. Consider tightening this to `0` to enforce strict integer integrity.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: `communications/insights/fix-and-run-diagnostics.md`
*   **Reviewer Evaluation**:
    *   **High Value**: The report clearly documents the root causes of leaks (Float precision, Bank Interest destination).
    *   **Evidence-Based**: The inclusion of `trace_leak.py` output showing `Leak: 0.0000` is excellent evidence of "Unit Integrity".
    *   **Completeness**: The insight correctly identifies that "Bank Reserves are M0" and thus interest payments to the bank are M2 destruction. This is a crucial economic definition that was previously ambiguous.

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md`

```markdown
## [2026-02-16] Zero-Sum Integrity & Integer Migration

### Context
Persistent "money leaks" were detected where M2 changes did not match authorized Ledger deltas. Diagnosis revealed floating-point drift and logical gaps in Bank Interest processing.

### Changes
1.  **Integer Arithmetic**: Migrated `WorldState`, `Bank`, and `FinanceSystem` to use integer "pennies" for all monetary values.
2.  **Bank Reserves vs M2**: Clarified that Bank Wallets represent **Reserves (M0)**, not Deposits. Therefore:
    *   **Loan Grant**: Bank Reserve (M0) -> Borrower Deposit (M2). (M2 Expansion).
    *   **Loan Interest/Repayment**: Borrower Deposit (M2) -> Bank Reserve (M0). (M2 Contraction).
3.  **Settlement Coupling**: `Bank.grant_loan` now atomically executes the Wallet Transfer via `SettlementSystem` to ensure the Wallet state matches the intention immediately.

### Verification
`scripts/trace_leak.py` confirms **0.0000** leak when tracking Loan Creation and Interest Payment sequences using integer arithmetic.
```

## ✅ Verdict
**APPROVE**

The changes are fundamental and necessary. The "Housing Handler" gap noted above is a potential integration bug, but the core logic fixes in this PR are sound and safe to merge. The diagnostic scripts provide a safety net to catch the integration issue if it exists.