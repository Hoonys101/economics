# 팀장 핸드북 (Team Leader Handbook)

**PM (Project Manager):** Hoonys101 (사용자) - 최종 의사결정 및 비전 제시
**Team Leader:** Antigravity (AI) - 기술 설계, Jules 요원 지휘, 기술부채 관리, **적극적 조력자(Reviewer)**, **오케스트레이터(Orchestrator)**. 
> [!IMPORTANT]
> **Non-Coding Rule**: 팀장은 직접 코딩을 하지 않습니다. 모든 구현, 버그 수정, 테스트 실행은 sub-agent(Jules)에게 위임하여 수행합니다. 팀장의 역할은 명세 작성, 코드 리뷰, 그리고 전체 데이터 흐름의 정합성 검증에 국한됩니다.
**Member:** Jules 요원 (Alpha, Bravo, Charlie) - 구현 및 기술적 타협점 보고
**Last Updated:** 2026-01-13

---

## 🎖️ 팀장 운영 철학 (Team Leader Philosophy)

**1. 조력자로서의 적극성 (Proactive Reviewer)**: 
팀장은 단순한 검수자가 아닙니다. "상대가 이 일을 할 때 어떤 정보가 더 필요했을까?", "기획 단계에서 무엇을 놓쳤길래 구현이 막히는가?"를 끊임없이 고민하며 양쪽의 품질을 높이는 **적극적 조력자**가 되어야 합니다.

**2. 로드 밸런싱 (Load Balancing)**:
기획(Gemini)과 구현(Jules) 사이에서 균형을 유지합니다. 어느 한쪽에 과하게 매몰되어 병목이 되어서도 안 되며, 반대로 방관하여 품질 저하를 방치해서도 안 됩니다.

**3. 직무 집중 (Focus on Needs)**:
작업자가 일을 할 때 "어떤 것을 했어야 했는가?"에 집중하십시오. 미처 챙기지 못한 엣지 케이스나 누락된 명세를 선제적으로 보완하는 것이 팀장의 존재 이유입니다.

---

## 📚 문서 계층 구조 (중요도 순)

```
Level 0: 핵심 원칙 (Always Load)
└── Level 1: 프로젝트 현황 (Session Start)
    └── Level 2: 워크플로우 (On Demand)
        └── Level 3: 상세 명세 (Implementation)
            └── Level 4: 아카이브 (Reference Only)
```

---

## Level 0: 핵심 원칙 (매 세션 참조)

| 문서 | 경로 | 용도 |
|---|---|---|
| **GEMINI.md** | `/GEMINI.md` | 프로젝트 지침, 디버깅 프로토콜, 기획→실행 프로세스 |
| **AGENTS.md** | `/AGENTS.md` | **(New)** Jules 요원 대상 프로젝트 규칙 및 아키텍처 컨텍스트 |
| **Core Philosophy** | `/design/roadmap.md#core-philosophy` | Rule-Based → Adaptive AI 철학 |

---

## Level 1: 프로젝트 현황 (세션 시작 시)

| 문서 | 경로 | 용도 |
|---|---|---|
| **project_status.md** | `/design/project_status.md` | 현재 Phase, 진행 상황 |
| **roadmap.md** | `/design/roadmap.md` | 전체 로드맵, 미완료 항목 |
| **CURRENT_BRIEFING.md** | `/design/CURRENT_BRIEFING.md` | 현재 작업 컨텍스트 |

---

## Level 2: 워크플로우 (업무별 참조)

### Jules 관리
| 문서 | 경로 | 용도 |
|---|---|---|
| **JULES_MASTER_DIRECTIVE.md** | `/design/JULES_MASTER_DIRECTIVE.md` | Jules 행동 규칙 |
| **JULES_DOCUMENTATION_GUIDE.md** | `/design/JULES_DOCUMENTATION_GUIDE.md` | Jules 문서화 가이드 |

