# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR standardizes System Agent IDs to a fixed integer range (0-5), replacing the previous mix of strings and magic numbers. It refactors `AgentRegistry` to use `sim.agents` as the strict Single Source of Truth (SSoT) and updates `SimulationInitializer` to explicitly register all system agents (Central Bank, Government, Bank, Escrow, Public Manager) at startup. It also corrects the initialization order of the registry state.

## 🚨 Critical Issues
*   None found. Security and zero-sum constraints appear respected.

## ⚠️ Logic & Spec Gaps
*   **Magic Number Retention**: In `simulation/systems/transaction_processor.py`, the legacy magic numbers `999999` and `-1` are retained in `is_pm_seller`:
    ```python
    is_pm_seller = (
        tx.seller_id == ID_PUBLIC_MANAGER
        or tx.seller_id == "PUBLIC_MANAGER"
        or tx.seller_id == 999999  # Legacy Magic Number
        or tx.seller_id == -1      # Legacy Magic Number
    )
    ```
    While this provides backward compatibility during the transition, it leaves dead code/magic numbers in a core processor. Ideally, if all agents are reset, these should be removed to enforce the new standard.

## 💡 Suggestions
*   **Cleanup**: Remove `999999` and `-1` from `TransactionProcessor` once the migration is confirmed stable.
*   **Consistency**: `ID_SYSTEM` is defined as `5` but not explicitly used in the `SimulationInitializer` diff shown (though it might be used internally by `TaxationSystem` etc.). Ensure any "System" logic uses this constant.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: Jules noted addressing `TD-ARCH-DI-SETTLE` and standardizing IDs. Verified `AgentRegistry` purity and M2 integrity.
*   **Reviewer Evaluation**: The insight is high quality and backed by strong verification scripts (`verify_sys_registry.py`, `verify_m2_integrity.py`).
    *   **Correction**: While Jules mentions `TD-ARCH-DI-SETTLE`, the provided context suggests this PR most directly resolves **`TD-CRIT-SYS0-MISSING`** (Central Bank not in Registry) and **`TD-CRIT-PM-MISSING`** (Public Manager not in Registry), which were flagged as critical open items. The report should ideally claim credit for these specific closures.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
| **TD-CRIT-SYS0-MISSING** | Systems | **Missing Account 0**: Central Bank not in Registry. | **Critical**: Reliability. | **RESOLVED** |
| **TD-CRIT-PM-MISSING** | Systems | **Missing PM**: Public Manager not in Registry. | **Critical**: Liquidation. | **RESOLVED** |
```

## ✅ Verdict
**APPROVE**

The PR achieves its core mission of standardizing system IDs and populating the registry correctly. The retention of legacy magic numbers is a minor code hygiene issue but does not block the architectural improvement or violate security. The verification evidence is sufficient.