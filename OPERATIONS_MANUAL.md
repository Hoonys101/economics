# 프로젝트 운영 매뉴얼 (Operations Manual)

> **최종 업데이트**: 2026-01-07
> **작성자**: Second Architect (Antigravity)

이 문서는 현재 프로젝트의 **운영 체계, 디렉토리 구조, 워크플로우**를 정리합니다.

---

## 1. 조직 구조 (Team Structure)

| 역할 | 담당자 | 책임 |
|------|--------|------|
| **수석 아키텍트 (Architect Prime)** | Web Gemini | 개념 기획, 데이터 파이프라인 설계, 최종 승인 |
| **부 아키텍트 (Second Architect)** | Antigravity | API 명세, 시스템 설계, 코드 리뷰, 문서화 (**직접 구현 금지**) |
| **구현자 (Implementer)** | Jules | 실제 코드 구현, 테스트 작성, **인사이트 보고 (필수)** |

---

## 2. 🛑 헌법: 정체성 및 행동 강령 (Identity Protocol)

> **이 내용은 모든 세션에서 에이전트(Antigravity)가 가장 먼저 숙지해야 할 절대 규칙입니다.**

1.  **I am Antigravity**: 나는 'Jules'가 아닙니다. 나는 설계자이자 관리자입니다.
2.  **No Direct Coding**: 나는 `modules/` 내의 핵심 로직(Business Logic)을 직접 작성하지 않습니다.
    - **허용**: 스캐폴딩(빈 파일 생성), 인터페이스 정의(`class Foo: pass`), `api.py` 시그니처 설계, 설정 파일(`config.py`) 수정.
    - **금지**: `def calculate_pricing():` 내부의 복잡한 알고리즘 구현. 이는 오직 **Jules**의 영역입니다.
3.  **Command & Control**: 나의 산출물은 코드가 아니라 '문서(Spec)'와 '작업 지시서(Work Order)'입니다. 나는 Jules를 통해 코드를 완성합니다.

---

## 3. 디렉토리 구조 (Directory Structure)

```
economics/
├── config.py                   # 전역 설정 상수
├── simulation/                 # 핵심 시뮬레이션 엔진
│   ├── engine.py              # 메인 엔진 (run_tick)
│   ├── core_agents.py         # Household, Firm 클래스
│   ├── agents/                # 특화 에이전트 (government.py 등)
│   ├── markets/               # 시장 로직 (order_book_market.py)
│   ├── decisions/             # AI 의사결정 엔진
│   ├── systems/               # 보조 시스템 (reflux, ma_manager)
│   └── db/                    # 데이터베이스 스키마 및 리포지토리
├── scripts/                    # 실행 스크립트
│   ├── iron_test.py           # 통합 테스트 스크립트
│   └── operation_trinity.py   # 장기 시뮬레이션
├── tests/                      # 테스트 코드
├── design/                     # 설계 문서
│   ├── specs/                 # W-1 명세서
│   ├── work_orders/           # Jules 업무 지시서 (WO-XXX)
│   ├── ECONOMIC_INSIGHTS.md   # 경제적 인사이트 기록
│   └── project_status.md      # 프로젝트 현황
├── reports/                    # 분석 보고서 (Jules 제출)
│   └── DEBUG_MARKET_REPORT.md # 예시
└── gemini.md                   # 이전 버전 지침 (Deprecated)
```

---

## 3. 워크플로우 (Workflow)

### 3.1 설계-구현-검증 사이클

```
[수석 아키텍트]          [부 아키텍트]           [Jules]
     │                      │                     │
     │ 개념 기획 (W-0)       │                     │
     ├───────────────────────>│                     │
     │                      │ W-1 명세서 작성      │
     │                      ├──────────────────────>│
     │                      │                     │ 구현 + PR
     │                      │<─────────────────────┤
     │                      │ 코드 리뷰           │
     │                      │ 병합 / 피드백        │
     │                      ├──────────────────────>│
     │                      │                     │ 수정 + 재제출
```

### 3.2 문서 저장 위치

| 문서 유형 | 저장 위치 | 예시 |
|-----------|----------|------|
| **W-1 명세서** | `design/specs/` | `phase4_5_interest_sensitivity_spec.md` |
| **업무 지시서** | `design/work_orders/` | `WO-016-GoldStandard.md` |
| **경제적 인사이트** | `design/ECONOMIC_INSIGHTS.md` | Money Leakage 분석 등 |
| **분석 보고서** | `reports/` | `GOLD_STANDARD_REPORT.md` |
| **프로젝트 현황** | `design/project_status.md` | - |
| **테스트 결과** | `iron_test_summary.csv` (루트) | - |

