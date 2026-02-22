# Architecture Detail: AI Engine & Intelligence Layer

## 1. 개요
본 시뮬레이션의 지능 계층은 에이전트들이 변화하는 시장 환경에 적응하고 최적의 전략을 수립할 수 있도록 돕습니다. 초기 하드코딩된 규칙 대신, 데이터 기반의 학습 및 최적화 엔진을 사용하여 경제 시스템의 창발적(Emergent) 현상을 유도합니다.

## 2. Core Components & Responsibilities

### 2.1. Agent Intelligence (`HouseholdAI`)
- **역할**: 개별 에이전트의 **실시간 의사결정(Real-Time Execution)** 을 전담합니다.
- **소유권**: 에이전트의 모든 내적 상태(Internal State)를 소유하고 관리합니다.
    - **Personality**: `MISER`, `STATUS_SEEKER` 등 에이전트의 고유 성향.
    - **Desire Weights**: 성향에 따라 결정되는 욕구의 가중치.
    - **Learning Rate (`base_alpha`)**: 교육 수준(Education XP) 등에 의해 영향을 받는 학습 속도.
- **책임**: 각 시뮬레이션 틱(Tick)마다 자신의 Q-Table과 현재 상태(State)를 기반으로 최적의 행동을 계산하고 실행합니다.

### 2.2. Strategy Evolution Engine (`AITrainingManager`)
- **역할**: **에이전트 간 전략 전파(Inter-Agent Strategy Propagation)** 를 담당합니다.
- **소유권**: Q-Table의 복제, 변이, 전파 등 시스템 전반의 진화적 알고리즘을 소유합니다.
- **책임**:
    - **모방 학습 (Imitation Learning)**: 주기적으로 우수 에이전트(Top Performer)의 전략(Q-Tables)을 성과 부진 에이전트(Under Performer)에게 복제 및 변이하여 전파합니다.
    - **전략 복제 서비스**: 에이전트의 생성(출생) 또는 교체 시, 부모나 다른 우수 개체의 지능을 복제해주는 API를 제공합니다.
- **Architectural Constraint**: `AITrainingManager`는 에이전트의 내적 상태(Personality, `base_alpha` 등)를 직접 수정해서는 안 됩니다. 모든 상호작용은 `Household` 또는 `HouseholdAI`가 제공하는 고수준 API(e.g., `agent.inherit_traits_from(parent)`)를 통해 이루어져야 합니다.

## 3. Key Mechanisms of Intelligence

### 3.4. Dynamic Insight Engine (Phase 4.1)
- **Concept**: Agent intelligence (`market_insight`) is dynamic, not static. It evolves based on the **3-Pillar Learning** model:
  1.  **Experience (Active)**: Learning from prediction errors (`TD-Error`). High surprise = High learning.
  2.  **Education (Service)**: Consuming `education_service` directly boosts insight.
  3.  **Time (Decay)**: Intelligence decays naturally per tick (`-0.001`), forcing continuous engagement.
- **Perceptual Filters**:
  - `HouseholdAI` filters incoming market data based on current insight.
  - **High Insight (>0.8)**: Sees Real-time data.
  - **Medium Insight (0.3-0.8)**: Sees 3-tick SMA (Simple Moving Average) data.
  - **Low Insight (<0.3)**: Sees 5-tick Lagged data + Distorted Debt Perception (Noise).
- **Panic Mechanism**:
  - Low-insight agents are susceptible to `market_panic_index`, freezing investment and reducing consumption during systemic crises.

### 3.5. Heterogeneous Market: Signaling, Envy, and Bargaining (Wave 3)
- **Concept**: The market assumes full heterogeneity. Matching is no longer an Order Book sort but a **Search & Bargaining** process.
- **Agent Choice (The Envy Model)**: 
  - Agents select majors/domains based on **100-Tick Lagged SMA Wages**. This creates "Cobweb Cycles" (Hog Cycles) where sectors alternate between labor shortages and education bubbles.
- **The Halo Effect (Employer Perception)**:
  - Employers estimate productivity based on signals. 
  - **Low-Insight Firms**: Fall for the "College Halo," doubling expected productivity in their WTP calculations, leading to overspending and eventual bankruptcy.
- **Nash Bargaining Solution**:
  - Matches are resolved via Nash Bargaining. The final wage is dictated by the surplus between `Firm_WTP` and `Agent_Reservation_Wage` (driven by Sunk Costs).
