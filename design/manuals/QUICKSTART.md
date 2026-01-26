# 🚀 Project Economics: Quickstart Guide

This is the definitive entry point for all contributors. **Read this first.**

---

## 🛑 0. The Master Principle (Architect's Rule)
**The Architect (AI/Antigravity) MUST NOT write code, analyze code, or debug directly in the source.** 

### 1. The Delegation Chain
- **Gemini**: The Brain (Analysis, Spec Writing, PR Review, Log Forensics).
- **Jules**: The Hands (Implementation, Debugging, Execution).
- **Antigravity**: The Orchestrator (Arming scripts, updating protocols, managing the "Handover Chain").

### 2. The Sacred Debug Loop
When a test fails or a leak is detected, follow this sequence:
1. **Log Capture**: Run the test and redirect all output to a file: `python scripts/test_name.py > debug_log.txt 2>&1`.
2. **Brain Analysis**: Arm Gemini to analyze the log and relevant source files:
   `python scripts/cmd_ops.py set-gemini <mission> --worker audit -i "Analyze debug_log.txt and find root cause" -c debug_log.txt path/to/code.py`
3. **Spec Design**: Have Gemini (or Antigravity using Gemini's output) draft a Work Order (WO).
4. **Dispatch**: Arm Jules to execute the fix based on the Work Order.


---

## 🚦 Phase 1: Orientation & Management
Manage these documents in every session to maintain the "Handover Chain":
1.  **[PROJECT_STATUS.md](../project_status.md)**: Current build state and next tasks.
2.  **[ROADMAP.md](../roadmap.md)**: The long-term plan.
3.  **[HANDOVER.md](../handovers/latest.md)**: Picking up from the last session.
4.  **[TECH_DEBT_LEDGER.md](TECH_DEBT_LEDGER.md)**: Track all technical debts found.

---

## 🛠️ Phase 2: Operations (The "Arming" Workflow)
We use **SCR (Structured Command Registry)** to control AI agents. Use `scripts/cmd_ops.py` to "arm" the tools.

### 1. Arm Gemini (Analysis/Spec)
```powershell
python scripts/cmd_ops.py set-gemini <mission_name> --worker [audit|spec|git-review] -i "<instruction>" -c <context_files...>
```
-> Then run **`.\gemini-go.bat`**.

### 2. Arm Jules (Implementation/Debug)
```powershell
python scripts/cmd_ops.py set-jules <mission_name> --command create -t "<title>" -i "<instruction>" -f <spec_file>
```
-> Then run **`.\jules-go.bat`**.

*Full details in **[PROTOCOL_TOOLING.md](PROTOCOL_TOOLING.md)**.*

---

## 🏗️ Phase 3: Engineering & Design
Follow the **SoC**, **DTO-only decisions**, and the **4-Phase Sacred Sequence**.
*Details in **[PROTOCOL_ENGINEERING.md](PROTOCOL_ENGINEERING.md)**.*

---

## 🏁 Phase 4: Session Conclusion
Before leaving, you **MUST** cleanup sessions, update the Ledger, and draft a new Handover.
*Strict checklist in **[PROTOCOL_GOVERNANCE.md](PROTOCOL_GOVERNANCE.md)**.*

---
> **"Arm the tool, do not be the tool."** - Standard Operating Procedure v2.0
