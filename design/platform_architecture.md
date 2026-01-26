# Platform Architecture & Design Patterns

## 1. 개요
본 시뮬레이션은 Python 기반의 **이산 사건 시뮬레이션(Discrete Event Simulation)** 엔진과 Flask 기반의 **웹 대시보드**로 구성됩니다. 에이전트(가계, 기업, 정부)는 AI 모델(Q-Learning)을 통해 의사결정을 내리며, 모든 데이터는 SQLite 데이터베이스에 기록됩니다.

## 2. 핵심 컴포넌트

### 2.1. Simulation Engine (`simulation/engine.py`)
- **역할**: 시뮬레이션의 시간(`tick`)을 진행시키고 에이전트와 시장의 상호작용을 조율합니다.

### 2.2. Agents
- **Household**: 소비, 노동 공급, 투자 주체.
- **Firm**: 생산, 고용, 판매 주체.
- **Government**: 세금 징수 및 재분배 담당.
- **Bank**: 대출 및 예금 관리.

### 2.3. AI Engine (`simulation/ai/`)
- **구조**: Multi-Channel Aggressiveness Vector 방식.
- **학습**: Q-Table 기반 강화학습. `AITrainingManager`를 통해 주기적으로 우수 에이전트의 전략을 복제/변이합니다.

### 2.4. Data Persistence (`simulation/db/`)
- **SQLite**: 시뮬레이션의 모든 상태(거래, 에이전트 상태, 지표)를 저장합니다.
- **Repository Pattern**: `SimulationRepository`를 통해 DB 접근을 추상화했습니다.

### 2.5. Optimization Layer (WO-051)
- **VectorizedHouseholdPlanner**: `numpy`를 활용한 벡터화된 의사결정 엔진.
- **ETL Pattern**: Agent Data Extract -> Matrix Computation -> Result Inject 패턴을 사용하여 대규모 에이전트 연산을 가속화합니다.

---

## 3. 아키텍처 원칙: 신성한 시퀀스 (The Sacred Sequence)

본 시뮬레이션의 모든 상태 변경은 "신성한 시퀀스"라 불리는 4단계 프로세스를 엄격히 준수한다. 이는 상태 변경의 예측 가능성을 보장하고, 제로섬(Zero-Sum) 오류와 타이밍 버그를 방지하기 위함이다.

### Phase 1: 결정 (Decisions)
- **Actor**: `Agent` (Household, Firm) 및 `System` (Education, Infrastructure)
- **Action**: 현재 상태(`MarketSnapshotDTO`, `GovernmentPolicyDTO`)를 기반으로 행동을 결정하고, `Order` 또는 `Transaction` 객체를 반환한다.
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

---

## 4. 핵심 아키텍처 패턴 (Core Architectural Patterns)

### 4.0 Pre-Viability Bootstrapping
- **원칙**: 시뮬레이션 시작(Tick 0) 시, 모든 에이전트에게 초기 자금과 인력을 먼저 투입(Bootstrapping)한 후에 viability 체크(Liquidation)를 수행한다.
- **효과**: 시작 시점에 자산이 없어 대량으로 파산하는 "Tick 1 Leak" 현상을 방지한다.

### 4.1 Data-Driven Purity (DTOs for Decisions)

- **현상(Phenomenon)**: 의사결정 로직(예: `AIDrivenHouseholdDecisionEngine`)이 `market`과 같은 live 서비스 객체를 직접 참조하면서, 테스트가 복잡해지고 서비스 간 결합도가 높아지는 문제.
- **원인(Cause)**: 엔진이 외부 상태(live object)에 직접 의존하여, 동일 입력에 대해 다른 결과를 낼 수 있는 비결정적 특성을 가짐.
- **해결(Solution)**: 의사결정 엔진은 반드시 `DecisionContext`를 통해 전달되는 정적 데이터(State DTO, Market Data, Config)에만 의존해야 한다. 엔진 내부에서 live 서비스 객체의 메서드를 직접 호출해서는 안 된다. 
- **효과(Effect)**:
    - **순수성**: 의사결정 함수는 Side-Effect를 일으키지 않으며, 동일 입력에 대해 항상 동일 출력을 보장하는 순수 함수(pure function)처럼 동작한다.
    - **테스트 용이성**: 외부 서비스로부터 완전히 분리되어, 다양한 시나리오의 DTO를 통해 행위를 예측 가능하게 검증할 수 있다.
    - **디버깅 용이성**: 특정 시점의 `DecisionContext`를 로깅하여, 의사결정 로직의 동작을 정확히 재현하고 분석할 수 있다.

### 4.2 Two-Phase State Transition (Plan & Finalize)
- **Phenomenon**: Complex logic mixing state reading, decision making, and state mutation in a single function (e.g., deciding consumption and immediately deducting inventory).
- **Principle**: Separate complex state transitions into **Plan** (Phase 1) and **Finalize** (Phase 3/4) phases.
    1.  **Phase 1 (Plan)**: Generate Intents or Transactions based on current state. No state mutation allowed.
    2.  **Phase 2 (Finalize)**: Execute generated Transactions/Intents in a batch to update state.
- **Effect**: Guarantees atomicity and clarity of tracking.

### 4.3 Financial Calculation Integrity (Zero-Sum Distribution)
- **Phenomenon**: Asset leakage or creation due to floating-point precision errors when distributing funds (e.g., Inheritance).
- **Principle**: When distributing assets to N recipients:
    - Distribute `floor(total / N)` to N-1 recipients.
    - Distribute `total - (N-1) * distributed_amount` to the last recipient.
- **Effect**: Guarantees strict Zero-Sum conservation of assets within the system.

---

## 5. 웹 인터페이스 (`app.py`, `static/`)
- **Backend**: Flask API (`/api/simulation/tick`, `/api/simulation/update`).
- **Frontend**: Vanilla JS + Chart.js.
- **통신**: `API.js`를 통해 백엔드와 통신하며, `ui.js`가 대시보드를 렌더링합니다.
