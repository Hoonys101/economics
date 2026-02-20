🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached context: C:\coding\economics\design\_archive\gemini_output\pr_diff_phase4-ai-lifecycle-scrubbing-16535408055983162538.txt
📖 Attached context: design\1_governance\architecture\standards\LIFECYCLE_HYGIENE.md
📖 Attached context: design\1_governance\architecture\ARCH_TRANSACTIONS.md
📖 Attached context: design\1_governance\architecture\ARCH_TESTS.md
📖 Attached context: design\1_governance\architecture\ARCH_AGENTS.md
📖 Attached context: design\1_governance\architecture\standards\FINANCIAL_INTEGRITY.md
📖 Attached context: design\1_governance\architecture\ARCH_SEQUENCING.md
📖 Attached context: design\1_governance\architecture\standards\TESTING_STABILITY.md
📖 Attached context: design\1_governance\architecture\standards\INDEX.md
📖 Attached context: modules\finance\dtos.py
📖 Attached context: modules\household\dtos.py
📖 Attached context: modules\system\api.py
📖 Attached context: modules\finance\api.py
📖 Attached context: simulation\dtos\api.py
📖 Attached context: modules\household\api.py
📖 Attached context: design\2_operations\ledgers\TECH_DEBT_LEDGER.md
🚀 [GeminiWorker] Running task with manual: git-review.md

📝 [Review Report]
============================================================
# 🐙 Gemini CLI Code Review Report

## 🔍 Summary
This PR implements **Phase 4.1: Lifecycle Scrubbing**, introducing an atomic cleanup process for dying agents (`DeathSystem`). Key features include recovering bank deposits (`close_account`) and enforcing debt repayment (`repay_loan`) during inheritance and liquidation. It also expands the `FinanceSystem` and `SettlementSystem` protocols to support these ledger operations.

## 🚨 Critical Issues

### 1. 💸 Money Creation & Integrity Violation (Zero-Sum Breach)
- **File**: `simulation/systems/lifecycle/death_system.py`
- **Location**: `_recover_external_assets` method (Lines ~164-168)
- **Violation**: The code directly calls `agent.deposit(amount)` after closing the bank account.
    ```python
    amount = bank.close_account(agent_id) # 1. Removes Liability from Bank Ledger
    if amount > 0:
        agent.deposit(amount)             # 2. Creates New Cash (M0) in Agent Wallet
    ```
- **Why this is a Fail**:
    - **Magic Money**: The `Bank` entity retains the physical cash (Asset) that backed the deposit, while the `Agent` gets *newly created* cash. Total system M0 increases by `amount`.
    - **Standard Violation**: Explicit violation of [FINANCIAL_INTEGRITY.md](../design/1_governance/architecture/standards/FINANCIAL_INTEGRITY.md) Rule #3 ("No Direct Mutation... Mandatory System Call").
- **Required Fix**: You **MUST** use `self.settlement_system.transfer(bank, agent, amount, ...)` instead of `agent.deposit()`. This ensures the Bank's cash holdings decrease as the Agent's increase.

## ⚠️ Logic & Spec Gaps

### 1. `InheritanceManager` Global State Access
- **File**: `simulation/systems/inheritance_manager.py`
- **Location**: Line ~75 `bank = getattr(simulation, 'bank', None)`
- **Issue**: Accessing `simulation` global object (God Object pattern) inside a system method is fragile.
- **Suggestion**: Ensure `simulation` or `state` is properly passed to `distribute_assets` or that `Bank` is resolved via `state.agents`.

## 💡 Suggestions

1.  **Bank Liquidity Check**: When converting deposits to cash via `SettlementSystem.transfer`, there is a theoretical risk the Bank doesn't have enough liquid cash (Reserves). While unlikely in current simulation parameters, consider wrapping the transfer in a `try-except` block or handling `SETTLEMENT_FAIL` if the bank is insolvent.

## 🧠 Implementation Insight Evaluation

-   **Original Insight**: *Phase 4.1: Lifecycle Scrubbing & Atomic Cleanup*
    -   "Recover: DeathSystem now queries... and calls Bank.close_account to sweep all deposits into the agent's wallet..."
-   **Reviewer Evaluation**: The insight correctly identifies the *need* for atomic cleanup ("External Assets... were not atomically settled"). However, it failed to identify that "sweeping into wallet" requires a **Settlement Transfer**, not just a ledger update. The insight is valuable but the implementation deviated from the "Zero-Sum Integrity" it claims to enforce.

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/1_governance/architecture/standards/LIFECYCLE_HYGIENE.md`

```markdown
### 3. Solvency Scrubbing Protocol (Phase 4.1)
- **External Asset Recovery**: Before an agent is liquidated, all external assets (e.g., Bank Deposits) MUST be converted to cash via `SettlementSystem.transfer`. Merely deleting the ledger entry and inflating the agent's wallet is a **Zero-Sum Violation**.
- **Debt-Ledger Sync**: Loan repayments during liquidation MUST trigger both the `SettlementSystem` (Cash Transfer) and `FinanceSystem` (Ledger Update) to ensure the `FinancialLedger` remains consistent with actual asset holdings.
```

## ✅ Verdict

**REQUEST CHANGES (Hard-Fail)**

The PR introduces a **Critical Zero-Sum Violation** in `DeathSystem._recover_external_assets` by bypassing the Settlement System and effectively printing money. This must be fixed before merging.
============================================================
✅ Review Saved: C:\coding\economics\design\_archive\gemini_output\review_backup_20260220_164746_Analyze_this_PR.md
