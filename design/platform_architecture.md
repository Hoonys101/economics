# 시스템 아키텍처 (V2)

**작성일**: 2025-12-29
**분석 대상 코드**: `simulation/engine.py`, `app.py`, `simulation/db/repository.py`

## 1. 개요

본 시뮬레이션은 Python 기반의 **이산 사건 시뮬레이션(Discrete Event Simulation)** 엔진과 Flask 기반의 **웹 대시보드**로 구성됩니다. 에이전트(가계, 기업, 정부)는 AI 모델(Q-Learning)을 통해 의사결정을 내리며, 모든 데이터는 SQLite 데이터베이스에 기록됩니다.

## 2. 핵심 컴포넌트

### 2.1. Simulation Engine (`simulation/engine.py`)
- **역할**: 시뮬레이션의 시간(`tick`)을 진행시키고 에이전트와 시장의 상호작용을 조율합니다.
- **주요 루프**:
    1. `run_tick()` 시작
    2. 시장 초기화 (`clear_orders`)
    3. 에이전트 의사결정 (`make_decision`) -> 주문 생성
    4. 시장 매칭 (`match_orders`) -> 거래 생성
    5. 거래 처리 및 상태 업데이트 (`process_transactions`)
    6. 소비 및 생산 활동 (`consume`, `produce`)
    7. 지표 추적 및 DB 저장 (`tracker.track`, `_save_state_to_db`)
    8. 소비 카운터 리셋

### 2.2. Agents
- **Household**: 소비, 노동 공급, 투자 주체. `HouseholdAI`를 통해 적극성 벡터를 결정합니다.
- **Firm**: 생산, 고용, 판매 주체. `FirmAI`를 통해 가격, 임금, 배당 등을 결정합니다.
- **Government**: 세금 징수 및 재분배(UBI, 보조금) 담당.
- **Bank**: 대출 및 예금 관리 (초기 단계).

### 2.3. AI Engine (`simulation/ai/`)
- **구조**: Multi-Channel Aggressiveness Vector 방식.
- **학습**: Q-Table 기반 강화학습. `AITrainingManager`를 통해 주기적으로 우수 에이전트의 전략을 복제/변이(Evolutionary Learning)합니다.

### 2.5. Optimization Layer (WO-051)
- **VectorizedHouseholdPlanner**: `numpy`를 활용한 벡터화된 의사결정 엔진.
- **ETL Pattern**: Agent Data Extract -> Matrix Computation -> Result Inject 패턴을 사용하여 대규모 에이전트의 반복 연산(예: 출산 결정)을 가속화합니다.

### 2.4. Data Persistence (`simulation/db/`)
- **SQLite**: 시뮬레이션의 모든 상태(거래, 에이전트 상태, 지표)를 저장합니다.
- **Repository Pattern**: `SimulationRepository`를 통해 DB 접근을 추상화했습니다.
- **Batch Processing**: 성능을 위해 `BATCH_SAVE_INTERVAL`마다 일괄 저장합니다.

## 3. 아키텍처 원칙: 신성한 시퀀스 (The Sacred Sequence)

본 시뮬레이션의 모든 상태 변경은 "신성한 시퀀스"라 불리는 4단계 프로세스를 엄격히 준수한다. 이는 상태 변경의 예측 가능성을 보장하고, 제로섬(Zero-Sum) 오류와 타이밍 버그를 방지하기 위함이다.

### Phase 1: 결정 (Decisions)
- **Actor**: `Agent` (Household, Firm) 및 `System` (Education, Infrastructure)
- **Action**: 현재 상태를 기반으로 행동을 결정하고, `Order` 또는 `Transaction` 객체를 반환한다.
- **Rule**: 이 단계에서는 **절대로** 상태(assets, inventory)를 직접 수정하지 않는다.

### Phase 2: 매칭 (Matching)
- **Actor**: `Market` (Commodity, Labor, Stock)
- **Action**: 생성된 `Order`들을 매칭하여 `Transaction` 객체를 생성한다.

### Phase 3: 처리 (Transactions)
- **Actor**: `TransactionProcessor`
- **Action**: 모든 `Transaction`들을 실행하여 자산 이동 및 세금을 정산한다. 
- **Rule**: 모든 가치 이동은 반드시 이 단계에서 **원자적(Atomic)**으로 일어나야 한다.

### Phase 4: 라이프사이클 및 효과 (Lifecycle & Effects)
- **Actor**: `DemographicManager`, `SystemEffectsManager`
- **Action**: 행위자의 노화/사멸 처리 및 트랜잭션의 부수 효과(e.g., TFP 증가, 노화)를 적용한다.
- **Rule**: 지연 실행(Deferred Execution)을 통해 가치 정산 후의 효과만을 적용하여 타이밍 오류를 방지한다.

## 4. 핵심 아키텍처 패턴 (Core Architectural Patterns)

### 4.0 Pre-Viability Bootstrapping
- **원칙**: 시뮬레이션 시작(Tick 0) 시, 모든 에이전트에게 초기 자금과 인력을 먼저 투입(Bootstrapping)한 후에 viability 체크(Liquidation)를 수행한다.
- **효과**: 시작 시점에 자산이 없어 대량으로 파산하는 "Tick 1 Leak" 현상을 방지한다.

## 4. 핵심 아키텍처 패턴 (Core Architectural Patterns)

### 4.1 Data-Driven Purity (DTOs for Decisions)

- **원칙**: 모든 의사결정 로직(Decision Engine)은 반드시 특정 시점의 불변 데이터 스냅샷(`DTO`, e.g., `MarketSnapshotDTO`)에 의존해야 한다. Market 객체와 같은 Live State 객체를 직접 주입하는 것을 금지한다.
- **효과**:
    - **순수성**: 의사결정 함수는 Side-Effect를 일으키지 않으며, 동일 입력에 대해 항상 동일 출력을 보장한다.
    - **테스트 용이성**: 다양한 시나리오의 DTO를 생성하여 단위 테스트를 쉽게 작성할 수 있다.

### 4.2 Two-Phase State Transition (Plan & Finalize)

- **원칙**: 상태 변경이 포함된 복합한 로직은 **계획(Plan)**과 **실행(Finalize)**의 두 단계로 분리한다.
    1.  **Phase 1 (Plan)**: 현재 상태를 바탕으로 모든 행위자의 의도나 트랜잭션을 생성한다. 이 단계에서는 절대 상태를 직접 변경하지 않는다.
    2.  **Phase 2 (Finalize)**: 생성된 의도를 중앙 처리기(`TransactionProcessor`)에서 일괄 처리하여 상태를 변경한다.
- **효과**: 원자성(Atomicity) 보장 및 로직 추적 용이성 확보.

### 4.3 Financial Calculation Integrity (Zero-Sum Distribution)

- **원칙**: 자산 분배 시, N-1명에게는 `floor` 처리된 금액을 분배하고, 마지막 1명에게는 `(총액 - 이미 분배된 금액)`을 할당하여 총합의 무결성을 강제한다.
- **효과**: 시스템 내 자산 총량이 완벽하게 보존(Zero-Sum)된다.

## 4. 웹 인터페이스 (`app.py`, `static/`)
- **Backend**: Flask API (`/api/simulation/tick`, `/api/simulation/update`).
- **Frontend**: Vanilla JS + Chart.js.
- **통신**: `API.js`를 통해 백엔드와 통신하며, `ui.js`가 대시보드를 렌더링합니다.
