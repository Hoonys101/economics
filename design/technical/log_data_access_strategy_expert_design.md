## 1. 시스템 아키텍처 사양 (System Architecture Specifications)

### 1.1. 컴포넌트 다이어그램 (Component Diagrams)

```mermaid
graph TD
    subgraph "Simulation Core"
        A[Simulation Engine] --> B(Repository Interface)
        C[Agents (Household, Firm)] --> A
        D[Markets (Goods, Labor, Loan)] --> A
    end

    subgraph "Data Layer"
        B --> E[SQLite3 Database]
        E -- "Schema: Transactions, AgentStates, MarketHistory, EconomicIndicators" --> F[Database Files (.db)]
    end

    subgraph "Web Application"
        G[Flask App (app.py)] --> H[ViewModel Layer]
        H --> B
        I[Web UI (index.html)] --> G
    end

    subgraph "External Tools"
        J[Data Analysis Tools (e.g., Pandas)] --> B
    end

    A -- "Writes data via Repository" --> B
    H -- "Reads data via Repository" --> B
    J -- "Reads data via Repository" --> B
```

**설명:**
- **Simulation Engine:** 시뮬레이션의 핵심 로직을 담당하며, 에이전트 및 시장과의 상호작용을 통해 데이터를 생성합니다. 생성된 데이터는 Repository Interface를 통해 SQLite3 데이터베이스에 저장됩니다.
- **Repository Interface:** 시뮬레이션 코어와 데이터베이스 간의 느슨한 결합(Loose Coupling)을 보장하는 추상화 계층입니다. 시뮬레이션 엔진과 ViewModel은 이 인터페이스를 통해 데이터에 접근합니다.
- **SQLite3 Database:** 시뮬레이션에서 발생하는 모든 영구 데이터를 저장하는 경량의 파일 기반 데이터베이스입니다.
- **ViewModel Layer:** 웹 UI에 필요한 데이터를 준비하고, Repository를 통해 데이터를 조회하여 UI 친화적인 형태로 가공합니다.
- **Flask App (app.py):** 웹 요청을 처리하고 ViewModel을 호출하여 데이터를 가져와 Web UI에 전달합니다.
- **Web UI (index.html):** Flask App으로부터 받은 데이터를 시각적으로 표현합니다.
- **Data Analysis Tools:** Pandas와 같은 외부 분석 도구도 Repository Interface를 통해 데이터베이스에 접근하여 시뮬레이션 결과를 분석할 수 있습니다.

### 1.2. 확장성 계획 (Scalability Plans)

- **데이터 계층:**
    - **SQLite3의 한계:** 현재는 경량의 파일 기반 SQLite3를 사용하지만, 시뮬레이션 규모가 커지거나 동시 접근이 많아질 경우 성능 병목이 발생할 수 있습니다.
    - **성장 전략:** 10x 성장 시나리오를 대비하여, Repository Interface는 PostgreSQL, MySQL 등 더 강력한 관계형 데이터베이스로의 전환을 용이하게 설계합니다. 데이터베이스 마이그레이션 시 Repository 구현체만 변경하면 되도록 추상화 수준을 유지합니다.
    - **데이터 파티셔닝/샤딩:** 장기적으로 데이터 양이 매우 커질 경우, 시간 기반 또는 에이전트 ID 기반의 데이터 파티셔닝/샤딩 전략을 고려할 수 있습니다.
- **시뮬레이션 엔진:**
    - **병렬 시뮬레이션:** 단일 시뮬레이션 실행 시간을 줄이기 위해, 여러 시뮬레이션 틱을 병렬로 처리하거나 여러 시뮬레이션 인스턴스를 동시에 실행하는 방안을 고려합니다. 이 경우, Repository는 동시 쓰기(Concurrent Write)를 안전하게 처리할 수 있어야 합니다.
- **웹 애플리케이션:**
    - **수평 확장:** Flask 앱은 stateless하게 설계하여 로드 밸런서 뒤에서 여러 인스턴스를 실행하여 트래픽 증가에 대응할 수 있도록 합니다.
    - **캐싱:** ViewModel 계층 또는 Flask 앱에 캐싱 메커니즘(Redis 등)을 도입하여 자주 조회되는 데이터에 대한 데이터베이스 부하를 줄입니다.

### 1.3. 기술 결정 (Technology Decisions)