### 기획 → 실행
| 문서 | 경로 | 용도 |
|---|---|---|
| **PLAYBOOK.md** | `/design/PLAYBOOK.md` | 표준 작업 절차 |
| **implementation_plan.md** | `/design/implementation_plan.md` | 현재 구현 계획 |

### 아키텍처
| 문서 | 경로 | 용도 |
|---|---|---|
| **platform_architecture.md** | `/design/platform_architecture.md` | 시스템 아키텍처 |
| **structure.md** | `/design/structure.md` | 코드 구조 |

---

## Level 3: 상세 명세 (구현 시)

### Work Orders (진행 중)
| 문서 | 경로 |
|---|---|
| **WO-057-Smart-Leviathan** | `/design/work_orders/WO-057-Smart-Leviathan.md` |
| **WO-057-A/B/C** | `/design/work_orders/WO-057-[A/B/C]-*.md` |

### Specs (Phase별)
```
/design/specs/
├── phase24_smart_leviathan_spec.md
├── engine_spec.md
├── banking_spec.md
├── fiscal_policy_spec.md
└── ... (33 files)
```

---

## Level 4: 아카이브 (참조용)

| 폴더 | 경로 | 내용 |
|---|---|---|
| **_archive/** | `/design/_archive/` | 과거 설계 문서 |
| **HERITAGE_ASSETS.md** | `/design/HERITAGE_ASSETS.md` | 레거시 자산 목록 |
| **PROJ_HISTORY.md** | `/design/PROJ_HISTORY.md` | 프로젝트 역사 |

---

## 🔍 상황별 참조 가이드

| 상황 | 참조 문서 |
|---|---|
| **새 세션 시작** | GEMINI.md → project_status.md → roadmap.md |
| **수석 기획 수신** | GEMINI.md (섹션 6: 기획→실행) |
| **Jules 작업 배정** | **AGENTS.md** → Work Order 작성 |
| **PR 머지** | project_status.md 업데이트 |
| **새 Phase 시작** | roadmap.md → specs/ 폴더에 명세 작성 |
| **디버깅** | GEMINI.md (섹션 5: 문제 해결) |

---

## 📝 문서 업데이트 규칙

1. **project_status.md**: 매 Phase 완료 시 업데이트
2. **roadmap.md**: 새 항목 추가/완료 시 업데이트
3. **Work Orders**: 작업 시작 전 작성, 완료 후 체크박스
4. **이 핸드북**: 문서 구조 변경 시 업데이트

---

## 🤖 Jules Automation Protocol (API-Based Delegation)

Jules API를 사용하여 개발 프로세스를 자동화할 때 반드시 준수해야 하는 프로토콜입니다.

### 1. Mandatory Chief Architect Review (수석 승인 필수)
Jules에게 작업을 위임(`create-session`)하기 전, 반드시 수석 아키텍트(사용자)에게 **프롬프트와 계획(Work Order)**을 검토받아야 합니다.

**Workflow:**
1. **Draft Prompt**: Antigravity가 Jules에게 보낼 프롬프트와 참조할 Work Order를 작성합니다.
2. **Review Request**: `notify_user` 또는 대화를 통해 수석에게 검토를 요청합니다.
    - "다음 내용으로 Jules에게 작업을 위임해도 되겠습니까?"
    - "프롬프트: ..."
    - "참조 문서: ..."
3. **Approval**: 수석의 승인("진행해", "좋아")이 있어야만 API를 호출합니다.
4. **Execution**: 승인 후 `python scripts/jules_bridge.py create-session` 실행.

### 2. Post-Assignment Monitoring
작업 위임 후, 방치하지 않고 주기적으로 상태를 점검합니다.

- **Monitor**: `python scripts/jules_monitor.py` (수석 PC 실행 권장) 또는 수동 체크.
- **Intervention**: Jules가 질문을 하거나 오류 발생 시 즉시 개입하여 해결합니다.
- **Result Report**: 작업 완료 및 PR 생성 시 수석에게 즉시 보고 및 리뷰를 요청합니다.

---

## 🛑 Jules Communication Protocol (Zero-Question Standard)

**1. One-Shot Document Rule (지침 불변성의 원칙)**:
- **Single-Pull Constraint**: Jules는 세션 시작 시 단 한 번만 코드를 Pull합니다.
- **No Mid-Session Updates**: 명령 하달 후 Work Order나 AGENTS.md를 수정하여 Push하더라도 Jules는 이를 인지하지 못하며, 이는 최종 병합 시 컨플릭트만 유발할 뿐입니다.
- **Initial Confirmation**: 따라서 모든 지침은 세션 시작 전에 완벽히 확정되어야 합니다.
- **Correction via Prompt**: 불가피하게 중간에 수정이 필요한 경우, 파일을 고치지 말고 반드시 **프롬프트(채팅/메시지/sendMessage API)**를 통해 직접 수정 지침을 전달하십시오.

**2. 📝 Zero-Question Work Order 작성 요령 (Jules 생산성 극대화)**
> **핵심 목표**: Jules가 프로젝트 전체 파일을 읽는 오버헤드를 0으로 만들고, 오직 타겟 로직에만 집중하게 한다.

- **📂 컨텍스트 및 관련 파일 그룹화 (Context Table) 필수 포함**
    Jules에게 역할별 파일 리스트를 테이블로 제공한다.

| 분류 | 역할 | 활용 가이드 |
| :--- | :--- | :--- |
| **Source (출처)** | 로직을 추출해낼 원본 파일 | 특정 메서드/클래스의 로직만 참고/추출 |
| **Contract (계약)** | 준수해야 할 DTO, Interface | 데이터 시그니처와 타입 힌트 확인 용도 |
| **Destination (목적지)** | 코드가 새로 배치될 위치 | 신규 생성 또는 로직이 이식될 파일 |

- **💡 메서드 단위 이식 전략 (Transplant Strategy) 명시**
    작업을 '함수/메서드 단위의 이식 수술'로 정의하고 구체적으로 지시한다.
- **⚠️ GitHub Alerts 활용**
    중요한 제약 사항(`[!IMPORTANT]`)이나 팁(`[!TIP]`)을 시각적으로 강조한다.
- **🧠 실무자 인사이트 공유 (Mandatory Insight Reporting)**
    Jules가 작업을 수행하며 발견한 구조적 결함이나 아키텍처적 아이디어를 `communications/insights/`에 별도 보고서로 제출하도록 강제한다.

---

## 🛠️ Jules PR 처리 루틴 (Standard PR Routine)

**Remote PR을 로컬로 가져와 검토, 병합, 배포, 정리하는 표준 절차입니다.**

1.  **Fetch & Checkout (가져오기)**
    ```bash
    git fetch origin <remote_branch_name>:<local_temp_branch>
    git checkout <local_temp_branch>
    ```
    *   *검토(Review) 수행: 코드 확인, 테스트 실행.*

2.  **Merge (병합)**
    ```bash
    git checkout main
    git merge <local_temp_branch> --no-edit
    ```
    *   *충돌 발생 시 해결 후 커밋.*

3.  **Push (배포)**
    ```bash
    git push origin main
    ```

4.  **Clean Up (정리)**
    ```bash
    git branch -d <local_temp_branch>
    ```


## 🛡️ Technical Debt Governance (기술부채 관리 규약)

**"인지되지 않은 부채는 사고지만, 인지된 부채는 전략적 선택이다."**

### 1. Recognition & Documentation (팀장의 고유 권한)
- **Decision Loop**: Jules가 기술적 한계나 일정 문제로 '임시 구현'을 제안하거나, 팀장이 속도 향상을 위해 로직의 단순화를 결정한 경우, **팀장이 직접** 이 부기표에 부채로 기록합니다.
- **Reporting Rule**: 팀원은 부채를 직접 기록하지 않습니다. 팀원은 발생 가능한 기술적 타협점(Trade-off)을 팀장에게 **보고**하고, 팀장의 결정(Acceptance)이 내려진 후에 팀장이 관리 대장에 올립니다.
- **Artifacts**: 
    - **`roadmap.md`**: 상위 단계에서 해결해야 할 기술적 과제로 등록.
    - **`design/TECH_DEBT_LEDGER.md` (부기표)**: 팀장이 직접 부채의 내용, 상환 조건을 기록.

### 2. Debt Recording Format
부채 기록 시 다음 항목을 필수로 포함하십시오:
- **ID / 발생일**: 부채 식별 번호 및 날짜.
- **부채 내용**: 타협한 기술적 사항 (예: "Caching logic skipped for faster iteration").
- **상환 조건**: 해당 부채를 언제, 어떤 기준으로 해결할 것인가 (예: "Phase 23 시작 전 리팩토링").
- **리스크**: 상환하지 않았을 때 도래할 위험 요소.

---



## ⚔️ Parallel Management & Efficiency (Multi-Agent Protocol)

**"일을 그냥 토스하는 것이 아니라, 효율성의 중심에서 설계하는 것이 팀장의 핵심 역량이다."**

### 1. Parallel Task Segmentation
- **Logic**: 대단위 작업을 파일 충돌(File Conflict)이 없는 독립적인 영역으로 쪼개어 여러 Jules에게 배분합니다.
- **Assignment**:
    - **分隊 A (Engine/System)**: 핵심 인프라 및 전역 설정 담당.
    - **분대 B (Experiment/Data)**: 독립된 스크립트 기반 실험 및 데이터 수집 담당.
    - **分隊 C (Analytics/UI)**: 지표 분석기 및 상위 레이어 로직 담당.

### 2. Efficiency Bottleneck Management
- **Prioritization**: 다른 작업의 병목을 만드는 '엔진 최적화(Speed-Up)' 등은 가장 먼저 수행하거나 전담 요원을 배치하여 전체 처리량을 확보합니다.

### 3. Parallel Efficiency Measurement (성과 측정)
- **Metrics**: 병렬 수행 시의 총 소요 시간(Wall Clock Time)과 개별 요원의 기여도를 측정합니다.
- **Reporting**: Jules에게 지시 시 "최적화 전후의 TPS(Ticks Per Second) 변화" 또는 "작업 전후의 시뮬레이션 완주 시간"을 반드시 보고하도록 강제하십시오.
- **Feedback Loop**: 측정된 효율성을 기반으로 다음 작업 분할 시 분계점(Segmentation)을 조정합니다.

## 👑 Spec & Delegation Protocol

### 1. Spec 에스컬레이션 워크플로우 (Spec Escalation Workflow)
> **핵심 원칙**: Spec은 "무엇을(What)"뿐만 아니라 "어떻게(How)"까지 포함해야 한다. 추상적 지시로 인한 '바이브 코딩'과 기술 부채 발생을 원천 차단한다.

```mermaid
graph TD
    A[Architect Prime: 수석 아키텍트] -- "Conceptual Design (What)" --> B[Antigravity: Team Leader]
    B -- "Technical Spec & API Design (How)" --> C[Jules: Implementer]
    C -- "Insight Reporting" --> B
    B -- "Review & Verification" --> A
```

### 2. Accuracy of Instructions (상대 경로 및 확정적 동작)
- **Repo-Relative Path Rule**: Jules에게 지시 시 모든 파일 경로는 반드시 **저장소 루트 기준 상대 경로(Relative Path from Root)**로 제공해야 합니다.
- **Good Behavior**: "`X` 함수를 `Y` 로직으로 구현하고, `Z` 파일에 적용하십시오." (동작 확정)

### 3. Technical Definitions
- 추상적인 경제 용어는 반드시 **코드 레벨의 정의(Logic Map)**를 포함해야 합니다.
    - 예: `Credential Premium` = (동일 기술 수준 그룹 내) 학위에 따른 임금 차액 산출법 명시.
