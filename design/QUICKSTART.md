# 🚀 Project Economics: Quickstart Guide

This is the definitive entry point for all contributors. **Read this first.**

---

## 🛑 0. The Master Principle (Architect's Rule)
**The Architect (AI/Antigravity) MUST NOT write code, analyze code, or debug directly in the source.**

### 1. The Delegation Chain
- **Gemini**: The Brain (Analysis, Spec Writing, PR Review, Log Forensics).
- **Jules**: The Hands (Implementation, Debugging, Execution).
- **Antigravity**: The Orchestrator (Arming scripts, updating protocols, managing the "Handover Chain").

### 2. The Concurrency Principle (Triple-Engine)
- **병렬 수행 지향**: 단순한 순차적 중요도보다 **병렬 수행 가능성**을 우선 고려합니다.
- **Triple-Engine Workflow**: 가급적 **인프라(Infra), 경제(Economics), 모델링(Modeling)**의 3가지 트랙이 독립된 세션에서 동시에 가동되는 것을 지향합니다.
- **격리된 부채 해결**: 메인 개발을 방해하지 않는 자잘한 기술 부채들은 꼼꼼히 챙겨 메인 엔진과 병행 처리함으로써 개발 속도를 극대화합니다.
- **설계형 부채 상환 (Spec-as-Repayment)**: 기술 부채는 코드 수정으로만 갚는 것이 아닙니다. 상세 명세(Spec)를 작성하고, 영역을 분리(Domain Segregation)하여 실행 시점을 확정하는 것만으로도 부채의 상당 부분은 이미 상환(SPECCED 상태)된 것으로 간주합니다. 충돌 위험으로 코딩(Jules)이 지연되더라도 명세 작성(Gemini)은 멈추지 않습니다.

### 3. 복명복창 (Acknowledgement & Execution)
- **질문과 확인**: 지시 사항에 의문점이 있다면 즉시 질문하여 명확히 합니다.
- **안 선행, 실행 후행**: 실행할 수 있을 만큼 구체화가 가능하다면, 먼저 실행 계획(方案)을 설명하여 승인을 얻은 후 실무(Jules/Gemini)에 착수합니다.


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
> **⚠️ Responsibility Clause**: Gemini creates the **Draft**. Antigravity (You) owns the **Final Quality**. Do not blindly commit AI output. Review, refine, and ensure it aligns with the Architecture before proceeding.
> **🚫 Prohibition Clause**: Antigravity is the Editor, NOT the Writer. You MUST NOT write specs or code from scratch. Always delegate the "First Draft" to Gemini or Jules, then Curate.
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
4.  **Incinerate & Push (Antigravity's Job)**: Once the Architect confirms knowledge crystallization, they execute **`.\cleanup-go.bat`**. This automates:
    - `git add .` & `git commit`
    - Purging all temporary files (PR diffs, logs, raw insights)
    - `git push origin main`

> **"Knowledge survives, artifacts perish."** - Standard Operating Procedure v2.3
