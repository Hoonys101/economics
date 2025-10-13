# 로그 데이터 접근 전략 (Log Data Access Strategy)

## 1. 문제 인식 (Problem Recognition)

현재 시뮬레이션 로그는 수십만 줄에 달하며, 이로 인해 다음과 같은 문제점이 발생합니다:
- **로그 파일 직접 분석의 비효율성:** 대규모 로그 파일을 직접 읽고 파싱하는 것은 비효율적이며, Gemini CLI의 컨텍스트 한계를 초과합니다.
- **웹 UI 데이터 접근의 필요성:** 최종 웹 애플리케이션(app.py)은 현재 시장 현황 및 과거 데이터를 효율적으로 조회하고 시각화해야 합니다. 현재 로그 파일 기반으로는 이러한 요구사항을 충족하기 어렵습니다.

## 2. 제안된 해결 방법 (Proposed Solution)

로그 파일 대신 구조화된 데이터베이스를 활용하고, MVVM(Model-View-ViewModel) 패턴을 적용하여 데이터 접근 계층을 설계합니다. 이를 통해 로그 데이터의 효율적인 저장, 조회 및 웹 UI와의 통합을 달성합니다.

### 2.1. 기술 스택 (Technology Stack)
- **데이터베이스:** SQLite3 (경량이며 파일 기반으로 관리 용이)
- **데이터 접근 패턴:** Repository Pattern
- **아키텍처 패턴:** MVVM (Model-View-ViewModel)

### 2.2. 아키텍처 설계 (Architecture Design)

#### Model (데이터 모델)
- 시뮬레이션에서 발생하는 주요 이벤트(거래, 생산, 소비, 에이전트 상태 변화 등)를 저장할 SQLite3 테이블 스키마를 정의합니다.
- `simulation_results.csv`와 같은 현재 CSV 출력 데이터를 대체하거나 보완하는 형태로 설계합니다.
- 예시 테이블: `transactions`, `agent_states`, `market_history`, `economic_indicators`

#### Repository (데이터 접근 계층)
- SQLite3 데이터베이스에 대한 CRUD(Create, Read, Update, Delete) 작업을 추상화하는 Repository 클래스를 구현합니다.
- 시뮬레이션 엔진은 직접적으로 데이터베이스에 접근하지 않고, Repository 인터페이스를 통해 데이터를 저장합니다.
- ViewModel은 Repository를 통해 필요한 데이터를 조회합니다.
- 주요 기능:
    - `save_transaction(transaction_data)`
    - `get_market_history(market_id, start_tick, end_tick)`
    - `get_agent_state(agent_id, tick)`
    - `get_economic_indicators(start_tick, end_tick)`

#### ViewModel (UI 로직 및 데이터 준비)
- 웹 UI(View)에 필요한 데이터를 준비하고, UI의 사용자 상호작용을 처리하는 로직을 포함합니다.
- Repository를 통해 데이터를 조회하고, 이를 View가 쉽게 렌더링할 수 있는 형태로 가공합니다.
- 웹 UI의 각 페이지/컴포넌트에 대응하는 ViewModel을 설계합니다.
- 예시 ViewModel: `MarketHistoryViewModel`, `AgentDashboardViewModel`, `EconomicOverviewViewModel`

#### View (웹 UI)
- Flask 기반의 `app.py`와 `index.html`을 활용하여 ViewModel이 제공하는 데이터를 시각적으로 표현합니다.
- Chart.js와 같은 라이브러리를 사용하여 시계열 데이터 및 경제 지표를 그래프로 표시합니다.

## 3. 구현 계획 (Implementation Plan)

1.  **SQLite3 데이터베이스 스키마 설계:**
    - `simulation/db/schema.py` 파일에 SQLite3 테이블 정의 및 관계를 명시합니다.
    - `simulation/db/database.py` 파일에 데이터베이스 연결 및 초기화 로직을 구현합니다.
2.  **Repository 구현:**
    - `simulation/db/repository.py` 파일에 `SimulationRepository` 클래스를 구현합니다.
    - 시뮬레이션 엔진이 이 Repository를 통해 데이터를 저장하도록 `simulation/engine.py`를 수정합니다.
3.  **ViewModel 설계 및 구현:**
    - `simulation/viewmodels/` 디렉토리를 생성하고, 필요한 ViewModel 클래스들을 정의합니다.
    - `app.py`에서 이 ViewModel을 활용하여 데이터를 웹 UI에 전달합니다.
4.  **웹 UI (`app.py`, `index.html`) 수정:**
    - ViewModel과 연동하여 데이터를 표시하도록 UI 로직을 업데이트합니다.
    - Chart.js 등을 활용하여 시각화를 구현합니다.

## 4. 기대 효과 (Expected Benefits)

- **성능 향상:** 대규모 로그 파일 파싱 없이 데이터베이스에서 직접 데이터를 조회하여 웹 UI의 응답 속도를 크게 개선합니다.
- **데이터 접근의 용이성:** 구조화된 쿼리를 통해 특정 시점 또는 특정 에이전트의 데이터를 쉽게 추출할 수 있습니다.
- **유지보수성:** MVVM 패턴 적용으로 UI 로직과 데이터 로직이 분리되어 코드의 유지보수성이 향상됩니다.
- **확장성:** 향후 데이터 분석 및 시각화 기능을 쉽게 추가할 수 있는 기반을 마련합니다.
