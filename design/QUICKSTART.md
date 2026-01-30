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
2.  **Master the Architecture**: Review **[Platform Architecture](1_governance/platform_architecture.md)**.
    - *Tip*: 핵심 개념은 숙지하고, 구체적인 매커니즘은 작업 시 상세 문서를 찾아 활용하십시오.
3.  **Check Status**: Review **[Project Status](1_governance/project_status.md)** for the big picture.
4.  **Check Debt**: Review **[Tech Debt Ledger](2_operations/ledgers/TECH_DEBT_LEDGER.md)** for critical blockers.
5.  **Connect the Dots**: Ensure the link from `Global Goal` -> `Handover` -> `Today's Task` is clear.

### 📜 The Documentation Integrity Rules
1. **The Spec-Architecture Rule**: **명세서(SPEC) 작성 시점**에서 해당 기능이 근원 아키텍처나 세부 설계에 영향을 준다면, 반드시 **아키텍처 문서들을 먼저 업데이트**하여 구조적 정합성을 유지해야 합니다. (의도 선행, 실행 후행)
2. **The "Read First" Rule**: 어떤 부분을 **수정(Modify), 보완(Supplement), 생성(Create)**하고자 한다면, 반드시 **해당 부분과 관련된 문서**를 먼저 확인해야 합니다. 맥락 없는 코드는 부채(Debt)입니다.

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

## 🏁 Phase 4: Session Conclusion (The Spontaneous Closure)
1.  **Harvest**: The USER runs **`.\session-go.bat`**. This arms and executes a Gemini mission to distill all `communications/insights/` into a single Handover Report.
2.  **Crystallize (Architect's Duty)**: 🚨 **MANDATORY**: Antigravity MUST read the generated report and reflect its findings into:
    - **Governance**: `design/1_governance/project_status.md` (Update milestones & current focus).
    - **Operations**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (Liquidate/Add debts).
    - **Architecture**: `design/1_governance/architecture/ARCH_*.md` (Hard-code new systemic rules).
3.  **Final Handover**: Ensure the permanent handover log is stored in `design/_archive/handovers/HANDOVER_YYYY-MM-DD.md`.
4.  **Incinerate**: Confirm knowledge is crystallized, then execute **`.\cleanup-session.bat`** (triggered by `session-go` or manual) to purge all temporary files (PR diffs, logs, raw insights).

> **"Knowledge survives, artifacts perish."** - Standard Operating Procedure v2.3
