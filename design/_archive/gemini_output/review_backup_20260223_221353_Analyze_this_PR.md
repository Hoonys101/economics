# 🐙 Gemini CLI System Prompt: Git Reviewer

## 📝 Code Review Report

### 🔍 Summary
This PR addresses critical M2 (Total Money Supply) leakage by implementing a **Transaction Injection Pattern** in the `CentralBankSystem` and `Government` agents. It harmonizes the M2 perimeter by explicitly excluding the Public Manager and System Agent from calculations. Additionally, it refines bond repayment logic to separate principal (contraction) from interest (transfer) in the `MonetaryLedger` and removes the redundant `Phase_MonetaryProcessing`.

### 🚨 Critical Issues
*   **Missing File / Interface Mismatch (`simulation/systems/settlement_system.py`)**:
    *   **Files**: `simulation/agents/government.py` (L594), `simulation/systems/central_bank_system.py` (L60).
    *   **Problem**: The updated code in `Government.execute_social_policy` and `CentralBankSystem.mint_and_transfer` now expects `self.settlement_system.transfer()` to return a `Transaction` object (checking `if tx:` and then `transactions.append(tx)`).
    *   **Evidence**: The PR Diff **does not include** changes to `simulation/systems/settlement_system.py`. If `SettlementSystem.transfer` still returns a `bool` (legacy behavior), `transactions.append(True)` will execute. This will cause an `AttributeError` downstream in `MonetaryLedger.process_transactions` when it attempts to access attributes like `tx.currency` on a boolean value.
    *   **Action Required**: Include `simulation/systems/settlement_system.py` in the PR, ensuring `transfer()` returns a `Transaction` object (or `None`), or modify the consumer code to handle the legacy boolean return type.

### ⚠️ Logic & Spec Gaps
*   **Bond Repayment Metadata Dependency**:
    *   **File**: `modules/government/components/monetary_ledger.py` (L84).
    *   **Issue**: The logic relies on `tx.metadata["repayment_details"]["principal"]`. While safe (falls back to full amount if missing), verify that `FiscalBondService` or the relevant handler is actually populating this metadata in this or a prior PR to ensure the "Split Repayment" feature functions as intended.

### 💡 Suggestions
*   **Explicit Type Hinting**: In `Government.execute_social_policy`, explicit type hinting for the `tx` variable (e.g., `tx: Optional[Transaction]`) would improve readability and tooling support, especially given the return type change.
*   **Hardcoded ID String in Test**: `tests/unit/modules/government/components/test_monetary_ledger_expansion.py` uses `tx.buyer_id = "4"` to represent `ID_PUBLIC_MANAGER`. While functional, it is better to import `ID_PUBLIC_MANAGER` from constants to ensure test resilience against ID changes.

### 🧠 Implementation Insight Evaluation
*   **Original Insight**: *WO-WAVE5-MONETARY-FIX: M2 Integrity & Audit Restoration* describes the "Ghost Money" issue caused by implicit LLR operations and the solution via dependency injection of the global transaction ledger.
*   **Reviewer Evaluation**: **High Value**. The insight accurately diagnoses a subtle distributed system consistency problem ("implicit operations not bubbling up"). The "Transaction Injection Pattern" is a pragmatic, albeit slightly "dirty" (bypassing event bus for list mutability), solution for ensuring strict atomic accounting in this specific architecture. The perimeter harmonization note is crucial for long-term auditability.

### 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    ```markdown
    ### [2026-02-23] Monetary Architecture: Transaction Injection Pattern
    - **Context**: Implicit financial operations (LLR, Tax) were modifying agent balances without generating visible `Transaction` records in the `WorldState`, leading to M2 audit failures (Ghost Money).
    - **Resolution**: Implemented dependency injection of `WorldState.transactions` (list) into `CentralBankSystem` and `Government` execution contexts.
    - **Pattern**: "Direct Ledger Injection". System Agents now directly append `Transaction` objects to the global ledger immediately upon settlement success, ensuring 1:1 atomicity between Balance Update and Ledger Record.
    - **Constraint**: `SettlementSystem.transfer` must now return the created `Transaction` object (or `None`) instead of a boolean to facilitate this capture.
    ```

### ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

The PR introduces code that depends on `SettlementSystem.transfer` returning a `Transaction` object, but the definition of that method (in `simulation/systems/settlement_system.py`) is missing from the diff. This is a likely runtime crash (AttributeError on boolean). Please add the missing file or revert the consumer logic.