# 🚀 Project Economics: Quickstart Guide

This is the definitive entry point for all contributors. **Read this first.**

---

## 🛑 0. The Master Principle (Architect's Rule)
**The Architect (AI/Antigravity) MUST NOT write code, analyze code, or debug directly in the source.**

### 1. The Delegation Chain
- **Gemini**: The Brain (Analysis, Spec Writing, PR Review, Log Forensics).
- **Jules**: The Hands (Implementation, Debugging, Execution).
- **Antigravity**: The Orchestrator (Arming scripts, updating protocols, managing the "Handover Chain").

---

## 🚦 Phase 1: Context Loading & Strategy
*Before taking any action, you must orient yourself.*

1.  **Read the Handover**: Check `_archive/handovers/` for the latest `HANDOVER_YYYY-MM-DD.md`. What was finished?
2.  **Check Status**: Review **[Project Status](1_governance/project_status.md)** for the big picture.
3.  **Check Debt**: Review **[Tech Debt Ledger](2_operations/ledgers/TECH_DEBT_LEDGER.md)** for critical blockers.
4.  **Connect the Dots**: Ensure the link from `Global Goal` -> `Handover` -> `Today's Task` is clear.

---

## 🛠️ Phase 2: Operations (The One-Shot Workflow)
> **🚨 CRITICAL: MASTER `cmd_ops.py` OR FAIL.**
> All agent control is done via **SCR (Structured Command Registry)** using `scripts/cmd_ops.py`.
> **DO NOT** edit `command_registry.json` manually unless absolutely necessary.

### 1. Arm Gemini (Analysis & Spec)
```powershell
python scripts/cmd_ops.py set-gemini <mission_key> --worker [audit|spec|git-review] -i "<instruction>" -c <files>
```
-> Execute with: **`.\gemini-go.bat`**

### 2. Arm Jules (Implementation)
```powershell
python scripts/cmd_ops.py set-jules <mission_key> --command create -t "<title>" -i "<instruction>" -f <work_order_path>
```
-> Execute with: **`.\jules-go.bat`**

*See **[Protocol: Tooling](1_governance/protocols/PROTOCOL_TOOLING.md)** for advanced details.*

---

## 🏗️ Phase 3: Document Hygiene
*Documents must flow from Abstract to Concrete.*
- **Entry Points**: `INDEX.md`, `QUICKSTART.md` (Do not clutter root).
- **Governance**: `1_governance/` (Why we are doing this).
- **Operations**: `2_operations/` (How we do it).
- **Artifacts**: `3_work_artifacts/` (What we created).
- **Archive**: `_archive/` (One-time logs, old handovers).

**Action**: If you see fragmentation (loose files in root, temp logs), use `mission-doc-restructure` to clean it up immediately.

---

## 🏁 Phase 4: Session Conclusion
1.  **Verify**: Ensure all tasks are complete.
2.  **Archive**: Move session logs/reports to `3_work_artifacts/reports/`.
3.  **Handover**: Create a new `HANDOVER_YYYY-MM-DD.md` in `_archive/handovers/`.
4.  **Clean**: Delete temporary `gemini_output` or `drafts` that are no longer needed.

> **"Arm the tool, do not be the tool."** - Standard Operating Procedure v2.1
