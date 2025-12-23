# V2 AI 전략 실행 및 학습 설계 (계층적 Q-러닝)

## 1. 개요

V2 AI 모델은 **계층적 Q-러닝(Hierarchical Q-Learning)**을 통해, '전략'을 결정하는 상위 AI와 '전술'을 결정하는 하위 AI로 역할을 분리한다.

이 설계 문서는 이 **2중 Q-테이블 구조**가 어떻게 작동하며, AI가 결정한 추상적인 '전술'이 어떻게 구체적인 '행동'으로 변환되고, 그 최종 결과가 어떻게 두 계층의 AI를 학습시키는지 그 표준 프로세스를 정의한다.

---

## 2. 전략 실행 모듈 설계 (Strategy Execution Module)

AI의 결정을 실행하는 책임은 해당 AI를 소유한 **`Agent` (예: `Firm`, `Household`) 클래스**가 직접 맡는다.

- **위치:** 각 `Agent` 클래스 내부에 `execute_tactic(tactic, aggressiveness)`와 같은 메서드를 구현한다.
- **역할:** 이 메서드는 AI로부터 '전술'과 '적극성'을 입력받아, 자신의 현재 상태와 시장 데이터를 바탕으로 구체적인 파라미터(가격, 수량, 임금 등)를 계산하고, 최종 `Order` 객체를 생성하여 시장에 제출하는 역할을 수행한다.
- **참조:** 구체적인 실행 규칙은 `household_agent_design.md`와 `firm_agent_design.md`에 정의된다.

### 2.1. 데이터 흐름 예시 (기업)

1.  **`SimulationEngine`:** `firm.get_decision()`을 호출하여 `FirmAI`로부터 최종 결정 `(Intention, Tactic)`을 얻는다.
2.  **`SimulationEngine`:** `firm.execute_tactic(tactic, aggressiveness)`을 호출하여 전술 실행을 명령한다.
3.  **`Firm.execute_tactic`:**
    -   `tactic`이 `INCREASE_PRICE`이면, `aggressiveness`에 따라 가격 인상률(예: 5%, 10%, 15%)을 차등 적용하여 새로운 판매 가격을 계산한다.
    -   계산된 가격과 수량을 담아 `Order` 객체를 생성하고 `Market`에 제출한다.

---

## 3. 계층적 Q-러닝 설계 (2중 Q-테이블)

### 3.1. 구조

#### 3.1.1. Q-테이블 1: 전략 AI (Strategic AI)

- **역할:** 에이전트의 전반적인 상태를 보고, 이번 턴의 **최상위 목표(`Intention`)**를 결정한다.
- **상태 (State):** 에이전트의 거시적 상태 (예: `(자산 수준, 주요 욕구)`)
- **행동 (Action):** `Intention` Enum (예: `INCREASE_ASSETS`, `SATISFY_SURVIVAL_NEED`)
- **Q-테이블:** `Q_strategy(상태, Intention)`

#### 3.1.2. Q-테이블 2: 전술 AI (Tactical AI)

- **역할:** 상위 AI가 결정한 `Intention`을 달성하기 위한 **구체적인 행동(`Tactic`)**을 결정한다. 각 `Intention` 별로 개별 Q-테이블이 존재한다.
- **상태 (State):** `Intention`과 관련된 에이전트의 세부 상태
- **행동 (Action):** `Tactic` Enum (예: `Intention`이 `INCREASE_ASSETS`일 경우, `PARTICIPATE_LABOR_MARKET` 또는 `INVEST_IN_STOCKS`)
- **Q-테이블:** `Q_tactic_for_INCREASE_ASSETS(상태, Tactic)`, `Q_tactic_for_SATISFY_SURVIVAL_NEED(상태, Tactic)` 등

### 3.2. 의사결정 흐름

