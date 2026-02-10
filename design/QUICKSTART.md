# 🚀 Project Economics: Quickstart Guide

This is the definitive entry point for all contributors. **Read this first.**

---

## 🛑 0. The Master Principle (Architect's Rule)

### 1. The Delegation Chain
| Role | Agent | Responsibility |
| :--- | :--- | :--- |
| **The Brain** | Gemini (gemini-go) | Analysis, Spec Writing, PR Review, Log Forensics |
| **The Hands** | Jules (jules-go) | Implementation, Debugging, Execution |
| **The Team Lead** | Antigravity | Orchestration, Context Management, Delegation |

### 2. The Team Lead's Three Pillars (Antigravity)
> **"The Team Lead is the Bottleneck and the Single Source of Truth (SSoT) for Design. If the Lead codes, the Project stalls."**

| **1. 기획 고도화 준비** | 코드의 현실(형이하학)을 해석하여 수석과의 논의 준비. 구현 가능성, 사이드 이펙트 제공. | 브리핑 자료, ADR 초안 |
| **2. 관심사 분리(SoC) 설계** | 일을 쪼개고 각 조각에 필요한 컨텍스트 정의. Jules/Gemini의 몰입 범위 확정. | 세션 프롬프트 및 컨텍스트 패키지 |
| **3. 지식 결정화 (Knowledge SSoT)** | 발견된 인사이트(Wisdom)를 선별하여 영구 자산화. | `ECONOMIC_INSIGHTS.md`, `_archive/insights/` |
| **4. 일목요연한 문서화** | 결정 사항(ADR), 논의 경과, 작업 진행 상황을 관리하고 전파. (디자인의 최종 진실성 유지) | TECH_DEBT_LEDGER, Handover |

### 3. Antigravity's Code Authority & Productivity Loss
- **Direct Coding = Interference (방해)**: 실무 도구(Jules, Gemini-CLI)는 대체 가능하지만, 팀장의 설계 및 중재 역할은 **대체 불가능(Irreplaceable)** 합니다.
- **Productivity Quantification**: 팀장이 직접 코드 1줄을 수정하는 시간은 곧 **명세서(Spec) 5개를 작성할 기회를 날리는 것**입니다. 이는 전체 프로젝트 생산성을 **20% 수준으로 급락**시킵니다.
- **Spec 수정/전면 재작성**: ✅ (Antigravity의 주권)
- **코드 수정**: ⚠️ (최후의 수단. 오직 확신이 있을 때만 수정하며, 디버깅은 금지)
- **디버깅**: 🚫 **NEVER.** (병목 현상의 주범. 반드시 Jules에게 위임)

### 3.5. Architectural Threshold Rules (The "Stop" Rule)
Any task that exceeds the following thresholds MUST be delegated to Jules (Implementation) or Gemini-Go (Analysis/Spec). **Antigravity must stop direct action immediately.**

- **Reading Threshold**: If the task requires referencing more than **5** code documents/files.
- **Modification Threshold**: If the task requires modifying more than **3** files.
- **Complexity Guard**: Even if the fix is "only 2-4 lines", if it touches more than 3 files or requires deep context from 5+ files, it's an architectural change, not a quick fix.
- **Action**: Halt implementation, draft the Integrated Mission Guide, and register a Jules-Go/Gemini-Go mission.

### 4. The Confidence-Driven Coding Rule (Antigravity's Exception)
**Antigravity가 코드를 직접 수정할 경우, 반드시 다음 절차를 엄수합니다.**
1.  **Branch Isolation**: `main` 브랜치 직접 수정 금지. `feature/` 브랜치 생성.
2.  **AI Review Verification**: 커밋 후 `gemini-go git-review` 실행, 객관적 리뷰 보고서 생성.
3.  **Confidence Report**: 리뷰 결과를 사용자에게 제시하여 코드 안전성에 대한 확신(Confidence) 확보 후 머지 승인 요청.
4.  **No Blind Merges**: 주관적 판단 머지 금지. 데이터(리뷰 결과, 테스트 통과)로 증명.

