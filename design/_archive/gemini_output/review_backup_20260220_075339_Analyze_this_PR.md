# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR addresses **Agent Lifecycle Atomicity** by implementing a "cancel-first" strategy during agent liquidation. It standardizes the `IMarket` protocol with a `cancel_orders` method and updates `OrderBookMarket` and `StockMarket` to comply. This ensures that when an agent dies, their pending orders are immediately scrubbed to prevent "zombie trading" or race conditions during the settlement phase.

## 🚨 Critical Issues
*   **Repository Hygiene (`check_isinstance.py`)**:
    *   The file `check_isinstance.py` appears to be a temporary manual test script.
    *   **Action**: Please **delete this file** from the PR before merging. We should not commit throwaway scripts to the main branch.

## ⚠️ Logic & Spec Gaps
*   **None identified**: The logic for `cancel_orders` in both `OrderBookMarket` and `StockMarket` appears sound, correctly iterating through order books and filtering out orders belonging to the target `agent_id`. The defensive coding in `StockMarket` (`str(id) != str(id)`) handles potential type mismatches (int vs str) effectively.

## 💡 Suggestions
*   **Refactoring**: In `simulation/systems/lifecycle/death_system.py`, the `try...except` block inside `_cancel_agent_orders` catches generic `Exception`. While acceptable for a cleanup routine (to ensure death execution doesn't hang), consider logging the specific exception type if possible for better debugging in the future.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "Protocol Purity Enforcement: The DeathSystem now strictly checks for isinstance(market, IMarket)... StockMarket Compliance: The StockMarket class was found to be technically non-compliant... Atomicity Strategy: Order cancellation is now the first step..."
*   **Reviewer Evaluation**:
    *   **High Value**: The insight accurately captures the architectural shift towards strict Protocol adherence (`@runtime_checkable`).
    *   **Relevance**: Identifying `StockMarket`'s non-compliance (missing `matched_transactions`) is a crucial fix that prevents hidden runtime errors. The explanation of the "Atomicity Strategy" provides clear rationale for the sequence change in `DeathSystem`.

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
| **TD-SYS-QUEUE-SCRUB** | Lifecycle | **Lifecycle Queue Scrubbing**: AgentLifecycleManager fails to remove stale IDs from queues. (Partial Fix: Market orders are now scrubbed via `fix-agent-lifecycle-atomicity`). | **High**: Logic Leak. | **In Progress** |
```

## ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

The logic and architectural changes are **Excellent**, but the inclusion of the temporary script `check_isinstance.py` requires cleanup. Please remove this file and update the PR.

1.  **Delete**: `check_isinstance.py`
2.  **Verify**: Tests pass.

Once the file is removed, this is ready to merge.