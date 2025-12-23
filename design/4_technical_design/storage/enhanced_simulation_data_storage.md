# 강화된 시뮬레이션 데이터 저장 설계 (Enhanced Simulation Data Storage Design)

## 1. 문제 인식 (Problem Recognition)
현재 시뮬레이션의 디버깅 및 분석은 주로 텍스트 로그 파일에 의존하고 있습니다. 이 방식은 다음과 같은 한계를 가집니다:
*   **비효율적인 디버깅**: 특정 틱에서 발생한 문제의 원인을 파악하기 위해 방대한 텍스트 로그를 수동으로 분석해야 합니다.
*   **상태 추적의 어려움**: 각 에이전트의 복잡한 상태 변화(자산, 인벤토리, 욕구, 고용 상태 등)와 AI 의사결정 과정을 틱별로 정확히 추적하기 어렵습니다.
*   **회귀 분석 및 재현성 부족**: 특정 시점의 시뮬레이션 상태를 정확히 재현하거나, 과거 틱으로 돌아가 분석하는 것이 불가능합니다.
*   **데이터 분석의 한계**: 텍스트 로그는 정량적인 데이터 분석 및 시각화에 적합하지 않아, 복잡한 경제 지표나 에이전트 행동 패턴을 파악하기 어렵습니다.

## 2. 제안하는 해결책 (Proposed Solution)
각 시뮬레이션 틱마다 발생하는 핵심 데이터를 관계형 데이터베이스에 체계적으로 저장하는 방식을 도입합니다. 이는 AI 의사결정, 에이전트(가계, 기업)의 상태 변화, 시장 거래 요청 및 체결 내역, 소비 내역 등 시뮬레이션의 모든 중요한 이벤트를 포함합니다.

## 3. 기대 효과 (Expected Benefits)
*   **디버깅 효율성 증대**: 특정 틱의 모든 에이전트 상태 및 의사결정 과정을 SQL 쿼리를 통해 쉽게 조회하고 분석할 수 있습니다.
*   **시뮬레이션 회귀 분석**: 데이터베이스에 저장된 과거 틱의 상태를 기반으로 시뮬레이션의 특정 시점으로 돌아가 문제 발생 원인을 심층적으로 분석할 수 있습니다.
*   **시뮬레이션 재시작 기능**: 특정 틱의 저장된 상태에서 시뮬레이션을 다시 시작하여, 가설 검증 및 파라미터 튜닝을 용이하게 합니다.
*   **데이터 분석 용이성**: 저장된 정형 데이터를 활용하여 다양한 경제 지표 및 에이전트 행동 패턴을 SQL 쿼리, BI 도구, 파이썬 스크립트 등으로 쉽게 분석하고 시각화할 수 있습니다.
*   **재현성 보장**: 시뮬레이션 설정과 결과가 함께 저장되어, 동일한 조건에서의 시뮬레이션 재현성을 높입니다.

## 4. 기술적 세부 사항 (Technical Details)

### 4.1. 데이터베이스 선택 (Database Choice)
*   **SQLite**: 초기 구현 및 개발 편의성을 위해 선택합니다. 단일 파일로 관리되어 설정 및 배포가 용이하며, 개발 단계에서 충분한 성능을 제공합니다.
*   **향후 확장성 고려**: 시뮬레이션 규모가 커지거나 다중 사용자 환경이 필요한 경우, PostgreSQL과 같은 클라이언트-서버 관계형 데이터베이스로의 마이그레이션을 고려할 수 있습니다.

### 4.2. 데이터베이스 스키마 (Database Schema)

#### `simulation_runs` 테이블
시뮬레이션 실행의 메타데이터를 저장합니다.
*   `run_id` (INTEGER PRIMARY KEY AUTOINCREMENT): 시뮬레이션 실행 고유 ID.
*   `start_time` (TEXT NOT NULL): 시뮬레이션 시작 시간 (ISO 8601 형식).
*   `end_time` (TEXT): 시뮬레이션 종료 시간 (ISO 8601 형식).
*   `config_hash` (TEXT NOT NULL): 시뮬레이션 설정 파일(`config.py`)의 해시값. 시뮬레이션 재현성을 보장하는 데 사용됩니다.
*   `description` (TEXT): 시뮬레이션 실행에 대한 간략한 설명.

