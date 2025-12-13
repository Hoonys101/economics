# 설계 문서: DB 기반 MVC 아키텍처 전환

## 1. 개요

이 문서는 기존의 시뮬레이션 아키텍처를 **데이터베이스(DB) 기반의 모델-뷰-컨트롤러(MVC) 구조**로 전환하기 위한 종합적인 설계와 실행 계획을 정의합니다. 이 전환의 목표는 다음 문제를 해결하는 것입니다.

*   **리소스 비효율:** `stdio`를 통한 과도한 로그 출력으로 인한 I/O 병목 및 CPU 낭비.
*   **메모리 문제:** 시뮬레이션이 진행될수록 메모리 사용량이 무한정 증가하는 구조.
*   **데이터 활용의 어려움:** 틱별 상태 정보가 휘발되거나 분석하기 어려운 형태로 존재.
*   **강한 결합도:** 시뮬레이션 로직(Model)과 UI(View)가 강하게 결합되어 유지보수 및 확장이 어려움.

---

## 2. 메인 설계: DB 스키마 및 데이터 흐름

### 2.1. SQLite 데이터베이스 스키마

시뮬레이션의 모든 상태를 구조적으로 저장하기 위해 다음 테이블들을 정의합니다.

| 테이블명 | 설명 | 주요 컬럼 |
| :--- | :--- | :--- |
| `simulation_runs` | 각 시뮬레이션 실행 정보를 관리합니다. | `run_id` (PK), `start_time`, `description`, `params_json` |
| `ticks` | 시뮬레이션의 각 틱 정보를 저장합니다. | `tick_id` (PK), `run_id` (FK), `tick_number` |
| `agents` | 모든 에이전트(가계, 기업)의 고유 정보를 저장합니다. | `agent_id` (PK), `run_id` (FK), `agent_type`, `birth_tick`, `death_tick` |
| `household_states` | 가계 에이전트의 틱별 상태를 저장합니다. | `state_id` (PK), `tick_id` (FK), `agent_id` (FK), `assets`, `needs_level`, `inventory_json` |
| `firm_states` | 기업 에이전트의 틱별 상태를 저장합니다. | `state_id` (PK), `tick_id` (FK), `agent_id` (FK), `assets`, `production_quantity`, `price`, `inventory_json` |
| `market_transactions` | 모든 시장(상품, 노동)의 거래 기록을 저장합니다. | `transaction_id` (PK), `tick_id` (FK), `good`, `buyer_id`, `seller_id`, `price`, `quantity` |
| `macro_indicators` | 틱별 거시 경제 지표를 저장합니다. | `indicator_id` (PK), `tick_id` (FK), `gdp`, `unemployment_rate`, `inflation` |

### 2.2. 데이터 흐름 (Model-View-Controller)

