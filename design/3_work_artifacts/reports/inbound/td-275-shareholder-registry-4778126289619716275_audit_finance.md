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
📖 Attached context: simulation\finance\api.py
⚠️ Context file not found or is not a file: simulation\monetary\central_bank.py
⚠️ Context file not found or is not a file: simulation\finance\settlement_system.py
⚠️ Context file not found or is not a file: design\1_governance\architecture\ARCH_FINANCE.md
🚀 [GeminiWorker] Running task with manual: reporter.md

✅ Report Saved: C:\coding\economics\reports\temp\report_20260206_230711_Domain_Auditor.md
============================================================
# ⚖️ Domain Auditor: Finance & Monetary Integrity

### 🚥 Domain Grade: PASS
The provided API design strictly adheres to the principles of financial integrity by centralizing all monetary state changes and clearly defining operations for money creation, destruction, and transfer.

### ❌ Violations
| File | Line | Violation | Severity |
| :--- | :--- | :--- | :--- |
| N/A | N/A | No violations found in the provided API definition. | N/A |

### 💡 Abstracted Feedback (For Management)
*   **Centraliz
...
============================================================