- **데이터베이스:** `SQLite3`
    - **선정 이유:** 경량이며 설정이 필요 없고 파일 기반으로 관리가 용이하여 개발 초기 단계 및 소규모 시뮬레이션에 적합합니다. Repository 패턴을 통해 향후 다른 DB로의 전환 비용을 최소화합니다.
    - **트레이드오프:** 동시성 제어 및 대규모 데이터 처리 성능에 한계가 있습니다.
- **데이터 접근:** `Repository Pattern`
    - **선정 이유:** 데이터 저장소(SQLite3)와 비즈니스 로직(Simulation Engine, ViewModel) 간의 의존성을 분리하여 코드의 유연성, 테스트 용이성, 유지보수성을 극대화합니다.
- **아키텍처 패턴:** `MVVM`
    - **선정 이유:** 웹 UI(View)와 비즈니스 로직(ViewModel)을 명확히 분리하여 UI 개발의 독립성과 테스트 용이성을 확보합니다. ViewModel은 View에 특화된 데이터를 제공하여 View의 복잡성을 줄입니다.
- **웹 프레임워크:** `Flask`
    - **선정 이유:** 경량이며 유연하여 시뮬레이션 데이터 시각화와 같은 특정 목적의 웹 애플리케이션 개발에 적합합니다.
- **프론트엔드 라이브러리:** `Chart.js` (예시)
    - **선정 이유:** 시계열 데이터 및 다양한 경제 지표를 시각적으로 표현하는 데 효과적입니다.

### 1.4. 통합 패턴 (Integration Patterns)

- **시뮬레이션 엔진 ↔ Repository:**
    - **패턴:** 의존성 주입(Dependency Injection)을 통해 Simulation Engine이 Repository Interface의 구현체를 주입받아 사용합니다.
    - **설계:** Simulation Engine은 `save_transaction`, `save_agent_state`, `save_economic_indicator` 등 Repository의 쓰기(Write) 메서드를 호출합니다.
- **ViewModel ↔ Repository:**
    - **패턴:** ViewModel은 Repository Interface를 통해 필요한 데이터를 조회합니다.
    - **설계:** ViewModel은 `get_market_history`, `get_agent_history` 등 Repository의 읽기(Read) 메서드를 호출합니다.
- **Flask App ↔ ViewModel:**
    - **패턴:** Flask 라우트 핸들러는 ViewModel 인스턴스를 생성하고, ViewModel의 메서드를 호출하여 UI에 필요한 데이터를 가져옵니다.
    - **설계:** Flask는 JSON API 엔드포인트를 제공하여 ViewModel이 가공한 데이터를 웹 UI에 전달합니다.
- **외부 분석 도구 ↔ Repository:**
    - **패턴:** Repository는 데이터베이스 파일에 직접 접근하거나, Repository Interface를 통해 데이터를 조회하는 유틸리티 함수를 제공합니다.
    - **설계:** Python 스크립트(예: `analyze_simulation.py`)는 Repository를 임포트하여 데이터베이스에서 데이터를 읽고 Pandas DataFrame으로 변환하여 분석합니다.

---

## 2. API 설계 문서 (API Design Documentation)

### 2.1. 엔드포인트 사양 (Endpoint Specifications)

Flask 앱은 ViewModel을 통해 데이터를 제공하는 RESTful API 엔드포인트를 노출합니다.

- **`GET /api/economic_indicators`**
    - **설명:** 전체 시뮬레이션의 경제 지표 시계열 데이터를 조회합니다.
    - **쿼리 파라미터:**
        - `start_tick` (int, optional): 조회 시작 틱.
        - `end_tick` (int, optional): 조회 종료 틱.
    - **응답:** `List[EconomicIndicatorData]` (JSON 배열)
    ```json
    [
        {
            "time": 1,
            "unemployment_rate": 5.2,
            "avg_wage": 1500.0,
            "food_avg_price": 10.5,
            "total_production": 1000.0,
            ...
        }
    ]
    ```

- **`GET /api/market_history/<market_id>`**
    - **설명:** 특정 시장의 거래 내역 또는 가격 변동 이력을 조회합니다.
    - **URL 파라미터:**
        - `market_id` (string, required): 시장 ID (예: "goods_market", "labor_market").
    - **쿼리 파라미터:**
        - `start_tick` (int, optional): 조회 시작 틱.
        - `end_tick` (int, optional): 조회 종료 틱.
        - `item_id` (string, optional): 특정 상품/서비스에 대한 필터.
    - **응답:** `List[MarketHistoryData]` (JSON 배열)
    ```json
    [
        {
            "time": 1,
            "item_id": "food",
            "avg_price": 10.2,
            "trade_volume": 500.0,
            ...
        }
    ]
    ```

