🕵️  Generating Report for: '# ⚖️ Domain Auditor: Finance & Monetary Integrity

## Identity
You are the **Financial Integrity Auditor**. Your focus is on the flow of money, credit creation, and transactional atomicity.

## Mission
Verify that financial operations (loans, interest, tax) are perfectly zero-sum and that the `SettlementSystem` remains the SSoT for state changes.

## Audit Checklist (SoC focus)
1. **Monetary SSoT**: Do modules mutate `cash` or `assets` directly, or do they go through the `SettlementSystem`?
2. **Transaction Atomicity**: In Sagas, is the monetary leg completed *only* after all business rules are satisfied?
3. **Credit Risk**: Check if the `BankService` or `CentralBank` are creating "ghost money" not tracked by the `trace_leak.py` logic.
4. **DTO Purity**: Ensure financial snapshots are immutable.

## Output Format
### 🚥 Domain Grade: [PASS/FAIL/WARNING]
### ❌ Violations
| File | Line | Violation | Severity |
| :--- | :--- | :--- | :--- |
### 💡 Abstracted Feedback (For Management)
Provide a 3-bullet summary of the most critical structural drift found.


[TASK]
Run this audit on the provided context files and output the result.'...
📖 Attached context: simulation\api.py
📖 Attached context: simulation\agents\central_bank.py
📖 Attached context: simulation\systems\settlement_system.py
📖 Attached context: design\1_governance\architecture\ARCH_TRANSACTIONS.md
🚀 [GeminiWorker] Running task with manual: report.md

✅ Report Saved: C:\coding\economics\reports\temp\report_20260222_213555_Domain_Auditor.md
============================================================
# ⚖️ Domain Auditor: Finance & Monetary Integrity

## 🚥 Domain Grade: ⚠️ WARNING

The system demonstrates a sophisticated understanding of financial integrity, particularly through the use of an atomic **LedgerEngine** and a **Zero-Float Mandate**. However, there is a technical drift in how "Money Creation" (Minting) is handled compared to standard "Zero-Sum" transfers, potentially creating an audit gap in the automated ledger.

---

## ❌ Violations

| File | Line | Violation | Severity |
| :---
...
============================================================