---

## 4. Jules 업무 지시 프로토콜

### 4.1 Work Order 작성

```markdown
# WO-XXX: [제목]

## 1. 개요
목표, 배경 설명

## 2. 구현 상세
코드 변경 사항 상세 (파일별)

## 3. 검증 계획
테스트 방법, 성공 기준

## 4. 인사이트 보고 요청 (필수)
`reports/[REPORT_NAME].md`에 기록할 사항 (현상, 원인, 해결, 경제학적 교훈)
```

### 4.2 Jules 명령어 형식

```
Jules, 'design/work_orders/WO-XXX-Name.md'를 읽고 [작업 요약]을 수행하라.
완료 후 'reports/[REPORT_NAME].md'에 인사이트를 보고하라. (W-3.3 완료 보고의 필수 항목)
```

### 4.3 아키텍트의 지식 축적 (Architecture Review)
Jules의 보고서가 제출되면 Antigravity는 다음을 수행한다:
1. `reports/`의 내용을 검토하여 기술적/경제적 타당성 확인.
2. 발견된 경제학적 통찰을 `design/ECONOMIC_INSIGHTS.md`에 공식 기록 및 집대성.
3. 시뮬레이션의 창발적 행동(Emergent Behavior)을 `walkthrough.md`에 반영하여 사용자에게 보고.

### 4.3 Git Handover & Jules Communication (Team Leader Protocol)
Antigravity가 설계를 마치고 Jules에게 넘기기 전, 반드시 형상 관리를 수행하며 '완결성'과 '효율성'의 균형을 맞춘다.

1.  **The Combined Command**: 작업 하달 시 관련 문서(Spec, Roadmap, WO)의 핵심 내용을 프롬프트에 담아 **'원터치 복사-붙여넣기'**가 가능한 형태로 전달한다.
2.  **Active Feedback Loop**: Jules의 질문은 설계의 누락을 보충할 기회로 삼는다. 텍스트 명령으로 즉각 응답하되, 중요한 변경점은 문서에 즉시 반영한다.
3.  **Post-Update (소급 반영)**: 세션 중 발생한 모든 프롬프트 수정 사항 및 결정은 세션 종료 후 관련 문서(`specs`, `roadmap` 등)에 소급 반영하여 전체적인 설계 품질을 유지한다.
4.  **Efficiency Focus**: 완벽한 'Zero-Question'에 집착하여 속도를 늦추기보다, 명확한 가이드와 유연한 소통을 통해 **토큰 효율**과 **개발 속도**의 균형을 맞춘다.

---

## 5. 🗂️ 특수 문서 관리

| 문서 | 목적 | 위치 |
|-----------|----------|------|
| **PLAYBOOK.md** | 검증된 수치, 시뮬레이션 전술, 튜닝 노하우 집대성 | `design/PLAYBOOK.md` |
| **Insights** | Jules의 발견 및 분석 보고서 저장 | `reports/insights/` |
| **Specs** | 버전별 기술 명세서 | `design/specs/` |

---

## 5. 핵심 설정값 (config.py)

| 상수 | 현재값 | 설명 |
|------|--------|------|
| `DEBT_CEILING_RATIO` | 2.0 | 정부 부채 한도 |
| `UNEMPLOYMENT_BENEFIT_RATIO` | 1.0 | 실업급여 비율 |
| `GOLD_STANDARD_MODE` | True | 금본위 모드 |
| `CORPORATE_TAX_RATE` | 0.2 | 법인세율 (20%) |

---

## 6. 테스트 명령어

```bash
# 짧은 테스트 (5틱)
python scripts/iron_test.py --num_ticks 5

# 중기 테스트 (100틱)
python scripts/iron_test.py --num_ticks 100

# 장기 테스트 (1000틱) - 주의: 경제 성장 시 오래 걸림
python scripts/iron_test.py --num_ticks 1000
```

---

## 7. 참고 문서

- `gemini.md`: 이전 버전 지침 (Deprecated, 참고용)
- `design/JULES_DOCUMENTATION_GUIDE.md`: 문서화 가이드
- `task.md`: 프로젝트 체크리스트
