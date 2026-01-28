# Jules 문서화 작업 지침서 (Documentation Guide)

이 문서는 `design/` 폴더 내의 빈 명세서(Spec) 파일들을 **실제 코드베이스 분석을 통해** 작성하기 위한 지침입니다. 모든 내용은 **코드에서 직접 추출**해야 하며, 추측이나 가정에 기반한 내용 작성은 **금지**됩니다.

---

## 🛡️ 핵심 원칙

1. **코드 기반 작성**: 모든 문서의 내용은 실제 코드 파일을 분석하여 추출해야 합니다.
2. **추측 금지**: 코드에 명시적으로 존재하지 않는 기능이나 구조를 기술하지 않습니다.
3. **파일 참조 명시**: 문서에 기술된 각 항목의 출처 파일과 라인 번호(가능한 경우)를 명시합니다.
4. **일관된 형식**: 각 문서의 제공된 섹션 헤더를 유지하고 그 하위에 내용을 채웁니다.
5. **인사이트 보고**: 작업 중 발견된 기술 부채나 특이 사항은 반드시 `communications/insights/[Mission_Key].md` 파일에 기록하십시오. 공용 대장(`TECH_DEBT_LEDGER.md`)을 직접 수정하는 것은 충돌 방지를 위해 금지됩니다.

---

## 📂 작업 대상 파일 및 분석 가이드

### 1. `specs/analysis_spec.md` (분석 명세)
**분석 대상 코드**:
- `simulation/metrics/economic_tracker.py`
- `simulation/metrics/inequality_tracker.py`
- `simulation/viewmodels/economic_indicators_viewmodel.py`

**추출해야 할 정보**:
- 어떤 거시 지표들이 계산되는가? (GDP, 실업률, Gini 계수 등)
- 각 지표의 계산 공식은 무엇인가? (코드에서 수식 추출)
- `track()` 메서드의 호출 시점과 데이터 흐름

---

### 2. `specs/data_layer_spec.md` (데이터 계층 명세)
**분석 대상 코드**:
- `simulation/db/schema.py`
- `simulation/db/repository.py`
- `simulation/dtos.py` 또는 `simulation/schemas.py`

**추출해야 할 정보**:
- 데이터베이스 테이블 정의 (테이블명, 컬럼, 타입)
- `SimulationRepository` 클래스의 주요 메서드 목록과 역할
- DTO/Schema 클래스들의 필드 정의

---

### 3. `specs/engine_spec.md` (엔진 명세)
**분석 대상 코드**:
- `simulation/engine.py` (특히 `run_tick` 메서드)
- `simulation/core_markets.py`
- `simulation/markets/order_book_market.py`

**추출해야 할 정보**:
- `run_tick` 메서드의 단계별 실행 흐름 (Decision → Matching → Consumption → Logging → Persistence)
- 각 시장(Market) 클래스의 역할과 주요 메서드
- 에이전트 간 상호작용 순서

---

### 4. `specs/main_integration_spec.md` (통합 명세)
**분석 대상 코드**:
- `app.py` (Flask 라우트 정의)
- `static/js/modules/api.js`
- `static/js/main.js`

**추출해야 할 정보**:
- 정의된 모든 API 엔드포인트 목록 (경로, HTTP 메서드, 역할)
- 각 엔드포인트의 요청/응답 데이터 구조
- 프론트엔드에서 호출하는 API 순서 및 타이밍

---

### 5. `specs/reportAndVisualize.md` (시각화 명세)
**분석 대상 코드**:
- `templates/index.html`
- `static/js/modules/ui.js`
- `static/css/` (스타일 관련)

**추출해야 할 정보**:
- 대시보드에 표시되는 차트 및 UI 컴포넌트 목록
- 각 차트가 사용하는 데이터 필드
- UI 업데이트 로직 (`updateDashboard` 등)

---

### 6. `platform_architecture.md` (플랫폼 아키텍처)
**분석 대상 코드**:
- 프로젝트 루트의 폴더 구조
- `simulation/` 하위 모듈 구조
- `config.py` (설정 상수들)

**추출해야 할 정보**:
- 전체 폴더/모듈 구조 트리
- 각 주요 모듈의 책임 (한 줄 설명)
- 에이전트 종류 (Household, Firm, Government 등) 및 그 역할

---

### 7. `interim_report.md` (중간 보고서)
**분석 대상 코드**:
- 최근 Git 커밋 로그 (`git log -n 20 --oneline`)
- `tests/` 폴더의 테스트 파일 목록
- 실제 테스트 실행 결과 (`pytest` 또는 개별 테스트)

**추출해야 할 정보**:
- 최근 완료된 주요 기능/수정 사항 (커밋 메시지 기반)
- 통과한 테스트 케이스 요약
- 현재 식별된 버그 또는 이슈

---

### 8. `project_status.md` (프로젝트 현황)
**분석 대상 코드**:
- `design/roadmap.md` (로드맵)
- `design/implementation_plan.md` (구현 계획)
- 최근 Git 커밋 및 브랜치 상태

**추출해야 할 정보**:
- 로드맵의 각 항목별 완료 상태
- 현재 진행 중인 작업 (In Progress 항목)
- 알려진 기술 부채 또는 리스크

---

## 📝 작업 완료 기준

각 문서가 다음 조건을 충족해야 작업 완료로 간주합니다:
1. 모든 섹션 헤더 아래에 실제 내용이 채워져 있음
2. 각 내용의 출처 파일이 명시되어 있음 (예: `[engine.py:L120-150]`)
3. `[TODO: Jules]` 태그가 모두 제거됨
4. Mypy나 린트 에러 없이 마크다운 문법이 올바름

---

## 🚀 작업 시작 방법

1. 이 지침서 전체를 숙지합니다.
2. 각 문서를 하나씩 열고, 해당 "분석 대상 코드" 파일들을 읽습니다.
3. 코드에서 추출한 정보를 해당 섹션에 기입합니다.
4. 작업 완료 후 PR을 생성합니다.
