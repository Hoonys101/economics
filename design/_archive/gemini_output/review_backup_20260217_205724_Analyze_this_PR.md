# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**. 
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

## 🏗️ Audit Report: `feature/lifecycle-decomposition`

### 1. 🔍 Summary
This PR decomposes the monolithic `AgentLifecycleManager` into three distinct, single-responsibility systems: `AgingSystem`, `BirthSystem`, and `DeathSystem`. This directly addresses the `TD-ARCH-LIFE-GOD` technical debt. Key improvements include Protocol-driven interfaces (`ILifecycleSubsystem`) and explicit, zero-sum compliant asset transfers during agent birth.

### 2. 🚨 Critical Issues
*   None. No hardcoding or security violations found.

### 3. ⚠️ Logic & Spec Gaps
*   **Potential DTO Attribute Missing**: In `AgingSystem._process_firm_lifecycle`, the code sets `firm.finance_state.is_distressed = True`.
    *   **Risk**: If `FirmFinanceStateDTO` (or equivalent) does not explicitly define `is_distressed` and `distress_tick_counter` fields, this will raise an `AttributeError` at runtime (frozen dataclass) or mask the state change (if not persisted). The unit tests pass because they use `MagicMock` which accepts dynamic attribute assignment, masking this potential schema mismatch.
    *   **Mitigation**: Ensure the DTO definition includes these fields.

### 4. 💡 Suggestions
*   **Explicit DTO Verification**: Add a test case that uses the *real* `FirmStateDTO` (or `FirmFinanceState`) instead of a Mock to verify that `is_distressed` is a valid field.
*   **Mock Strictness**: In `tests/unit/systems/lifecycle/test_aging_system.py`, prefer using `MagicMock(spec=Firm)` or `spec=FirmStateDTO` to catch attribute errors during testing.

### 5. 🧠 Implementation Insight Evaluation

*   **Original Insight**:
    > **Decomposition of God Class**: The `AgentLifecycleManager` has been decomposed into three distinct subsystems...
    > **Financial Integrity**: The `BirthSystem` now explicitly handles the "birth gift" asset transfer via `SettlementSystem`...
    > **Risks**: Mock Drift... Tests rely on `MagicMock`.

*   **Reviewer Evaluation**:
    *   **Relevance**: The insight accurately captures the architectural shift and correctly identifies "Mock Drift" as the primary risk, which matches my observation in the "Logic & Spec Gaps" section.
    *   **Quality**: High. The explicit mention of the "Birth Gift" moving to `SettlementSystem` highlights a significant improvement in financial auditability.

### 6. 📚 Manual Update Proposal (Draft)

*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    (Update the status of `TD-ARCH-LIFE-GOD` from `Identified` to `Resolved`)

```markdown
| **TD-ARCH-LIFE-GOD** | Systems | **God Manager**: `LifecycleManager` monolithically handles Birth, Death, Aging, Liquidation. | **Medium**: Coupling. | **Resolved** |
```

### 7. ✅ Verdict
**APPROVE**

The decomposition is clean, follows the SEO pattern, and improves financial integrity. The Mock Drift risk is noted and acceptable given the scope of this refactor, provided integration tests are monitored.