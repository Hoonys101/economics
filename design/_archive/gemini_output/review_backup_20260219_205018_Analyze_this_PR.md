# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**. 
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

# 🔍 Code Review Report

## 🔍 Summary
This PR resolves a regression in `Government` agent's fiscal decision logic where a raw dictionary was passed to the `FiscalEngine` instead of the required `MarketSnapshotDTO` dataclass. It harmonizes the imports in `government/engines/api.py` to use the strictly typed Dataclass from `modules.system.api`.

## 🚨 Critical Issues
*   None.

## ⚠️ Logic & Spec Gaps
*   None. The fix correctly aligns the caller (`Government`) with the callee's (`FiscalEngine`) type expectations (Dataclass attribute access).

## 💡 Suggestions
*   **Refactoring**: The insight correctly identifies that `MarketSnapshotDTO` seems to exist as a `TypedDict` in `finance` and a `dataclass` in `system`. This dual definition is a trap for future developers. I have added a Tech Debt item below to track unifying this.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: "DTO Instantiation Regression: The regression was caused by `Government.provide_firm_bailout` passing a raw dictionary instead of a `MarketSnapshotDTO` dataclass... Protocol Definition Mismatch... mixing TypedDicts and Dataclasses for the same concept... creates fragility."
*   **Reviewer Evaluation**: **High Value**. The insight accurately pinpoints the root cause (Python's runtime type confusion between `dict` and `object` attribute access) and correctly identifies the structural issue (ambiguous DTO definitions across modules).

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
| **TD-ARCH-DTO-ALIAS** | Architecture | **DTO Ambiguity**: `MarketSnapshotDTO` exists as both TypedDict (Finance) and Dataclass (System), causing integration regressions. | **Medium**: Runtime Crash. | **Identified** |

---
### ID: TD-ARCH-DTO-ALIAS
### Title: MarketSnapshotDTO Definition Conflict
- **Symptom**: `Government` agent crashed because it passed a dict (matching Finance's TypedDict) to an engine expecting System's Dataclass.
- **Risk**: Duck-typing works until attribute access (`.attr`) is used instead of subscription (`['attr']`).
- **Solution**: Standardize on `modules.system.api.MarketSnapshotDTO` (Dataclass) globally. Remove local TypedDict definitions in Finance module.
```

## ✅ Verdict
**APPROVE**

The fix is chemically pure, enforces type safety, and is backed by a valid reproduction test and insight report.