#### `simulation_states` 테이블
각 틱의 전반적인 시뮬레이션 상태 및 거시 경제 지표를 저장합니다.
*   `state_id` (INTEGER PRIMARY KEY AUTOINCREMENT): 상태 기록 고유 ID.
*   `run_id` (INTEGER NOT NULL): `simulation_runs`의 `run_id` 참조 (FOREIGN KEY).
*   `tick` (INTEGER NOT NULL): 현재 시뮬레이션 틱 번호.
*   `timestamp` (TEXT NOT NULL): 해당 틱의 기록 시간 (ISO 8601 형식).
*   `global_economic_indicators` (TEXT): JSON 형태의 거시 경제 지표 (예: 총 생산량, 실업률, 평균 가격, 총 자산 등).

#### `agents_state_history` 테이블
각 에이전트(가계, 기업)의 틱별 상태 변화를 저장합니다.
*   `history_id` (INTEGER PRIMARY KEY AUTOINCREMENT): 기록 고유 ID.
*   `run_id` (INTEGER NOT NULL): `simulation_runs`의 `run_id` 참조 (FOREIGN KEY).
*   `tick` (INTEGER NOT NULL): 시뮬레이션 틱.
*   `agent_id` (INTEGER NOT NULL): 에이전트 고유 ID.
*   `agent_type` (TEXT NOT NULL): 'Household', 'Firm', 'Bank' 등.
*   `assets` (REAL NOT NULL): 에이전트의 현재 자산.
*   `inventory` (TEXT): JSON 형태의 인벤토리 (재화 ID: 수량).
*   `needs` (TEXT): JSON 형태의 가계 욕구 (욕구 ID: 현재 값). 가계 에이전트에만 해당.
*   `is_employed` (BOOLEAN): 가계의 고용 상태. 가계 에이전트에만 해당.
*   `employer_id` (INTEGER): 고용된 기업 ID. 가계 에이전트에만 해당.
*   `employees` (TEXT): JSON 형태의 기업 고용 현황 (가계 ID: 임금). 기업 에이전트에만 해당.
*   `production_targets` (TEXT): JSON 형태의 기업 생산 목표. 기업 에이전트에만 해당.
*   `current_production` (TEXT): JSON 형태의 기업 현재 생산량. 기업 에이전트에만 해당.
*   `ai_model_state` (TEXT): JSON 형태의 AI 모델 내부 상태 (예: 가중치, 학습률 등). 필요한 경우 저장.

#### `transactions_history` 테이블
시장 및 대출 시장에서 발생한 모든 거래 내역을 저장합니다.
*   `transaction_id` (INTEGER PRIMARY KEY AUTOINCREMENT): 거래 고유 ID.
*   `run_id` (INTEGER NOT NULL): `simulation_runs`의 `run_id` 참조 (FOREIGN KEY).
*   `tick` (INTEGER NOT NULL): 시뮬레이션 틱.
*   `buyer_id` (INTEGER): 구매자 에이전트 ID.
*   `seller_id` (INTEGER): 판매자 에이전트 ID.
*   `item_id` (TEXT): 거래된 재화/서비스 ID (예: 'food', 'labor', 'loan').
*   `quantity` (REAL NOT NULL): 거래 수량.
*   `price` (REAL NOT NULL): 거래 가격.
*   `transaction_type` (TEXT NOT NULL): 'Goods', 'Labor', 'Loan', 'InterestPayment' 등.
*   `loan_id` (TEXT): 대출 거래인 경우 해당 대출의 고유 ID.