### 5. The Concurrency Principle (Triple-Engine)
- **병렬 수행 지향**: 단순한 순차적 중요도보다 **병렬 수행 가능성**을 우선 고려합니다.
- **Triple-Engine Workflow**: 가급적 **인프라(Infra), 경제(Economics), 모델링(Modeling)**의 3가지 트랙이 독립된 세션에서 동시에 가동되는 것을 지향합니다.
- **격리된 부채 해결**: 메인 개발을 방해하지 않는 자잘한 기술 부채들은 꼼꼼히 챙겨 메인 엔진과 병행 처리함으로써 개발 속도를 극대화합니다.
- **설계형 부채 상환 (Spec-as-Repayment)**: 기술 부채는 코드 수정으로만 갚는 것이 아닙니다. 상세 명세(Spec)를 작성하고, 영역을 분리(Domain Segregation)하여 실행 시점을 확정하는 것만으로도 부채의 상당 부분은 이미 상환(SPECCED 상태)된 것으로 간주합니다. 충돌 위험으로 코딩(Jules)이 지연되더라도 명세 작성(Gemini)은 멈추지 않습니다.

### 6. 복명복창 (Acknowledgement & Execution)
- **질문과 확인**: 지시 사항에 의문점이 있다면 즉시 질문하여 명확히 합니다.
- **안 선행, 실행 후행**: 실행할 수 있을 만큼 구체화가 가능하다면, 먼저 실행 계획(方案)을 설명하여 승인을 얻은 후 실무(Jules/Gemini)에 착수합니다.


---

## 🚦 Phase 1: Context Loading & Strategy
*Before taking any action, you must orient yourself.*

1.  **Read the Handover**: Check `_archive/handovers/` for the latest `HANDOVER_YYYY-MM-DD.md`. What was finished?
2.  **Master the Architecture**: Review **[Platform Architecture](1_governance/platform_architecture.md)**.
    - *Tip*: 핵심 개념은 숙지하고, 구체적인 매커니즘은 작업 시 상세 문서를 찾아 활용하십시오.
3.  **Check Status**: Review **[Project Status](../PROJECT_STATUS.md)** for the big picture.
4.  **Check Debt**: Review **[Tech Debt Ledger](2_operations/ledgers/TECH_DEBT_LEDGER.md)** for critical blockers.
5.  **Scan Ready Specs**: Check `design/3_work_artifacts/specs/` for specced but unmerged features (e.g., Political System, Saga Patterns).
6.  **Connect the Dots**: Ensure the link from `Global Goal` -> `Handover` -> `Today's Task` is clear.

### 📜 The Documentation Integrity Rules
1. **The Spec-Architecture Rule**: **명세서(SPEC) 작성 시점**에서 해당 기능이 근원 아키텍처나 세부 설계에 영향을 준다면, 반드시 **아키텍처 문서들을 먼저 업데이트**하여 구조적 정합성을 유지해야 합니다. (의도 선행, 실행 후행)
2. **The "Read First" Rule**: 어떤 부분을 **수정(Modify), 보완(Supplement), 생성(Create)**하고자 한다면, 반드시 **해당 부분과 관련된 문서**를 먼저 확인해야 합니다. 맥락 없는 코드는 부채(Debt)입니다.
3. **The "Don't Reinvent the Wheel" Rule**: 새로운 기능을 구현하기 전, 반드시 기존 코드베이스에서 유사한 로직이나 "이미 구현되다 만 흔적"이 있는지 검색하십시오. **바퀴를 다시 발명하지 마십시오.** (Archaeology First)
4. **The Manual Evolution Rule**: **Gemini의 결과물(리뷰 보고서, 상세 설계 등)**을 검토한 후, Gemini용 매뉴얼(`git_reviewer.md`, `spec_writer.md` 등)의 보완이나 정책 업데이트가 필요하다고 판단되면 이를 **즉시 수행**하여 프로젝트의 지능적 정합성을 유지해야 합니다. (Continuous Improvement)

---

## 📋 1.5. 최종 관리자 업무 절차 (Admin Workflow)
> **관리업무 수행 시 반드시 아래 절차를 따르십시오.**