- **`GET /api/agent_state/<agent_id>`**
    - **설명:** 특정 에이전트(가계 또는 기업)의 시간 경과에 따른 상태 변화를 조회합니다.
    - **URL 파라미터:**
        - `agent_id` (int, required): 에이전트 ID.
    - **쿼리 파라미터:**
        - `start_tick` (int, optional): 조회 시작 틱.
        - `end_tick` (int, optional): 조회 종료 틱.
    - **응답:** `List[AgentStateData]` (JSON 배열)
    ```json
    [
        {
            "time": 1,
            "agent_id": 101,
            "assets": 1000.0,
            "is_employed": true,
            "needs_survival": 50.0,
            ...
        }
    ]
    ```

### 2.2. 데이터 모델 (Data Models)

SQLite3 데이터베이스에 저장될 주요 엔티티의 스키마 정의 (Python 클래스 또는 SQLAlchemy 모델로 구현 예정).

- **`Transaction` (거래)**
    - `id` (INTEGER PRIMARY KEY)
    - `time` (INTEGER)
    - `buyer_id` (INTEGER)
    - `seller_id` (INTEGER)
    - `item_id` (TEXT)
    - `quantity` (REAL)
    - `price` (REAL)
    - `market_id` (TEXT)
    - `transaction_type` (TEXT)

- **`AgentState` (에이전트 상태)**
    - `id` (INTEGER PRIMARY KEY)
    - `time` (INTEGER)
    - `agent_id` (INTEGER)
    - `agent_type` (TEXT, 'household' or 'firm')
    - `assets` (REAL)
    - `is_active` (BOOLEAN)
    - `is_employed` (BOOLEAN, for Household)
    - `employer_id` (INTEGER, for Household)
    - `needs_survival` (REAL, for Household)
    - `needs_labor` (REAL, for Household)
    - `inventory_food` (REAL, for Household/Firm)
    - `current_production` (REAL, for Firm)
    - `num_employees` (INTEGER, for Firm)
    - ... (필요한 다른 에이전트 속성)

- **`MarketHistory` (시장 이력)**
    - `id` (INTEGER PRIMARY KEY)
    - `time` (INTEGER)
    - `market_id` (TEXT)
    - `item_id` (TEXT)
    - `avg_price` (REAL)
    - `trade_volume` (REAL)
    - `best_ask` (REAL)
    - `best_bid` (REAL)

- **`EconomicIndicator` (경제 지표)**
    - `id` (INTEGER PRIMARY KEY)
    - `time` (INTEGER)
    - `unemployment_rate` (REAL)
    - `avg_wage` (REAL)
    - `food_avg_price` (REAL)
    - `total_production` (REAL)
    - `total_consumption` (REAL)
    - ... (EconomicIndicatorTracker에서 기록하는 모든 지표)

### 2.3. 인증 설계 (Authentication Design)

- **초기 단계:** 시뮬레이션 데이터는 민감하지 않으므로, 초기 개발 단계에서는 별도의 인증 메커니즘을 구현하지 않습니다.
- **향후 확장:** 시뮬레이션 결과에 대한 접근 제어가 필요해질 경우, Flask-Login과 같은 라이브러리를 활용하여 세션 기반 인증 또는 JWT(JSON Web Token) 기반 인증을 도입할 수 있습니다.

### 2.4. 오류 처리 (Error Handling)

- **API 응답:** 모든 API 엔드포인트는 일관된 JSON 형식의 오류 응답을 반환합니다.
    ```json
    {
        "status": "error",
        "message": "Error description",
        "code": 500
    }
    ```
- **데이터베이스 오류:** Repository 계층에서 발생하는 데이터베이스 관련 오류는 적절히 로깅하고, ViewModel 계층으로 전파하여 사용자에게 의미 있는 메시지로 변환합니다.
- **입력 유효성 검사:** API 엔드포인트는 쿼리 파라미터 및 URL 파라미터에 대한 유효성 검사를 수행하고, 유효하지 않은 입력에 대해서는 400 Bad Request 응답을 반환합니다.

---

