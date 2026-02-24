# 🚀 Project Economics: Quickstart Guide

This is the definitive entry point for all contributors. **Read this first.**

---

## 🛑 0. The Master Principle (Architect's Rule)

### 1. The Delegation Chain
| Role | Agent | Responsibility | Output Type |
| :--- | :--- | :--- | :--- |
| **Architect & Orchestrator** | **Antigravity** | Role Assignment, Context Selection, Final Review | Missions & Strategic Direction |
| **Logic Generator** | Gemini-CLI Workers | Analysis, Spec Writing, PR Review, Logging | Markdown Reports & Specs |
| **Logic & Vision Hub** | **Roadmap** | [CONCEPTUAL_ROADMAP.md](CONCEPTUAL_ROADMAP.md) | Long-term Wave 3-5 Blueprints |
| **Implementation Hand** | Jules | Coding, Debugging, Execution | Git PRs & Codebase Changes |

### 2. The Architectural Governance Philosophy (Team Lead's Creed)
**"팀장은 세부 구현에 매몰되는 실무자가 아니라, 시스템의 방향성을 결정하는 설계자입니다."**

- **팀장은 코드를 직접 읽지 않는다.** (전문 에이전트가 작성한 **코드 분석 보고서(Insight Reports)**와 **Audit 결과**를 통해 시스템의 상태를 파악한다.)
- **팀장은 구현 코드를 작성하지 않는다.** (비즈니스 로직은 위임하며, 오직 **코드 아키텍처를 설계**하고 **프로토콜을 정의**할 뿐이다.)
- **팀장은 명령서(Manifest)를 통해 소통한다.** (명령서 코드는 아키텍처 설계를 실행으로 옮기기 위한 유일하고 필수적인 **최종 승인 서명**이다.)

### 3. Antigravity's Decision Engine (The 7-Step Protocol)
**"팀장은 직접 코딩하는 자리가 아니라, 정보를 집계하여 최선의 판단을 내리고 명령하는 자리입니다."**

| 단계 | 행동 | 주체 | 도구 |
| :--- | :--- | :--- | :--- |
| **1. 정보 수집** | 관련도/중요도에 따른 컨텍스트 선별 | **Lead (Command)** | `gemini-go` |
| **2. 분석** | 수집된 정보의 기술적 분석 및 요약 | Agent (Analysis) | `gemini-go` |
| **3. 추측** | 분석 결과를 바탕으로 파급력 및 결과 추측 | **Lead (Judgement)** | (Brain) |
| **4. 결단** | 최종 실행 여부 및 방향성 확정 | **Lead (Decision)** | (Decision) |
| **5. 계획수립/전략** | 업무량에 따른 모듈 분할 및 구현 방식 결정 | **Lead (Strategy)** | (Brain) |
| **5.5. 명세서 작성** | 결정된 전략에 따른 세부 구현 명세(Spec) 문서화 | Agent (Drafting) | `gemini-go` |
| **6. 명령** | 매니페스토(`command_manifest.py`) 등록 | **Lead (Command)** | (Registry) |
| **7. 실행** | 명세 기반의 실제 코드 구현/수정 | Agent (Execution) | `jules-go` |

### 3.5. GIGO Guard (Strict Context Selection)
- **GIGO (Garbage In, Garbage Out)**: Gemini 3는 정보수집 및 컨텍스트 정제에서 취약점을 보일 수 있습니다.
- **Lead의 핵심 의무**: 수만 줄의 코드 중 **무엇이 중요하고 관련 있는지**를 필터링하여 Gemini에게 '강제'로 주입하는 것이 팀장의 가장 중요한 실력입니다.
- **Fail-Safe**: 분석 결과가 만족스럽지 않다면, Gemini의 능력을 탓하기 전에 **"내가 준 컨텍스트가 쓰레기(Garbage)가 아니었나?"**를 먼저 자문하십시오.

### 3.5. Architectural Threshold Rules (The "Stop" Rule)
Any task that exceeds the following thresholds MUST be delegated to Jules (Implementation) or Gemini-Go (Analysis/Spec). **Antigravity must stop direct action immediately.**

