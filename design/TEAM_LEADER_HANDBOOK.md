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
