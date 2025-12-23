# 프로젝트 API 설계 문서 (PROJECT_API_DESIGN.md)

이 문서는 경제 시뮬레이션 프로젝트의 주요 모듈 및 클래스 간 API 정의와 상호작용 방식을 설명합니다. 새로운 기능을 구현하거나 기존 모듈을 수정할 때 이 문서를 참조하여 일관성과 확장성을 유지해야 합니다.

---

## 1. 핵심 에이전트 (Core Agents)

### 1.1. Household (가계)
- **역할**: 노동 공급, 재화 소비, 자산 관리, 욕구 충족.
- **주요 속성**: `id`, `assets`, `inventory`, `needs`, `is_employed`, `employer_id`, `current_consumption`, `current_food_consumption`.
- **주요 메서드**: `make_decision(market_data, current_tick)`, `update_needs()`, `consume(item_id, quantity, current_tick)`.

### 1.2. Firm (기업)
- **역할**: 재화 생산, 노동 수요, 재고 관리, 이윤 추구.
- **주요 속성**: `id`, `assets`, `inventory`, `employees`, `productivity_factor`, `production_targets`, `revenue_this_turn`, `cost_this_turn`, `current_production`.
- **주요 메서드**: `make_decision(market_data, current_tick)`, `produce(current_tick)`, `distribute_dividends(households)`.

### 1.3. Bank (은행) - (신규)
- **역할**: 대출 승인 및 관리, 이자 처리, 상환 처리.
- **주요 속성**: `id`, `assets`, `outstanding_loans` (현재 미상환 대출 목록).
- **주요 메서드**:
    - `request_loan(agent_id: int, amount: float, interest_rate: float, duration: int) -> Transaction | None`:
        - **설명**: 에이전트의 대출 요청을 처리합니다. 은행 자산이 충분하면 대출을 승인하고 `Transaction` 객체를 반환합니다.
        - **인자**: `agent_id` (대출 요청 에이전트 ID), `amount` (요청 금액), `interest_rate` (이자율), `duration` (대출 기간).
        - **반환**: `Transaction` 객체 (대출 승인 시) 또는 `None` (대출 거부 시).
    - `repay_loan(loan_id: str, amount: float) -> Transaction | None`:
        - **설명**: 대출 상환을 처리합니다. 상환액만큼 대출 잔액을 줄이고 `Transaction` 객체를 반환합니다.
        - **인자**: `loan_id` (상환할 대출 ID), `amount` (상환 금액).
        - **반환**: `Transaction` 객체 (상환 처리 시) 또는 `None` (대출을 찾을 수 없을 때).
    - `process_interest() -> List[Transaction]`:
        - **설명**: 매 틱마다 모든 미상환 대출에 대한 이자를 계산하고 징수합니다. 이자 징수에 대한 `Transaction` 리스트를 반환합니다.
        - **인자**: 없음.
        - **반환**: `List[Transaction]` (이자 징수 트랜잭션 목록).
    - `get_outstanding_loans_for_agent(agent_id: int) -> List[Dict[str, Any]]`:
        - **설명**: 특정 에이전트의 미상환 대출 목록을 반환합니다.
    - `get_total_outstanding_loans() -> float`:
        - **설명**: 은행의 총 미상환 대출 잔액을 반환합니다.

---

## 2. 시장 (Markets)

### 2.1. OrderBookMarket (상품/노동 시장)
- **역할**: 매수/매도 주문을 받아 가격-시간 우선 원칙에 따라 거래를 체결.
- **주요 메서드**: `place_order(order, current_tick)`, `get_best_bid(item_id)`, `get_best_ask(item_id)`.

### 2.2. LoanMarket (대출 시장) - (신규)
- **역할**: 대출 요청 및 상환 주문을 은행과 중개.
- **주요 속성**: `market_id`, `bank` (연결된 Bank 인스턴스).
- **주요 메서드**:
    - `place_order(order: Order, current_tick: int) -> List[Transaction]`:
        - **설명**: 대출 요청(`LOAN_REQUEST`) 또는 상환(`REPAYMENT`) 주문을 받아 은행에 전달하고 처리 결과를 `Transaction` 리스트로 반환합니다.
        - **인자**: `order` (주문 객체), `current_tick` (현재 틱).
        - **반환**: `List[Transaction]` (처리된 트랜잭션 목록).
    - `process_interest() -> List[Transaction]`:
        - **설명**: 연결된 은행의 이자 처리 로직을 호출하고, 발생한 이자 트랜잭션을 반환합니다.
        - **인자**: 없음.
        - **반환**: `List[Transaction]` (이자 트랜잭션 목록).

---

## 3. 의사결정 엔진 (Decision Engines)

### 3.1. BaseDecisionEngine
- **역할**: 모든 의사결정 엔진의 추상 기본 클래스.

### 3.2. HouseholdDecisionEngine
- **역할**: 가계의 소비, 노동 공급, 대출 요청/상환 등 의사결정.
- **주요 메서드**: `make_decisions(household, current_tick, market_data)`.

### 3.3. FirmDecisionEngine
- **역할**: 기업의 생산, 고용, 판매, 대출 요청/상환 등 의사결정.
- **주요 메서드**: `make_decisions(firm, current_tick, market_data)`.

---

## 4. 기타 핵심 모듈

### 4.1. Simulation (시뮬레이션 엔진)
- **역할**: 시뮬레이션의 메인 루프 관리, 틱 진행, 주체 및 시장 상호작용 조정.
- **주요 메서드**: `run_tick()`.

### 4.2. EconomicIndicatorTracker
- **역할**: 거시 경제 지표 추적 및 기록.

### 4.3. Logger
- **역할**: 시뮬레이션 로그 기록 및 관리.

---

## 5. 데이터 모델 (Data Models)

### 5.1. Order
- **역할**: 시장에 제출되는 주문의 기본 구조.

### 5.2. Transaction
- **역할**: 시장에서 체결된 거래의 결과.

---

## 6. 설정 (Configuration)

### 6.1. config.py
- **역할**: 시뮬레이션의 모든 주요 파라미터 및 상수를 정의.

---

## 7. AI 관련 모듈

### 7.1. AIDecisionEngine
- **역할**: AI 에이전트의 의사결정 로직.

### 7.2. AITrainingManager
- **역할**: AI 에이전트의 학습 경험 관리 및 모델 훈련.