| 단계 | 행동 | 도구 |
| :--- | :--- | :--- |
| **1a. 자료 수집** | 관련 파일명/경로 수집 | (에이전트) |
| **1b. 자료 분석** | 수집된 컨텍스트를 넣어 정리된 보고서 수령 | `gemini-go` |
| **2. 분류/관리** | 중요도 및 문제 관련성에 따라 정보 분류 | (에이전트 판단) |
| **3. 판단** | 정리된 핵심 정보를 기반으로 의사결정 | (에이전트 판단) |
| **4a. 설계** | Spec 문서 작성 | `gemini-go` |
| **4b. 구현** | Spec 기반 미션 위임 | `jules-go` |

---

## 🛠️ Phase 2: Operations (The SCR Workflow)
> **🚨 CRITICAL: PREFER DIRECT REGISTRY EDITING.**
> Edit **[command_registry.py](file:///_internal/registry/command_registry.py)** directly for complex missions.

### 🚨 Zero-Error Operations: Agent HARMONY
Gemini와 Jules는 정합된 파라미터 구조를 공유합니다. 모든 미션 설정 시 **Key**와 **Title(-t)**은 필수입니다.

| Agent | command | Key Args | Path Flag |
| :--- | :--- | :--- | :--- |
| **Gemini** | `set-gemini` | `--worker [audit/spec/...]`, **`-t Title`** | `--context` (Multiple files) |
| **Jules** | `set-jules` | `--command [create/send-message]`, **`-t Title`** | `--file` (Single spec/wo file) |

### 🆘 Troubleshooting & Support
- **Git Errors?** (Blocked checkout, commit issues): See **[Troubleshooting: Git](2_operations/protocols/TROUBLESHOOTING_GIT.md)**.
- **cmd_ops Command Failures?** Check the **[Zero-Error Check List](1_governance/protocols/PROTOCOL_TOOLING.md#🚨-guidelines--anti-patterns-zero-error-check)**.

---

### 1. Analysis & Spec (Gemini)
**Preferred Pattern (Direct Edit)**:
1. Open [`command_registry.py`](file:///_internal/registry/command_registry.py).
2. Follow the `# --- CHOICE REFERENCE ---` comments for valid workers.
3. Add/Modify a mission dictionary entry using Python triple-quotes for multi-line prompts.

**Legacy/Simple Pattern (CLI)**:
```powershell
python _internal/scripts/cmd_ops.py set-gemini <key> -t "<title>" --worker <type> -i "<prompt>" --context <file1> <file2>
```
- **Pro-Tip**: 여러 참조 파일은 `--context` 뒤에 나열합니다.

### 2. Implementation (Jules)
**Preferred Pattern (Direct Edit)**:
1. Open [`command_registry.py`](file:///_internal/registry/command_registry.py).
2. Define a `create` mission for Jules.
3. Reference an "Integrated Mission Guide" in the `instruction` or `file` field.

**Legacy/Simple Pattern (CLI)**:
```powershell
# Create Mode (New Mission)
python _internal/scripts/cmd_ops.py set-jules <key> -t "<title>" --command create -i "<prompt>" --file <spec_path>

# Send Mode (Feedback / Follow-up)
# Note: session_id는 UI/Orchestrator에서 활성 세션을 검색하여 자동 주입하므로 설정 시 생략 가능합니다.
python _internal/scripts/cmd_ops.py set-jules <key> -t "<title>" --command send-message -i "<prompt>"
```
- **Pro-Tip**: Jules는 `--file` (또는 `-f`)만 지원하며, `--context`는 무시됩니다.
- **Dynamic ID**: `send-message` 시 서버의 활성 ID를 UI에서 선택하면 레지스트리의 설정값이 해당 세션으로 발송됩니다.

### 🚨 Jules Delegation Protocol: 맥락 주입 (Context Injection)
> **"신입사원에게 일을 맡기듯 하지 마라 (Don't Delegate Like a Rookie Manager)."**

Jules에게 미션을 위임할 때, "장부(Ledger)"나 "단일 명세서(Single Spec)"만 던지고 "알아서 해"라고 하는 것은 **반쪽짜리 위임(Lazy Delegation)**입니다. Jules가 업무에 진입하는 시점에서 **충분한 맥락이 주입(Context Injection)**되어야 합니다.

#### ✅ 올바른 위임(Good Delegation)
1.  **통합 가이드 작성**: 관련 명세서, 감사 보고서, 에러 로그 등을 하나의 **"통합 미션 가이드(Integrated Mission Guide)"**로 먼저 작성합니다.
    - 위치: `design/3_work_artifacts/drafts/bundle_[a|b|c]_[topic]_guide.md`
2.  **가이드 전달**: `--file` 인자에 통합 가이드 파일을 지정합니다. 이 파일이 Jules의 **유일한 입문서(Single Entry Point)**가 됩니다.
3.  **자기 완결성 검증**: 가이드 문서만 읽어도 "뭘 해야 하는지", "어떤 파일을 건드려야 하는지", "성공 기준(Verification)이 뭔지" 알 수 있어야 합니다.

#### 🔥 Anti-Patterns (이렇게 하지 마세요)
| Anti-Pattern | 왜 나쁜가? |
| :--- | :--- |
| **장부만 던지기** | Jules가 장부에서 명세서를 찾고, 명세서에서 코드를 찾는 탐색 비용 발생. 시간 낭비. |
| **인스트럭션에 모든 맥락 서술** | 텍스트 제한에 금방 도달. 유지보수 불가. |
| **여러 개의 명세서 병렬 참조** | 어떤 것이 우선인지 불명확. 충돌 해석 부담이 Jules에게 전가됨. |

#### 💡 통합 가이드 템플릿 (Integrated Mission Guide Template)
```markdown
# Mission Guide: [Mission Title]

## 1. Objectives
- List of TD-IDs and their one-liner descriptions.

## 2. Reference Context (MUST READ)
- Links to PRIMARY spec files and audit reports.

## 3. Implementation Roadmap
### Phase 1: ...
### Phase 2: ...

## 4. Verification
- Exact test commands or validation steps.
```


---

---

## 🏗️ Phase 3: Document Hygiene
*Documents must flow from Abstract to Concrete.*
- **Entry Points**: `INDEX.md`, `QUICKSTART.md` (Do not clutter root).
- **Governance**: `1_governance/` (Why we are doing this).
- **Operations**: `2_operations/` (How we do it).
- **Artifacts**: `3_work_artifacts/` (What we created).
- **Archive**: `_archive/` (One-time logs, old handovers).

### 3.5. Technical Debt & Knowledge Crystallization (지식 자산화)
기술 부채를 상환하거나 중요한 시스템 인사이트를 발견했을 때, 지시 사항을 반드시 문서로 자산화하십시오.

#### 🏛️ The Crystallization Pipeline
1.  **Selection**: `communications/insights/`에 생성된 리포트 중 보존 가치가 있는 것 선별.
2.  **Archiving**: 선별된 파일을 `design/_archive/insights/`로 이동 (Date Prefix 활용).
3.  **Linking**: `ECONOMIC_INSIGHTS.md` (KB) 및 `TECH_DEBT_LEDGER.md`에 영구 링크 생성.

> **"이 인사이트를 영원히 지워도 되는가?" - 이 질문에 답하기 전까지는 `cleanup-go.bat`을 실행하지 마십시오.**

**Action**: If you see fragmentation (loose files in root, temp logs), use `mission-doc-restructure` to clean it up immediately.

---

## 🏁 Phase 4: Session Conclusion (The Spontaneous Closure)
1.  **Harvest**: The USER runs **`.\session-go.bat`**. This arms and executes a Gemini mission to distill all `communications/insights/` into a single Handover Report.
2.  **Crystallize (Architect's Duty)**: 🚨 **MANDATORY**: Antigravity MUST read the generated report and reflect its findings into:
    - **Governance**: `PROJECT_STATUS.md` (Update milestones & current focus).
    - **Operations**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (Liquidate/Add debts).
    - **Architecture**: `design/1_governance/architecture/ARCH_*.md` (Hard-code new systemic rules).
3.  **Final Handover**: Ensure the permanent handover log is stored in `design/_archive/handovers/HANDOVER_YYYY-MM-DD.md`.
4.  **Incinerate & Push (Antigravity's Job)**: Once the Architect confirms knowledge crystallization, they execute **`.\cleanup-go.bat`**. This automates:
    - `git add .` & `git commit`
    - Purging all temporary files (PR diffs, logs, raw insights)
    - `git push origin main`

> **"Knowledge survives, artifacts perish."** - Standard Operating Procedure v2.3