1.  에이전트가 자신의 **전체 상태**를 인식한다.
2.  **전략 AI**가 `Q_strategy` 테이블을 사용하여 최적의 **`Intention`**을 선택한다.
3.  선택된 `Intention`에 해당하는 **전술 AI**가 활성화된다.
4.  **전술 AI**가 자신의 `Q_tactic` 테이블을 사용하여 최적의 **`Tactic`**을 선택한다.
5.  선택된 `(Intention, Tactic)`이 `Agent`의 `execute_tactic` 메서드로 전달되어 실행된다.

### 3.3. 학습 및 보상 적용

1.  **통합 보상 계산:** 틱 종료 시, 행동의 최종 결과(자산 변화, 욕구 변화)를 바탕으로 **단 하나의 통합 보상(Unified Reward)** 값이 계산된다.
2.  **보상 역전파 (Credit Assignment):** 이 통합 보상 값은 의사결정에 참여한 **두 계층의 Q-테이블을 모두 업데이트**하는 데 사용된다.
    -   **전술 테이블 업데이트:** `Q_tactic(상태, Tactic)`이 갱신된다.
    -   **전략 테이블 업데이트:** `Q_strategy(상태, Intention)`가 갱신된다.

---

## 4. AI 모델 영속화 전략 (AI Model Persistence Strategy)

### 4.1. 개요

수백 개의 AI 에이전트가 각자 Q-테이블을 가지고 학습하는 환경에서, 학습된 모델을 효율적으로 저장하고 로드하는 영속화 전략이 필요하다. '메모리 내 저장 + 주기적 영속화' 방식을 채택하여, 시뮬레이션 중에는 빠른 접근을 보장하고, 시뮬레이션 간에는 학습된 지식을 보존한다.

### 4.2. 저장 메커니즘: SQLite 데이터베이스

- 모든 에이전트의 Q-테이블 데이터를 SQLite 데이터베이스에 일괄적으로 저장한다.
- Python 객체 형태의 상태(State)와 행동(Action) 튜플은 데이터베이스에 저장하기 위해 문자열 등으로 직렬화(Serialization)하여 저장한다.

### 4.3. 데이터베이스 스키마 (예시)

-   **`agent_q_values` 테이블:**
    -   `agent_id` (TEXT): 에이전트의 고유 ID
    -   `q_table_type` (TEXT): '전략'(`strategy`) 또는 '전술'(`tactic`)
    -   `state_key` (TEXT): 직렬화된 상태(State) 튜플
    -   `action_key` (TEXT): 직렬화된 행동(Action) 튜플
    -   `q_value` (REAL): 해당 상태-행동 쌍의 Q-값

### 4.4. 로드 메커니즘

-   시뮬레이션 시작 시, 필요한 모든 Q-테이블 데이터를 SQLite 데이터베이스에서 읽어와 각 AI 에이전트의 메모리에 로드한다.
-   데이터베이스에서 읽어온 직렬화된 상태/행동 키를 다시 Python 튜플 객체로 역직렬화(Deserialization)하여 Q-테이블을 재구성한다.

---

## 5. 고급 학습 메커니즘 (설계 아이디어 - 구현 보류)

**[구현 보류]** 아래 내용은 향후 AI 고도화를 위한 설계 아이디어이며, 현재 구현 범위에는 포함되지 않음.

- **동적 학습 초점 (Dynamic Learning Focus):** 실패의 '크기'에 따라 학습 대상을 동적으로 변경 (큰 실패 -> 전략 AI, 작은 실패 -> 전술 AI).
- **학습 강도 조절 (Learning Intensity Adjustment):** 실패의 '연속성'에 따라 학습 강도를 조절 (연속 실패 시 학습률 증폭).
- **주요 전략 실패 이력 (Major Strategic Failure History):** 큰 손실을 유발한 전략 실패를 별도 이력으로 관리하여 메타 학습 기반으로 활용.
- **통계 기반 동적 임계값:** '큰 손실'과 같은 기준을 고정값이 아닌, 과거 데이터의 평균과 표준편차를 이용해 동적으로 설정.
