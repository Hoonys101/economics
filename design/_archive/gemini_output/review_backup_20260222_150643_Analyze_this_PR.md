# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**. 
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

# 🛡️ Gemini Code Review Report

## 🔍 Summary
This PR implements **Strict DTO Hygiene** across the system, specifically targeting `MarketContextDTO` and `SimulationState`. It replaces loose dictionary usage with strict Dataclass attribute access (`.exchange_rates` vs `.get()`), forcing compile-time safety. Crucially, it hardens unit tests by applying `spec=SimulationState` to mocks, exposing and fixing hidden "Mock Drift" where tests were passing despite missing attributes.

## 🚨 Critical Issues
*   None found. Security and Hardcoding checks passed.

## ⚠️ Logic & Spec Gaps
*   **None Identified**: The changes align perfectly with the `TESTING_STABILITY.md` standard (Strict Mocking) and the goal of eliminating DTO drift.

## 💡 Suggestions
*   **Future Hardening**: Consider making `MarketContextDTO` frozen (`@dataclass(frozen=True)`) in a future iteration to enforce immutability strictly, although the current `field(default_factory=...)` usage suggests it might be constructed piece-wise in some legacy paths.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: *Phase 4.1: DTO Test Hygiene Implementation Report* (New File)
    *   "Strict Mocking Exposed Hidden Bugs: Enforcing `spec=SimulationState` in `TransactionProcessor` tests revealed that the DTO definition was incomplete compared to actual usage."
*   **Reviewer Evaluation**: **High Value**. The insight correctly identifies "Mock Drift" as a silent killer of test value. The remediation (adding missing fields to DTOs and enforcing `spec` in tests) is the textbook solution. The report provides clear evidence of the regression fixes (FinanceEngine attribute access).

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    *   *Update the status of TD-TEST-DTO-MOCK to RESOLVED.*

```markdown
| **TD-TEST-DTO-MOCK** | Testing | **DTO Hygiene**: `tests/test_firm_brain_scan.py` uses permissive `MagicMock` for DTOs. | **Low**: Stability. | **RESOLVED (PH4.1)** |
```

## ✅ Verdict
**APPROVE**

The PR significantly improves codebase stability by enforcing strict typing contracts between Agents, Engines, and Tests. The transition from dictionary-based access to strict DTO property access eliminates a whole class of potential `AttributeError`/`KeyError` runtime bugs.