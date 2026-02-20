# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**.
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

## 📝 Code Review Report

### 1. 🔍 Summary
This PR implements a critical **Atomic Lifecycle Scrubbing** mechanism to resolve "orphaned asset" leaks during agent death. It updates `DeathSystem` to recover bank deposits via `SettlementSystem` transfers before closing accounts, and enhances `InheritanceManager` to perform explicit debt repayment transactions. New protocols (`close_account`, `repay_loan`, `get_agent_banks`) are added to `IBank` and `ISettlementSystem` to support this zero-sum compliant cleanup.

### 2. 🚨 Critical Issues
*   None. No hardcoded secrets or absolute paths detected.

### 3. ⚠️ Logic & Spec Gaps
*   **Minor Handling of Bank Reference**: In `simulation/systems/inheritance_manager.py`, the code uses `getattr(simulation, 'bank', None)`. While functional, relying on the god-object `simulation.bank` attribute is less robust than injecting `IBankService`. Ensure `simulation` object always has `bank` initialized before `InheritanceManager` runs.
*   **Fallback Logic in Handler**: In `simulation/systems/handlers/financial_handler.py`, the fallback `elif hasattr(context, 'bank')` assumes `context` has a `bank` attribute. If `FinancialTransactionHandler` is used in a context without a bank (e.g., peer-to-peer debt), this might be skipped, though acceptable for the current scope where loans are centralized.

### 4. 💡 Suggestions
*   **Refinement**: The `_recover_external_assets` logic in `DeathSystem` is robust. Consider moving the "Find Banks -> Recover -> Close" sequence into a dedicated `AssetRecoveryService` in the future if other external asset types (e.g., Staking, Bonds) are added.

### 5. 🧠 Implementation Insight Evaluation
*   **Original Insight**: *"`DeathSystem` now queries `SettlementSystem.get_agent_banks` and calls `Bank.close_account` to sweep all deposits... ensuring strict protocol compliance."*
*   **Reviewer Evaluation**: **High Value**. The insight correctly identifies a systemic "M2 Leak" (orphaned deposits) and a "Ghost Ledger" issue (dead agents remaining in bank books). The solution enforces Zero-Sum integrity by using `SettlementSystem.transfer` (preserving money supply) rather than just deleting the numbers.

### 6. 📚 Manual Update Proposal (Draft)

*   **Target File**: `design/1_governance/architecture/standards/LIFECYCLE_HYGIENE.md`
*   **Draft Content**:

```markdown
### 3. External Asset Scrubbing (Post-Mortem Recovery)
- **Scope**: Upon agent death or liquidation, ALL assets held by third parties (e.g., Bank Deposits, Stock Portfolio) MUST be recovered to the agent's primary wallet *before* final distribution/destruction.
- **Protocol**:
  1. **Identify**: Query registries (e.g., `SettlementSystem.get_agent_banks`) to find external holdings.
  2. **Recover**: Execute `SettlementSystem.transfer` to move funds to the agent (Realization).
  3. **Close**: Call the external entity's closure method (e.g., `Bank.close_account`) to remove ledger records.
- **Prohibition**: Simply deleting the agent ID from the bank's ledger without transferring funds ("Writing off") is a **Zero-Sum Violation** (Money Destruction).
```

### 7. ✅ Verdict
**APPROVE**

The changes robustly address the lifecycle asset leakage issue. The logic adheres to the Zero-Sum/Penny Standard by ensuring funds are moved via `SettlementSystem` before accounts are closed. Tests are comprehensive and cover the new logic. The insight report is present and accurate.