#### `ai_decisions_history` 테이블
AI 에이전트의 의사결정 내역을 저장합니다.
*   `decision_id` (INTEGER PRIMARY KEY AUTOINCREMENT): 의사결정 고유 ID.
*   `run_id` (INTEGER NOT NULL): `simulation_runs`의 `run_id` 참조 (FOREIGN KEY).
*   `tick` (INTEGER NOT NULL): 시뮬레이션 틱.
*   `agent_id` (INTEGER NOT NULL): 의사결정을 내린 에이전트 ID.
*   `decision_type` (TEXT NOT NULL): 'Consume', 'Produce', 'Hire', 'Fire', 'Buy', 'Sell', 'RequestLoan', 'RepayLoan' 등.
*   `decision_details` (TEXT): JSON 형태의 의사결정 세부 내용 (예: 소비할 재화, 생산량, 고용할 가계, 주문 가격 등).
*   `predicted_reward` (REAL): AI가 의사결정 시 예측한 보상 값.
*   `actual_reward` (REAL): 의사결정 후 실제로 얻은 보상 값.

### 4.3. 구현 영향 (Implementation Impact)
*   **`simulation/engine.py`**: `run_tick` 메서드 내에서 각 틱의 시뮬레이션 상태, 에이전트 상태, 거래 내역, AI 의사결정 등을 수집하여 데이터베이스에 저장하는 로직을 추가합니다.
*   **`simulation/core_agents.py` (Household, Firm, Bank)**: `make_decision`, `consume`, `produce`, `request_loan`, `repay_loan` 등의 메서드에서 발생하는 주요 상태 변화 및 의사결정 정보를 캡처하여 데이터베이스 관리 모듈에 전달합니다.
*   **`simulation/core_markets.py` (OrderBookMarket, LoanMarket)**: `place_order`, `execute_trade`, `process_interest` 등에서 발생하는 거래 요청 및 체결 정보를 캡처하여 데이터베이스 관리 모듈에 전달합니다.
*   **새로운 데이터베이스 관리 모듈 (`simulation/db_manager.py`) 생성**:
    *   데이터베이스 연결 및 세션 관리.
    *   위에서 정의된 스키마에 따라 테이블 생성.
    *   각 테이블에 데이터를 삽입하는 메서드 (예: `save_simulation_run`, `save_agent_state`, `save_transaction`, `save_ai_decision`).
    *   특정 `run_id` 및 `tick`에 대한 데이터를 조회하는 메서드.

### 4.4. 성능 고려 사항 (Performance Considerations)
*   **대량 데이터 삽입 최적화**: 각 틱마다 발생하는 수많은 데이터 삽입 요청을 개별 `INSERT` 문 대신 `executemany` 또는 ORM의 배치 삽입 기능을 사용하여 최적화합니다.
*   **인덱스 활용**: `run_id`, `tick`, `agent_id` 등 자주 조회되거나 필터링되는 컬럼에 적절한 데이터베이스 인덱스를 생성하여 쿼리 성능을 향상시킵니다.
*   **데이터 보존 정책**: 시뮬레이션 실행 후 분석이 완료된 오래된 데이터는 아카이빙하거나 삭제하는 정책을 수립하여 데이터베이스 크기를 관리합니다.
*   **비동기 처리**: 데이터베이스 쓰기 작업을 별도의 스레드나 프로세스로 분리하여 시뮬레이션의 메인 루프 성능에 미치는 영향을 최소화하는 것을 고려할 수 있습니다.

### 5. 향후 확장 (Future Extensions)
*   **웹 UI 통합**: 저장된 데이터를 기반으로 시계열 그래프, 에이전트별 통계, 시장 동향 등 다양한 시각화 기능을 웹 UI에 추가합니다.
*   **시뮬레이션 제어 기능 확장**: 웹 UI 또는 CLI를 통해 특정 틱으로 이동하거나, 해당 틱의 저장된 상태에서 시뮬레이션을 재시작하는 기능을 구현합니다.
*   **AI 학습 데이터셋 생성**: 저장된 `ai_decisions_history` 테이블을 활용하여 AI 모델 재학습을 위한 고품질 데이터셋을 쉽게 생성합니다.
