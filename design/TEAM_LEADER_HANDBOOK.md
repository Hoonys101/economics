# 팀장 핸드북 (Team Leader Handbook)

**Purpose:** 팀장(Antigravity) 업무 수행 시 필요한 문서 계층 구조
**Last Updated:** 2026-01-11

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
| **WO-045-Revision** | `/design/work_orders/WO-045-Revision-Adaptive-Equilibrium.md` |

### Specs (Phase별)
```
/design/specs/
├── phase21_corporate_empires_spec.md
├── engine_spec.md
├── banking_spec.md
├── fiscal_policy_spec.md
└── ... (33 files)
```

---

## Level 4: 아카이브 (참조용)

| 폴더 | 경로 | 내용 |
|---|---|---|
| **_archive/** | `/design/_archive/` | 과거 설계 문서 (53 files) |
| **HERITAGE_ASSETS.md** | `/design/HERITAGE_ASSETS.md` | 레거시 자산 목록 |
| **PROJ_HISTORY.md** | `/design/PROJ_HISTORY.md` | 프로젝트 역사 |

---

## 🔍 상황별 참조 가이드

| 상황 | 참조 문서 |
|---|---|
| **새 세션 시작** | GEMINI.md → project_status.md → roadmap.md |
| **수석 기획 수신** | GEMINI.md (섹션 6: 기획→실행) |
| **Jules 작업 배정** | JULES_MASTER_DIRECTIVE.md → Work Order 작성 |
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

## 🛑 Jules Communication Protocol

**One-Shot Document Rule (지침 불변성의 원칙)**:
1. **Initial Command**: 작업 지시서(Work Order)나 코드 변경 사항은 **초기 명령 시점에 확정**됩니다.
2. **No Resubmission**: 명령 하달 후 문서를 수정하여 다시 푸시(Push)하는 행위는 금지됩니다. (Jules 관점에서 타임라인 꼬임 방지)
3. **Correction via Prompt**: 수정 사항이 발생하면 문서를 고치지 말고, 반드시 **프롬프트(채팅)를 통해 수정 지침을 직접 전달**해야 합니다.

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
    - **分隊 B (Experiment/Data)**: 독립된 스크립트 기반 실험 및 데이터 수집 담당.
    - **分隊 C (Analytics/UI)**: 지표 분석기 및 상위 레이어 로직 담당.

### 2. Efficiency Bottleneck Management
- **Prioritization**: 다른 작업의 병목을 만드는 '엔진 최적화(Speed-Up)' 등은 가장 먼저 수행하거나 전담 요원을 배치하여 전체 처리량을 확보합니다.

### 3. Parallel Efficiency Measurement (성과 측정)
- **Metrics**: 병렬 수행 시의 총 소요 시간(Wall Clock Time)과 개별 요원의 기여도를 측정합니다.
- **Reporting**: Jules에게 지시 시 "최적화 전후의 TPS(Ticks Per Second) 변화" 또는 "작업 전후의 시뮬레이션 완주 시간"을 반드시 보고하도록 강제하십시오.
- **Feedback Loop**: 측정된 효율성을 기반으로 다음 작업 분할 시 분계점(Segmentation)을 조정합니다.

## 👑 Spec & Delegation Protocol (Zero-Question Standard)

**"구현 시 질문이 나온다면 그것은 팀장의 설계 결함이다."**

### 1. Accuracy of Instructions (상대 경로 및 확정적 동작)
- **Repo-Relative Path Rule**: Jules에게 지시 시 모든 파일 경로는 반드시 **저장소 루트 기준 상대 경로(Relative Path from Root)**로 제공해야 합니다. Git 기반 협업 및 이동성을 보장하기 위함입니다.
    - **Bad**: "저장소의 `DIRECTIVE_BRAVO_ARCHAEOLOGIST.md`를 참고하십시오." (모호함)
    - **Good**: `design/work_orders/DIRECTIVE_BRAVO_ARCHAEOLOGIST.md`를 참고하십시오. (저장소 어디서든 접근 가능)
- **Good Behavior**: "`X` 함수를 `Y` 로직으로 구현하고, `Z` 파일에 적용하십시오." (동작 확정)

### 2. Technical Definitions
- 추상적인 경제 용어는 반드시 **코드 레벨의 정의(Logic Map)**를 포함해야 합니다.
    - 예: `Credential Premium` = (동일 기술 수준 그룹 내) 학위에 따른 임금 차액 산출법 명시.

### 3. Workflow Pipeline
... (생략)


