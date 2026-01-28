# 🦅 Protocol: Governance & Administration

This protocol defines the roles, responsibilities, and administrative procedures for the Economics Simulation Project.

---

## 🏛️ 1. Project Roles
| Role | Entity | Responsibility |
|---|---|---|
| **PM** | User (Hoonys101) | Final decision making, vision, tool execution (`.bat` files). |
| **Architect** | Antigravity (AI) | Planning, Spec writing, PR Review, Task delegation. |
| **Implementer** | Jules (AI/Human) | Code implementation, test writing, PR creation. |

---

## ⚔️ 2. Core Governance Rules (Inviolable)
1.  **Direct Coding Ban**: The Architect (Antigravity/AI) MUST NOT move code directly into the source. All changes must go through a Jules session.
2.  **HITL (Human-In-The-Loop)**: Execution of `.bat` files is the **exclusive right** of the PM (User). The Architect drafts the commands in the SCR Registry; the User fires them.
3.  **Zero-Question Specs**: Specs must be detailed enough for Jules to implement without further clarification.
4.  **Collective Accountability**: Implementer is responsible for execution (no crashes, no `NaN`). Architect is responsible for logic (economic correctness).

---

## 🐙 3. PR Review & Security
PRs are reviewed by the **Git Reviewer** worker.
- **Criteria**: Zero-Sum violation, Security/Hardcoding leaks, Code Purity, SoC compliance.
- **Verdict**: Must receive an **APPROVE** verdict from the Reviewer before the PM merges.

---

## 🏁 4. Session Conclusion & Cleanup
At the end of every work session, the Architect MUST execute the following "Cleanup Sequence".

### 4.1. Knowledge Absorption (Farming)
1.  **Insight Farming**:
    - Harvest `communications/insights/*.md` -> Merge into `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`.
    - **Post-Action**: MOVE processed files to `communications/insights/archived/`.
2.  **Handover**: Update `design/_archive/handovers/HANDOVER_YYYY-MM-DD.md`.

### 4.2. Tactical Sanitation (The Purge)
*Delete ephemeral artifacts to maintain a "Cold Boot" state.*

1.  **Run Cleanup Script**: Execute **`.\cleanup-session.bat`** from the project root.
2.  **Effect**: This will empty `gemini_output`, `drafts`, `jules_logs`, and root-level debug debris.
3.  **Manual Check**: Verify that no critical `Spec` or `Work Order` was accidentally targeted if they were temporarily placed in draft zones.

---

## 📚 5. Documentation Architecture
1.  **Linked Graph Structure**: Every document must be reachable from `INDEX.md`. Orphaned documents are deleted during Session Conclusion.
2.  **Abstract to Concrete Hierarchy**: 
    - `1_governance` (Why/Rules) 
    - `2_operations` (How/Manuals)
    - `3_work_artifacts` (What/Specs)
    - `_archive` (History/Logs)
