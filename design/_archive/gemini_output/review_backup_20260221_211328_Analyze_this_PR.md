# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR refactors the financial transaction architecture by renaming the low-level `TransactionEngine` to `LedgerEngine` and introducing a new, high-level `TransactionEngine` that employs the **Registry Pattern**. It implements specialized `ITransactionHandler`s for `BAILOUT`, `BOND_ISSUANCE`, and `TRANSFER` types, effectively decoupling business logic from core ledger mechanics.

## 🚨 Critical Issues
*None detected.*

## ⚠️ Logic & Spec Gaps
*None detected.* The implementation aligns well with the `TD-RUNTIME-TX-HANDLER` resolution plan. The `BondIssuanceHandler` includes application-level compensation (rollback) logic to prevent money trapping if asset creation fails, which adheres to the integrity requirements.

## 💡 Suggestions
*   **Bond Issuance Rollback Robustness**: The rollback in `BondIssuanceHandler` (`source_account_id=str(request.issuer_id)`) assumes the issuer still has the funds immediately after the credit. While valid for this synchronous operation, ensure that `bond_market_system.issue_bond` does not trigger any side-effects that might instantly sweep those funds (e.g., an auto-debt-repayment hook) before the rollback can occur.

## 🧠 Implementation Insight Evaluation

*   **Original Insight**:
    > "This mission addressed the "Technical Debt: Runtime Transaction Handler" by introducing a Registry-based Transaction Engine and specialized handlers for complex financial operations. Key Decisions: Engine Separation... High-Level Transaction Engine... Specialized Handlers."

*   **Reviewer Evaluation**:
    The insight accurately captures the architectural shift. The distinction between "Ledger" (Mechanism) and "Transaction" (Business Logic) is a crucial maturity step for the system. The use of the Registry Pattern allows for OCP (Open-Closed Principle) adherence when adding future transaction types like `MERGER` or `ACQUISITION`.

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

**Draft Content**:
```markdown
### ID: TD-RUNTIME-TX-HANDLER
- **Title**: Missing Transaction Handlers
- **Symptom**: `bailout`, `bond_issuance` tx types not registered.
- **Risk**: Runtime Failure.
- **Solution**: Register all transaction types with the `TransactionEngine`.
- **Status**: **RESOLVED**
```

## ✅ Verdict
**APPROVE**