![MVC Data Flow](https://i.imgur.com/9A7f48t.png)

*   **Model (Simulation Engine):**
    *   독립적인 백그라운드 프로세스로 실행되며, UI와 완전히 분리됩니다.
    *   매 틱 계산이 끝난 후, 위에서 설계한 DB 스키마에 맞춰 모든 상태를 SQLite DB에 **WRITE**합니다.
    *   모든 로그는 `stdio`가 아닌 지정된 로그 파일(`app.log`)에만 기록합니다.

*   **Controller (API Server - Flask/FastAPI):**
    *   시뮬레이션 엔진의 실행/중지를 제어하고, UI에 데이터를 제공하는 RESTful API를 구현합니다.
    *   UI로부터 데이터 요청이 오면(예: `GET /api/ticks/100/macro`), SQLite DB를 **READ**하여 결과를 JSON 형태로 반환합니다.

*   **View (Web UI):**
    *   사용자가 특정 틱을 선택하면, 해당 틱의 데이터를 가져오기 위해 Controller의 API를 비동기적으로 호출합니다.
    *   API로부터 받은 JSON 데이터를 사용하여 차트와 테이블을 렌더링합니다.

---

## 3. API 설계 명세

UI와 백엔드 간의 명확한 통신 규약을 정의합니다.

### 3.1. 시뮬레이션 제어 (Simulation Control)
*   `POST /api/simulations`: 새로운 시뮬레이션 실행을 시작합니다.
    *   **Request Body:** `{ "description": "Baseline run with new tax policy" }`
    *   **Response:** `{ "run_id": "uuid-1234", "status": "running" }`
*   `GET /api/simulations/{run_id}`: 특정 시뮬레이션의 현재 상태(실행 여부, 현재 틱)를 조회합니다.
    *   **Response:** `{ "run_id": "uuid-1234", "status": "running", "current_tick": 150 }`
*   `POST /api/simulations/{run_id}/stop`: 실행 중인 시뮬레이션을 중지합니다.
    *   **Response:** `{ "status": "stopped" }`

### 3.2. 거시 데이터 조회 (Macro Data Retrieval)
*   `GET /api/simulations/{run_id}/macro/timeseries`: 특정 시뮬레이션의 전체 기간에 대한 거시 지표 시계열 데이터를 가져옵니다.
    *   **Query Params:** `indicators=gdp,unemployment_rate`
    *   **Response:** `[{ "tick": 1, "gdp": 1000, "unemployment_rate": 0.05 }, ...]`

### 3.3. 에이전트 데이터 조회 (Agent Data Retrieval)
*   `GET /api/simulations/{run_id}/agents`: 특정 시뮬레이션에 참여한 모든 에이전트 목록을 가져옵니다.
    *   **Query Params:** `type=household` (optional filter)
    *   **Response:** `[{ "agent_id": 1, "type": "household", "birth_tick": 0 }, ...]`
*   `GET /api/agents/{agent_id}/state/timeseries`: 특정 에이전트의 상태(자산, 재고 등) 변화에 대한 시계열 데이터를 가져옵니다.
    *   **Query Params:** `run_id=uuid-1234`, `fields=assets,price`
    *   **Response:** `[{ "tick": 1, "assets": 500, "price": 10.5 }, ...]`

### 3.4. 시장 데이터 조회 (Market Data Retrieval)
*   `GET /api/simulations/{run_id}/market/transactions`: 특정 틱 또는 전체 기간의 시장 거래 내역을 가져옵니다.
    *   **Query Params:** `tick=150` (optional), `good=food` (optional)
    *   **Response:** `[{ "transaction_id": 1, "tick": 150, "good": "food", ... }, ...]`

---

## 4. 테스트 계획

새로운 아키텍처의 안정성과 데이터 무결성을 보장하기 위한 다층적 테스트 전략을 정의합니다.

### 4.1. Model 계층: 데이터 영속성 테스트 (Unit Tests)
*   **목표:** 시뮬레이션 엔진이 매 틱의 결과를 DB에 정확하게 저장하는지 검증합니다.
*   **방법:** 테스트용 인메모리 SQLite DB를 설정하고, 1틱 실행 후 DB에 직접 쿼리하여 데이터의 정합성을 확인합니다.
*   **주요 검증 항목:** 가계/기업의 상태, 시장 거래 내역이 빠짐없이 정확하게 기록되는지 확인.

### 4.2. Controller 계층: API 기능 테스트 (Integration Tests)
*   **목표:** 설계된 API 엔드포인트들이 DB의 데이터를 정확하게 조회하고, 올바른 형식의 JSON으로 반환하는지 검증합니다.
*   **방법:** `pytest`와 `TestClient`를 사용하여 미리 정의된 데이터가 담긴 테스트 DB를 대상으로 API를 호출하고, HTTP 상태 코드와 응답 내용을 확인합니다.
*   **주요 검증 항목:** 각 API가 정확한 데이터를 반환하는지, 에러 케이스(예: 없는 데이터 요청)를 적절히 처리하는지 확인.

---

## 5. 구현 체크리스트

전체 전환 과정을 체계적인 Task들로 분해한 실행 가이드입니다.

### Phase 1: 데이터베이스 및 모델 리팩토링 (Backend Core)
- [ ] **1.1. `database.py` 모듈 생성:**
    - [ ] SQLite DB 연결 및 세션 관리 기능 구현.
    - [ ] `SQLAlchemy`를 사용하여 DB 스키마(테이블 모델) 정의.
    - [ ] 프로그램 시작 시 DB와 테이블을 생성하는 초기화 함수 구현.
- [ ] **1.2. 데이터 영속성 로직 구현:**
    - [ ] `SimulationEngine` 클래스에 `_save_state_to_db` 메서드 추가.
    - [ ] `run_tick` 메서드 마지막 부분에서 `_save_state_to_db`를 호출하도록 수정.
    - [ ] `_save_state_to_db` 내부에 에이전트/시장 상태를 DB 모델 객체로 변환하고 저장하는 로직 구현.
- [ ] **1.3. 로깅 시스템 리팩토링:**
    - [ ] `SimulationEngine` 및 하위 모듈에서 `print()`를 `logging` 모듈로 변경.
    - [ ] 불필요한 `stdio` 출력을 모두 제거.
- [ ] **1.4. 단위 테스트 작성 (Model):**
    - [ ] `tests/test_database.py` 파일 생성 및 데이터 영속성 검증 테스트 케이스 작성.

### Phase 2: API 서버 구현 (Backend API)
- [ ] **2.1. API 서버 기본 설정 (`api.py`):**
    - [ ] `Flask` 또는 `FastAPI` 애플리케이션 인스턴스 생성.
- [ ] **2.2. 시뮬레이션 제어 API 구현:**
    - [ ] `POST /api/simulations`: 시뮬레이션 엔진을 별도 프로세스로 실행하고 `run_id`를 반환.
    - [ ] `GET /api/simulations/{run_id}` 및 `POST /api/simulations/{run_id}/stop` 구현.
- [ ] **2.3. 데이터 조회 API 구현:**
    - [ ] `database.py` 모듈을 사용하여 DB에서 데이터를 조회하는 로직 구현.
    - [ ] 모든 GET 엔드포인트 (`/macro/timeseries`, `/agents/.../timeseries` 등) 구현.
- [ ] **2.4. 통합 테스트 작성 (Controller):**
    - [ ] `tests/test_api.py` 파일 생성 및 API 검증 테스트 케이스 작성.

### Phase 3: UI 리팩토링 (Frontend)
- [ ] **3.1. 데이터 요청 로직 수정:**
    - [ ] 기존에 시뮬레이션 엔진과 직접 통신하던 모든 코드 제거.
    - [ ] `fetch()` API를 사용하여 새로운 백엔드 API 서버에 데이터를 요청하도록 모든 데이터 관련 함수 수정.
- [ ] **3.2. UI 컴포넌트 업데이트:**
    - [ ] 차트, 테이블 등 모든 UI 컴포넌트가 API 응답(JSON) 형식에 맞춰 데이터를 처리하도록 수정.
    - [ ] 시뮬레이션 제어 버튼(시작/중지)이 새로운 API를 호출하도록 이벤트 핸들러 수정.