## 3. 사용자 인터페이스 아키텍처 (User Interface Architecture)

- **컴포넌트 계층 구조:**
    - `index.html`은 시뮬레이션 대시보드의 메인 레이아웃을 정의합니다.
    - Chart.js와 같은 라이브러리를 사용하여 각 경제 지표, 시장 이력, 에이전트 상태를 시각화하는 재사용 가능한 UI 컴포넌트(예: `LineChartComponent`, `BarChartComponent`, `AgentCardComponent`)를 구성합니다.
    - 각 컴포넌트는 ViewModel로부터 데이터를 받아 렌더링합니다.
- **접근성 프레임워크:**
    - WCAG(Web Content Accessibility Guidelines)를 준수하여 모든 사용자가 시뮬레이션 결과를 이해하고 상호작용할 수 있도록 설계합니다. (예: 차트의 대체 텍스트, 키보드 내비게이션 지원).
- **성능 아키텍처:**
    - **비동기 데이터 로딩:** 웹 UI는 API 엔드포인트로부터 데이터를 비동기적으로 로딩하여 UI 응답성을 유지합니다.
    - **데이터 필터링/페이징:** 대규모 데이터셋을 효율적으로 처리하기 위해 ViewModel 및 API 계층에서 데이터 필터링 및 페이징 기능을 제공합니다.
    - **클라이언트 측 렌더링:** Chart.js와 같은 라이브러리를 활용하여 클라이언트 측에서 차트를 렌더링하여 서버 부하를 줄입니다.
- **반응형 디자인:**
    - 모바일 우선(Mobile-first) 접근 방식을 채택하여 다양한 화면 크기(데스크톱, 태블릿, 모바일)에서 최적의 사용자 경험을 제공합니다. CSS 미디어 쿼리 및 유연한 레이아웃을 활용합니다.

---

## 4. 구현 지침 (Implementation Guidance)

- **개발 로드맵:**
    1.  **데이터베이스 스키마 정의 및 초기화:** `simulation/db/schema.py`, `simulation/db/database.py` 구현.
    2.  **Repository 구현:** `simulation/db/repository.py` 구현 및 시뮬레이션 엔진(`simulation/engine.py`) 수정하여 Repository 사용.
    3.  **ViewModel 구현:** `simulation/viewmodels/` 디렉토리 생성 및 ViewModel 클래스 정의.
    4.  **Flask API 엔드포인트 구현:** `app.py`에 ViewModel을 활용하는 API 엔드포인트 추가.
    5.  **웹 UI 연동:** `index.html` 수정하여 API 데이터 시각화.
- **품질 게이트:**
    - **단위 테스트:** Repository, ViewModel, Flask API 엔드포인트에 대한 단위 테스트를 `pytest`로 작성합니다.
    - **통합 테스트:** 시뮬레이션 엔진과 Repository 간의 통합, Flask API와 ViewModel 간의 통합을 검증하는 테스트를 작성합니다.
    - **코드 리뷰:** 모든 코드 변경 사항은 동료 개발자(또는 Gemini)의 코드 리뷰를 거쳐 품질을 확보합니다.
- **위험 완화:**
    - **데이터 마이그레이션:** SQLite3 스키마 변경 시 기존 데이터의 마이그레이션 전략을 수립합니다. (예: Alembic 사용 고려)
    - **성능 병목:** 초기 단계에서는 SQLite3로 시작하되, 시뮬레이션 규모가 커질 경우 데이터베이스 전환을 위한 계획을 미리 수립합니다.
    - **데이터 일관성:** 시뮬레이션 엔진에서 데이터베이스에 데이터를 저장할 때 트랜잭션(Transaction)을 사용하여 데이터 일관성을 보장합니다.
- **성공 지표:**
    - **웹 UI 응답 시간:** 주요 대시보드 페이지 로딩 시간이 2초 이내.
    - **데이터 정확성:** 웹 UI에 표시되는 데이터가 시뮬레이션 결과와 100% 일치.
    - **시뮬레이션 실행 안정성:** 데이터베이스 저장으로 인한 시뮬레이션 성능 저하가 10% 이내.
    - **코드 유지보수성:** MVVM 및 Repository 패턴 적용으로 코드 복잡도 감소 및 신규 기능 추가 용이성 향상.

---
This comprehensive design specification integrates the various expert perspectives to provide a robust and scalable foundation for the new log data access strategy.