# 프로젝트 운영 매뉴얼 (Operations Manual)

> **최종 업데이트**: 2026-01-07
> **작성자**: Second Architect (Antigravity)

이 문서는 현재 프로젝트의 **운영 체계, 디렉토리 구조, 워크플로우**를 정리합니다.

---

## 1. 조직 구조 (Team Structure)

| 역할 | 담당자 | 책임 |
|------|--------|------|
| **수석 아키텍트 (Architect Prime)** | Web Gemini | 개념 기획, 데이터 파이프라인 설계, 최종 승인 |
| **부 아키텍트 (Second Architect)** | Antigravity | API 명세, 시스템 설계, 코드 리뷰, 문서화 |
| **구현자 (Implementer)** | Jules | 실제 코드 구현, 테스트 작성, 인사이트 보고 |

---

## 2. 디렉토리 구조 (Directory Structure)

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

## 4. 인사이트 보고 요청 (선택)
`reports/[REPORT_NAME].md`에 기록할 사항
```

### 4.2 Jules 명령어 형식

```
Jules, 'design/work_orders/WO-XXX-Name.md'를 읽고 [작업 요약]을 수행하라.
완료 후 'reports/[REPORT_NAME].md'에 인사이트를 보고하라.
```

### 4.3 Git Handover Protocol (Team Leader Rule)
Antigravity가 설계를 마치고 Jules에게 넘기기 전, 반드시 형상 관리를 수행한다.

1.  **Stage & Commit**:
    ```bash
    git add .
    git commit -m "docs: hand over WO-XXX to Jules"
    ```
2.  **Push**:
    ```bash
    git push origin <current_branch>
    ```
3.  **Prompt Generation**:
    사용자가 복사해서 Jules에게 붙여넣을 수 있는 **'명령 프롬프트'**를 생성하여 전달한다.

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
