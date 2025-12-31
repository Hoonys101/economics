# W-1 Specification: [W-2] Economic Control Tower

본 문서는 Jules 및 프론트엔드 작업자가 추가 질문 없이 즉시 개발에 착수할 수 있도록 설계된 상세 명세서입니다.

---

## 1. 인터페이스 계약 (The Contract)

### 1.1 API Endpoint
- **URL**: `GET /api/simulation/dashboard`
- **Method**: `GET`
- **Response Type**: `application/json`

### 1.2 Data Schema (DTOs)
Jules는 `simulation/dtos.py`에 정의된 다음 구조를 사용하여 데이터를 반환해야 한다:
- `DashboardSnapshotDTO`: 최상위 컨테이너.
- `DashboardGlobalIndicatorsDTO`: HUD 데이터.
- `SocietyTabDataDTO`: 인구/사회 탭 (세대 통계 포함).
- `GovernmentTabDataDTO`: 재정/세금 탭.
- `MarketTabDataDTO`: 실물 시장 탭 (CPI, Maslow).
- `FinanceTabDataDTO`: 금융 시장 탭 (시총, 거래량).

---

## 2. 모듈 상세 설계 (Micro-Design)

### 2.1 Backend Aggregator (Jules 담당)
- **로직**: `simulation/viewmodels/snapshot_viewmodel.py`를 생성하고 `get_dashboard_snapshot()` 메서드를 구현한다.
    1. `SimulationRepository.get_latest_economic_indicator()`를 호출하여 HUD의 대부분 지표를 가져온다.
    2. `SimulationRepository.get_wealth_distribution()` (또는 `InequalityTracker` 데이터)를 통해 지니계수와 5분위 데이터를 가져온다.
    3. `SimulationRepository.get_generation_stats(tick)`를 호출하여 세대 분포를 가져온다.
    4. `Government.tax_records`를 집계하여 세수 분포를 계산한다.
    5. `MarketHistory`에서 최근 N틱의 거래량과 가격을 가져와 CPI와 품목별 추이를 계산한다.
- **API 구현**: `app.py`에 `/api/simulation/dashboard` 라우트를 추가하고 위 ViewModel을 호출하여 결과를 반환한다.

### 2.2 Frontend Components (Assistant 담당)
- **Vite 프로젝트 초기화**: `frontend/` 폴더 내에 React + TS 프로젝트를 생성한다.
- **Shadcn/UI 설치**: Button, Tabs, Card, Table 컴포넌트를 설치한다.
- **Recharts**: 각 탭에 필요한 차트(Area, Bar, Pie, Radar)를 구현한다.
- **상태 관리**: `useSimulation` 훅을 통해 데이터를 1초 간격으로 폴링하고, 전역 상태로 관리한다.

---

## 3. Work Order for Jules (구현 지침)
"Jules, 아래 순서대로 백엔드 작업을 완료하고 보고하라."
1.  **Repository 검색**: `SimulationRepository`에 `get_generation_stats`가 구현되어 있으니 이를 활용하라.
2.  **ViewModel 생성**: `simulation/viewmodels/snapshot_viewmodel.py`를 만들고, `DashboardSnapshotDTO`를 조립하는 로직을 작성하라.
3.  **API 노출**: `app.py`에서 프로젝트의 핵심 관제 라우트인 `/api/simulation/dashboard`를 활성화하라.
4.  **검증**: `tests/test_dashboard_api.py`를 작성하여 JSON 형식이 계약서와 일치하는지 확인하라.

---

## 3. 예외 처리 및 방어적 설계
- **Empty Data**: 시뮬레이션 초기(tick 0)에는 모든 값을 기본값(0.0)으로 반환하여 프론트엔드 크래시 방지.
- **Performance**: `InequalityTracker` 호출 시 매번 O(N log N) 정렬이 발생하므로, 가계 수가 1000명 이상일 경우 5틱마다 한 번씩만 계산하는 캐싱 로직 고려.

## 4. Work Order (지침)
- **Jules**: `simulation/viewmodels/snapshot_viewmodel.py`를 신설하여 집계 로직을 캡슐화하고, `app.py`에서 이를 호출하도록 구현하라.
- **Assistant**: `frontend/` 디렉토리를 생성하고 `npx create-vite@latest`를 통해 React/TS 설정을 하라.