- **Reading Threshold**: If the task requires referencing more than **5** code documents/files.
- **Modification Threshold**: If the task requires modifying more than **3** files.
- **Complexity Guard**: Even if the fix is "only 2-4 lines", if it touches more than 3 files or requires deep context from 5+ files, it's an architectural change, not a quick fix.
- **Action**: Halt implementation, draft the Integrated Mission Guide in `design/3_work_artifacts/specs/`, and arm the mission (**장착**) in **[command_manifest.py](file:///_internal/registry/command_manifest.py)**.

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

### 5.5. Sprint Execution Methodology (Agile × Waterfall Hybrid)
> **"의도는 실행에 앞섭니다."**
>
> 스프린트에 대한 기획안은 문서(기술부채 및 아키텍처)에 **선행 작성**됩니다.

> **"우리는 애자일을 따라 스프린트를 수행하지만, 각 스프린트는 폭포수 기법을 따릅니다."**

각 스프린트(Wave/Phase) 내부는 아래의 **엄격한 순차적 단계**를 따릅니다:

```
┌──────────────────────────────────────────────────────────────────┐
│  Sprint N (Wave/Phase)                                           │
│                                                                  │
│  ① API/DTO 확정 ──→ ② 모듈별 병렬 구현 ──→ ③ 통합 테스트         │
│     (파생문제 검토)    (Jules × N)            (pytest 100%)       │
│                                                                  │
│  Spec: gemini-manifest  │  Impl: jules-manifest                  │
└──────────────────────────────────────────────────────────────────┘
```

| 단계 | 행동 | 원칙 | 도구 |
| :--- | :--- | :--- | :--- |
| **① API/DTO 확정** | 인터페이스 계약 확정 및 파생 문제(Breaking Changes, 참조 사이트) 검토 | **SDD** (Spec-Driven Development) | `gemini-manifest` → `gemini-go` |
| **② 모듈별 병렬 구현** | 확정된 Spec 기반으로 독립 모듈을 동시 구현 | 모듈 격리 (충돌 방지) | `jules-manifest` → `jules-go` |
| **③ 통합 테스트** | 전체 테스트 스위트 통과 확인 | Zero Regression | `pytest tests/` |

**SDD (Spec-Driven Development) 원칙**:
- 코드를 먼저 작성하지 않습니다. **명세(Spec)가 먼저**입니다.
- Spec은 `gemini-manifest`를 통해 Gemini 워커가 생성합니다.
- Spec이 승인된 후에만 Jules가 구현에 착수합니다.
- API/DTO 변경 시 **전수조사(Call Site Audit)**가 Spec 단계에서 완료되어야 합니다.
### 6. 복명복창 및 능동적 보고 (Communication & Coordination)
- **응답 우선순위**: 질문을 받으면 질문에 대답을 우선하고, 질문의 의도를 파악하여 할 일을 제안드립니다.
- **지시 이행 절차**: 무언가를 시키면 해당 내용이 무엇인지 구체화하여 확인 후 그것을 실행하겠습니다.
- **안 선행, 실행 후행**: 실행할 수 있을 만큼 구체화가 가능하다면, 먼저 실행 계획(方案) 설명하여 승인을 얻은 후 실무(Jules/Gemini)에 착수합니다.
- **선제적 인지 및 보고**: 
    - 사용자가 X를 요구했으나 이를 위해 미리 해야 할 일(Prerequisite)이 있는 경우, 이를 먼저 인지시킨 후 진행합니다.
    - X를 완료하고 Y를 이어서 하는 것이 당연한 흐름인 경우, **"X가 완료되었습니다. 이제 Y를 시작합니다."**와 같이 완료 상태를 명시적으로 보고한 후 후속 작업을 수행합니다.
- **예측 가능성 유지**: 제멋대로 일을 처리하여 사후에 사용자를 당황하게 하거나 신뢰를 깨뜨려서는 안 됩니다. 모든 행동은 사용자가 예측 가능한 범위 내에서, 혹은 명시적 보고 하에 이루어져야 합니다.


---

## 🚦 Phase 1: Context Loading & Strategy
*Before taking any action, you must orient yourself.*

1.  **Read the Handover**: Check `_archive/handovers/` for the latest `HANDOVER_YYYY-MM-DD.md`. What was finished?
2.  **Master the Architecture**: Review **[Platform Architecture](1_governance/platform_architecture.md)**.
    - *Tip*: 핵심 개념은 숙지하고, 구체적인 매커니즘은 작업 시 상세 문서를 찾아 활용하십시오.
3.  **Check Status**: Review **[Project Status](../PROJECT_STATUS.md)** for the big picture.
4.  **Absorb the Vision**: Consult the **[Conceptual Roadmap](CONCEPTUAL_ROADMAP.md)** for long-term wave goals.
5.  **Check Debt**: Review **[Tech Debt Ledger](2_operations/ledgers/TECH_DEBT_LEDGER.md)** for critical blockers.
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

## 🛠️ Phase 2: Operations (The Manifest Workflow)
> **🚨 CRITICAL: Edit `*_manifest.py` ONLY.**
> 오직 아래 두 파일만 수정하십시오. (나머지는 시스템이 알아서 처리합니다.)
> 1. **Gemini**: `_internal/registry/gemini_manifest.py`
> 2. **Jules**: `_internal/registry/jules_manifest.py`

### 📐 Manifest Lifecycle (생명주기)

```
┌─────────────┐     gemini-go / jules-go      ┌──────────────┐     성공 시     ┌──────────┐
│  Manifest   │ ──────────────────────────────→│  JSON (DB)   │ ──────────────→│  삭제됨  │
│  (.py 파일) │   미션 이관 + 매니페스토 리셋   │  (Registry)  │  auto-delete   │          │
└─────────────┘                                └──────────────┘                └──────────┘
                                                     │ 실패 시
                                                     ▼
                                               JSON에 잔존 (재실행 가능)
```

| 단계 | 발생 시점 | 동작 |
| :--- | :--- | :--- |
| **1. 장착** | `manifest.py`에 미션 작성 | 사용자가 dict에 미션 추가 |
| **2. 이관** | `gemini-go` / `jules-go` 실행 | manifest → JSON DB 복사 후 **manifest 자동 리셋** |
| **3. 실행** | 미션 처리 중 | JSON DB에서 미션 로드 및 실행 |
| **4. 완료** | 미션 성공 | JSON DB에서 **자동 삭제** |
| **5. 리셋** | `reset-go` 실행 | **JSON만 초기화** (manifest 보존) |

### 🤖 Gemini Workers (워커 타입 상세)

| Worker | 모델 Tier | 용도 | 출력 예시 |
| :--- | :--- | :--- | :--- |
| `spec` | Pro (Reasoning) | 구현 명세 작성. Jules 실행용 상세 설계 문서 생성 | `MISSION_*_SPEC.md` |
| `git-review` | Pro | PR Diff 분석. 코드 리뷰 보고서 생성 | `pr_review_*.md` |
| `context` | Pro | 프로젝트 상태 요약 및 스냅샷 생성 | 상태 요약문 |
| `crystallizer` | Pro | 분산된 보고서를 통합 지식으로 압축 | 지식 문서 |
| `audit` | Flash (Analysis) | 코드/아키텍처 감사. 기술부채 진단 | 감사 보고서 |
| `report` | Flash | 데이터 분석 및 보고서 생성 | 분석 보고서 |
| `verify` | Flash | 아키텍처 규칙 준수 여부 검증 | 검증 결과 |

### 📝 Field Schema Reference

#### GEMINI_MISSIONS
```python
"MISSION_KEY": {
    "title": "미션 제목",                    # str, 필수
    "worker": "spec",                        # str, 필수 (위 워커 타입 참조)
    "instruction": "상세 지시 사항",          # str, 필수
    "context_files": ["path/to/file.py"],    # list[str], 분석 대상 파일
    "output_path": "gemini-output/spec/...", # str, 결과물 저장 경로
    "model": "gemini-3-pro-preview",         # str, 모델 오버라이드 (선택)
}
```

#### JULES_MISSIONS
```python
"MISSION_KEY": {
    "title": "구현 업무 제목",                # str, 필수
    "instruction": "구체적 행동 지시",         # str, 필수
    "file": "path/to/SPEC.md",               # str, 참조 명세 문서 (선택)
    "command": "create",                      # str, 명령 유형 (선택)
    "wait": False,                            # bool, 완료 대기 (선택)
}
```

### 💡 사용 예시

**1단계: 매니페스토에 미션 작성**
```python
# _internal/registry/gemini_manifest.py
GEMINI_MISSIONS: Dict[str, Dict[str, Any]] = {
    "WO-AUDIT-SETTLEMENT": {
        "title": "Settlement System Audit",
        "worker": "audit",
        "instruction": "SettlementSystem의 zero-sum 정합성을 감사하십시오.",
        "context_files": ["simulation/systems/settlement_system.py"],
        "output_path": "gemini-output/audit/settlement_audit.md"
    }
}
```

**2단계: 실행**
```bash
.\gemini-go.bat WO-AUDIT-SETTLEMENT
# → 미션이 JSON으로 이관되고, manifest.py는 자동 리셋됨
# → 성공 시 JSON에서도 자동 삭제됨
```

### 🆘 Troubleshooting & Support
- **Git Errors?** (Blocked checkout, commit issues): See **[Troubleshooting: Git](2_operations/protocols/TROUBLESHOOTING_GIT.md)**.
- **JSON 초기화**: `reset-go.bat` 실행 (매니페스토는 보존됨).
- **매니페스토 수동 리셋**: 매뉴얼 상태로 되돌리려면 매니페스토 내 dict를 `{ # Add missions here }` 로 비우십시오.

---

## 🛠️ Phase 2.5: Forensic Diagnostic Workflow
> **"Failures are data. Simulations are laboratories."**

When the simulation exhibits stability issues or unexpected behavior, use the Forensic Diagnostic Workflow to identify root causes.

### 1. Run Diagnostic Simulation
Execute a short, high-fidelity run to capture raw behavioral data:
```bash
python scripts/operation_forensics.py --ticks 60 --no-stress --output logs/diagnostic_raw.csv
```
- This generates `logs/diagnostic_raw.csv` (raw data) and `reports/AUTOPSY_REPORT.md` (human-readable summary).

### 2. Refine & Analyze (Gemini)
Log refinement is now **automated** within `scripts/operation_forensics.py`. It generates `reports/diagnostic_refined.md` automatically.
1. Arm a mission in `gemini_manifest.py` with `worker="audit"` for root cause analysis (`diag-log-analyze`).
2. Set `context_files` to include `reports/AUTOPSY_REPORT.md` and `reports/diagnostic_refined.md`.
3. Run `gemini-go.bat diag-log-analyze`.

### 3. Implement Fix (Jules)
Once the analysis identifies the fix, arm a Jules mission based on the generated `MISSION_spec`.

---

### 1. Analysis & Spec (Gemini)
**Manifest 방식 (표준)**:
1. `command_manifest.py` → `GEMINI_MISSIONS`에 미션 **장착** (Dict 추가).
2. `gemini-go.bat [key]` 실행 (auto-sync 후 Gemini 작업 시작).

### 2. Implementation (Jules)
**Manifest 방식 (표준)**:
1. `_internal/registry/command_manifest.py` -> `JULES_MISSIONS`에 미션 **장착**.
2. `jules-go.bat [key]` 실행 (auto-sync 후 Jules 세션 생성).
3. 작업 및 발사 완료 후 manifest에서 해당 항목 삭제. (Antigravity의 일상 업무)

### 2.5. Mission Governance & Worker Scaling
> **"매뉴얼은 에이전트의 뇌이며, 매니페스트는 에이전트의 손입니다 (Manuals are Brains, Manifests are Hands)."**

새로운 기술적 영역이 추가되거나 Gemini의 업무 범위를 확장하고 싶을 때, 다음 절차를 따르십시오.

#### 1️⃣ 새로운 워커(Worker) 및 매뉴얼 추가
1.  **매뉴얼 생성**: `_internal/manuals/[worker_name].md` 파일을 생성합니다.
    - 예: `ui-architect.md`
2.  **지식 바인딩**: 매뉴얼 내부에 `@` 기호를 사용하여 참고할 아키텍처 문서나 가이드를 링크합니다.
    - 시스템은 실행 시 이 링크된 문서들을 자동으로 수집하여 컨텍스트로 주입합니다.
3.  **매니페스트 등록**: `gemini_manifest.py`에 해당 워커를 사용하는 미션을 등록합니다.

#### 2️⃣ 자동화된 계약 주입 (Context Auto-Injection)
`launcher.py`는 코드의 무결성을 위해 관련 DTO 및 API 계약 파일을 자동으로 주입합니다.
- **Universal Contracts**: 모든 코어 파일 수정 시 `TECH_DEBT_LEDGER.md`와 `simulation/dtos/api.py`가 강제 주입됩니다.
- **Domain Contracts**: 수정 대상 파일의 경로(예: `modules/finance/`)를 감지하여 해당 도메인의 `api.py`를 자동으로 첨부합니다.

#### 3️⃣ GIGO 방지: 필터링 가이드
- **Worker Manual**: "어떻게(How)" 일해야 하는지 정의 (전략).
- **Mission Context**: "무엇을(What)" 건드려야 하는지 정의 (대상).
- **Universal Contracts**: "규규(Rules)"가 무엇인지 정의 (제약).
- **Impact Analysis (Call Site Injection)**: DAO/DTO 수정 시, 이를 참조하는 모든 모듈을 검색하여 컨텍스트로 함께 주입하는 것을 원칙으로 합니다. (GIGO 방지)

### 🚨 Jules Delegation Protocol: 맥락 주입 (Context Injection)
> **"신입사원에게 일을 맡기듯 하지 마라 (Don't Delegate Like a Rookie Manager)."**

- **원칙**: 미션을 장착(Mounting)할 때는 **오직 매니페스토 파일(`*_manifest.py`) 하나만 수정**해야 합니다.
- **금지사항**: `command_registry.json`, `launcher.py`, 또는 다른 시스템 파일을 절대 건드리지 마십시오. 장착은 순수하게 **명령서(Manifest)**를 통해서만 이루어집니다.

Jules에게 미션을 위임할 때, "장부(Ledger)"나 "단일 명세서(Single Spec)"만 던지고 "알아서 해"라고 하는 것은 **반쪽짜리 위임(Lazy Delegation)**입니다. Jules가 업무에 진입하는 시점에서 **충분한 맥락이 주입(Context Injection)**되어야 합니다.

#### ✅ 올바른 위임(Good Delegation)
1.  **통합 가이드 작성**: 관련 명세서, 감사 보고서, 에러 로그 등을 하나의 **"통합 미션 가이드(Integrated Mission Guide)"**로 먼저 작성합니다.
    - 위치: `design/3_work_artifacts/specs/spec_[topic].md`
2.  **가이드 전달**: `command_manifest.py`의 `"file"` 필드에 가이드 경로를 설정합니다. 이 파일이 Jules의 **유일한 입문서(Single Entry Point)**가 됩니다.
3.  **자기 완결성 검증**: 가이드 문서만 읽어도 "뭘 해야 하는지", "어떤 파일을 건드려야 하는지", "성공 기준(Verification)이 뭔지" 알 수 있어야 합니다.

#### 🔥 Anti-Patterns (이렇게 하지 마세요)
| Anti-Pattern | 왜 나쁜가? |
| :--- | :--- |
| **장부만 던지기** | Jules가 장부에서 명세서를 찾고, 명세서에서 코드를 찾는 탐색 비용 발생. 시간 낭비. |
| **인스트럭션에 모든 맥락 서술** | 텍스트 제한에 금방 도달. 유지보수 불가. |
| **여러 개의 명세서 병렬 참조** | 어떤 것이 우선인지 불명확. 충돌 해석 부담이 Jules에게 전가됨. |

#### 💡 통합 가이드 템플릿 (Integrated Mission Guide Template)
> **GIGO 방지 원칙**: 인스트럭션에 모든 것을 쓰지 마십시오. 대신 **[Reference Context]** 섹션에 가장 연관성 높은 파일들(High-Relevance)과 아키텍처 규칙을 선별하여 링크하십시오.
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


### 2.6. Manifest Schema Contract (Strict Integrity)
> **🚨 Mandatory Rule**: Manifests are system contracts. Violating the field schema (adding arbitrary keys) is an architectural breach.

#### 🤖 Gemini-Go Schema (`gemini_manifest.py`)
- **`title`** (str): Mission representative name.
- **`worker`** (str): Persona type (`spec`, `audit`, `review`, etc.).
- **`instruction`** (str): Detailed objective.
- **`context_files`** (list): List of required file paths for analysis.
- **`output_path`** (str, Optional): Target path for result persistence.
- **`model`** (str, Optional): Specific model override.

#### 🛠️ Jules Schema (`jules_manifest.py`)
- **`title`** (str): Implementation task name.
- **`instruction`** (str): Brief action summary.
- **`file`** (str, Optional): Path to the **Integrated Mission Guide** (Spec).
- **`wait`** (bool, Optional): Whether to block for completion.

**Rule**: NEVER invent keys like `context_files` in Jules or `wait` in Gemini. Stick to the documented schema to ensure system automation works.

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
