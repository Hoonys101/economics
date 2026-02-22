# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**.
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

## 🏗️ Code Review Report

### 1. 🔍 Summary
This PR implements **Atomic FX Swaps** (`execute_swap`) within the `SettlementSystem`, enabling multi-currency barter capabilities. It leverages the existing `LedgerEngine.process_batch` to ensure that both legs of the swap (A→B and B→A) execute successfully or roll back together. Comprehensive unit tests covering success, insufficient funds (atomic rollback), and validation edge cases are included.

### 2. 🚨 Critical Issues
*   None identified. The implementation adheres to the "Penny Standard" and Zero-Sum principles.

### 3. ⚠️ Logic & Spec Gaps
*   None identified. The implementation aligns with the `ISettlementSystem` protocol and correctly handles the atomic requirement via batch processing.

### 4. 💡 Suggestions
*   **Refactoring Capability**: The pre-flight check (`_prepare_seamless_funds`) is a good optimization, but ensure it doesn't drift from the actual engine logic in `process_batch`. Currently, they seem synchronized.
*   **Architecture**: As noted in your insights, `SettlementSystem` is taking on too many responsibilities (Indexing, Metrics, Transaction Orchestration). Prioritize the extraction of `BankRegistry` logic in the next refactoring cycle.

### 5. 🧠 Implementation Insight Evaluation

*   **Original Insight**:
    > "SettlementSystem Complexity: SettlementSystem is growing large. While it delegates to LedgerEngine, it still contains logic for bank indices (`_bank_depositors`), metrics recording, and legacy `create_transaction_record`. Future refactoring might consider extracting the bank index logic to a dedicated `BankRegistry` or `AccountManager`."

*   **Reviewer Evaluation**:
    *   **Valid & High Value**: This is a crucial architectural observation. The `SettlementSystem` is approaching "God Class" status for financial operations.
    *   **Actionable**: The suggestion to extract `BankRegistry` is concrete and aligns with the Single Responsibility Principle (SRP). This should be formally tracked as technical debt.

### 6. 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
### ID: TD-ARCH-SETTLEMENT-BLOAT
- **Title**: SettlementSystem Responsibility Overload
- **Symptom**: `SettlementSystem` currently handles transaction orchestration, ledger delegation, internal bank indexing (`_bank_depositors`), and metrics recording.
- **Risk**: High coupling makes future FX/Market expansions (like multi-hop swaps) difficult to test and maintain.
- **Solution**: Extract `BankRegistry` logic and `MetricsRecording` into dedicated services; keep `SettlementSystem` purely focused on transaction orchestration.
- **Status**: Identified (Phase 4.1)
```

### 7. ✅ Verdict
**APPROVE**

The code is secure, logically sound, and well-tested. The inclusion of `process_batch` ensures atomicity for swaps, preventing "half-completed" trades which would violate Zero-Sum integrity. The Insight Report accurately identifies the growing complexity risk.