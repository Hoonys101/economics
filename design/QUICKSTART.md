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
> Use **SCR (Structured Command Registry)** via `scripts/cmd_ops.py`.

### 1. Analysis & Spec (Gemini)
**Generic Pattern**:
```powershell
python scripts/cmd_ops.py set-gemini <key> --worker <type> -i "<prompt>" -c <file1> <file2>
```
*Worker Types: `audit`, `spec`, `git-review`, `verify`, `reporter`, `git`*

**Example (Draft Spec)**:
```powershell
python scripts/cmd_ops.py set-gemini mission-spec-v1 --worker spec -i "Draft a spec for the Bank module." -c design/manuals/BANKING.md
```
-> **Run**: `.\gemini-go.bat`

### 2. Implementation (Jules)
**Generic Pattern**:
```powershell
python scripts/cmd_ops.py set-jules <key> --command create -t "<title>" -i "<prompt>"
```

**Example (New Code)**:
```powershell
python scripts/cmd_ops.py set-jules mission-code-v1 --command create -t "Bank Impl" -i "Implement the Bank class based on the spec." -f design/specs/BANK_SPEC.md
```
-> **Run**: `.\jules-go.bat`

*See **[Protocol: Tooling](1_governance/protocols/PROTOCOL_TOOLING.md)** for deep dives.*

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
4.  **Clean**: Run **`.\cleanup-session.bat`** to automate the removal of temporary artifacts and logs.

> **"Arm the tool, do not be the tool."** - Standard Operating Procedure v2.1
