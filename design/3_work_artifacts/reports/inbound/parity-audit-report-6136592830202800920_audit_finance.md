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
🚀 [GeminiWorker] Running task with manual: reporter.md

✅ Report Saved: C:\coding\economics\reports\temp\report_20260207_193143_Domain_Auditor.md
============================================================
# ⚖️ Financial Integrity Audit Report

### 🚥 Domain Grade: WARNING

### ❌ Violations
| File | Line | Violation | Severity |
| :--- | :--- | :--- | :--- |
| `simulation\systems\settlement_system.py` | 76-79 | Monetary SSoT | Minor |

### 💡 Abstracted Feedback (For Management)
*   The system correctly enforces atomic transactions with robust rollback logic, preventing value loss during failed multi-party or standard transfers.
*   Non-zero-sum operations (money creation/destruction) are properly i
...
============================================================