- **Adaptive Firm Learning**:
  - Firms calculate **TD-Error** ($Expected - Realized$) at the factory floor. High error directly boosts `market_insight`, representing the organization "learning" to see through signals.

### 3.1. Real-Time Decision Making (Agent Execution)
- 각 에이전트는 매 틱마다 `HouseholdAI`를 통해 자신의 현재 상태와 시장 정보를 `DecisionContext`로 조합합니다.
- `HouseholdAI`는 이 컨텍스트를 사용하여 자신의 Q-Table에서 최적의 행동(소비, 노동, 투자 등)을 선택하고 실행합니다.
- 이 과정은 전적으로 개별 에이전트의 내부 로직에 의해 완결됩니다.

### 3.2. Trait Inheritance (Agent Lifecycle Event)
- 에이전트의 출생(Mitosis) 시, 자식 에이전트(`child_agent`)는 부모(`parent_agent`)로부터 지적 자산을 상속받습니다. 이 프로세스는 자식 에이전트의 초기화 과정의 일부입니다.
- **1. Personality & Psychology Inheritance**:
    - 자식은 부모의 `Personality`를 상속받거나 일정 확률(`MITOSIS_MUTATION_PROBABILITY`)로 새로운 성향으로 변이합니다.
    - 자신의 최종 성향에 따라 `Desire Weights`를 스스로 계산하고 설정합니다. 이 로직은 `Household` 모듈 내에 존재하며, `AITrainingManager`는 관여하지 않습니다.
- **2. Education & Learning Rate Inheritance**:
    - 자식은 부모의 교육 경험치(`education_xp`)를 기반으로 자신의 초기 학습률 보너스(`xp_bonus`)를 계산합니다.
    - 이 보너스는 자신의 `HouseholdAI`에 `base_alpha` 값으로 설정되어, 더 빠른 학습 능력을 갖추게 됩니다.
- **3. Q-Table Inheritance**:
    - 자식 에이전트는 `AITrainingManager.clone_and_mutate_q_table(parent, self)`를 **호출**하여 부모의 전략적 지식(Q-Tables)을 복제합니다. 이로써 `AITrainingManager`는 단순한 '복제 서비스' 역할을 수행합니다.

### 3.3. Strategy Propagation (Evolutionary Cycle)
- 시뮬레이션의 특정 주기마다 `AITrainingManager`의 `run_imitation_learning_cycle`이 실행됩니다.
- 이 과정은 실시간 에이전트 실행과 분리된 **전략적 동기화 단계(Strategy Sync Phase)** 입니다.
- **1. Performers Assessment**: `AITrainingManager`는 자산(Assets)을 기준으로 상위(Top) 및 하위(Under) 성과자 그룹을 식별합니다.
- **2. Knowledge Transfer**: 하위 성과자는 상위 성과자 중 무작위 롤모델의 Q-Table을 복제하고 일부 변이(Mutation)를 적용하여 자신의 전략을 갱신합니다. 이 과정 역시 에이전트의 고수준 API를 통해 수행됩니다.

## 4. 연산 최적화 (Optimization Layer)

대규모 에이전트(2,000명 이상)의 지능적 연산을 실시간으로 처리하기 위해 최적화 계층을 운영합니다.

### 4.1 Vectorized Planner (with NumPy)
- 개별 에이전트 루프를 도는 대신, `numpy` 배열 연산을 활용하여 수천 명의 의사결정을 한 번에 병렬적으로 계산합니다.
- **성능**: 하드웨어 가속을 통해 틱당 연산 시간을 밀리초 단위로 단축합니다.

### 4.2 Data-Driven Purity
- **DecisionContext**: 의사결정에 필요한 모든 정적 데이터(State, Market Data, Config)를 집계한 불변 컨텍스트 객체.
- AI 엔진은 이 컨텍스트 외의 어떤 외부 시스템에도 의존하지 않으며, 동일 입력에 대해 동일한 전략을 산출합니다.

## 5. 아키텍처적 의의
AI 엔진은 시뮬레이션에 "생명력"을 불어넣는 역할을 합니다. 단순한 수식의 나열이 아니라, 에이전트들이 스스로 이익을 추구하는 과정에서 인플레이션, 스태그플레이션, 호황과 불황 같은 복잡한 거시경제 현상이 자연스럽게 발생하게 됩니다. 명확히 분리된 **실행(Execution)** 계층과 **진화(Evolution)** 계층은 시스템의 안정성과 확장성을 보장합니다.
