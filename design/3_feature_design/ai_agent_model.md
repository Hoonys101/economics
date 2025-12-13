# AI 에이전트 모델 설계 (V2 - 계층적 Q-러닝)

## 1. V1 AI 모델의 한계와 V2의 목표

### 1.1. V1 모델의 한계

기존 V1 모델의 AI는 모든 에이전트가 단일 AI를 공유하며, 주로 '가격 맞추기'와 같은 저수준의 전술적 판단에 집중했습니다. 하지만 시장 메커니즘 자체가 불안정했기 때문에, AI가 아무리 합리적인 판단을 하려 해도 경제 전체가 붕괴되는 문제가 발생했습니다. 이는 AI가 행동의 결과(보상)를 정확히 인지하고 학습하기 어려운 환경을 조성하여, 의미 있는 전략 학습이 불가능했습니다.

### 1.2. V2 모델의 목표

V2 설계에서는 AI의 역할을 안정된 시장 위에서 장기적 이익을 추구하는 **고수준의 '전략' 결정**으로 격상시킵니다. 각 에이전트가 독립적인 AI를 통해 자신만의 성공 전략을 학습하고, 시장에 다양한 행태를 창발시키는 것을 목표로 합니다. 이를 위해 **계층적 Q-러닝(Hierarchical Q-Learning)** 구조를 도입하여, '전략'을 결정하는 상위 AI와 '전술'을 결정하는 하위 AI로 역할을 분리합니다.

---

## 2. 계층적 Q-러닝 아키텍처 (Hierarchical Q-Learning Architecture)

V2 AI 모델은 2개의 Q-테이블을 사용하는 계층적 구조를 가집니다.

### 2.1. Q-테이블 1: 전략 AI (Strategic AI)

- **역할:** 에이전트의 전반적인 상태를 보고, 이번 턴의 **최상위 목표(`Intention`)**를 결정합니다. "무엇을 원하는가?"에 대한 답을 내립니다.
- **상태 (State):** 에이전트의 거시적 상태 (예: `(자산 수준, 주요 욕구)`)
- **행동 (Action):** `Intention` Enum (예: `INCREASE_ASSETS`, `SATISFY_SURVIVAL_NEED`)
- **Q-테이블:** `Q_strategy(상태, Intention)`

### 2.2. Q-테이블 2: 전술 AI (Tactical AI)

- **역할:** 상위 AI가 결정한 `Intention`을 달성하기 위한 **구체적인 행동(`Tactic`)**을 결정합니다. "어떻게 달성할 것인가?"에 대한 답을 내립니다.
- **구조:** 각 `Intention` 별로 개별 Q-테이블이 존재합니다.
- **상태 (State):** 해당 `Intention`과 관련된 에이전트의 세부 상태
- **행동 (Action):** `Tactic` Enum (예: `Intention`이 `INCREASE_ASSETS`일 경우, `PARTICIPATE_LABOR_MARKET` 또는 `INVEST_IN_STOCKS`)
- **Q-테이블:** `Q_tactic_for_INCREASE_ASSETS(상태, Tactic)`, `Q_tactic_for_SATISFY_SURVIVAL_NEED(상태, Tactic)` 등

### 2.3. 의사결정 및 학습 흐름

1.  에이전트가 자신의 **전체 상태**를 인식합니다.
2.  **전략 AI**가 `Q_strategy` 테이블을 사용하여 최적의 **`Intention`**을 선택합니다.
3.  선택된 `Intention`에 해당하는 **전술 AI**가 활성화됩니다.
4.  **전술 AI**가 자신의 `Q_tactic` 테이블을 사용하여 최적의 **`Tactic`**을 선택합니다.
5.  선택된 `Tactic`이 에이전트의 실행 모듈로 전달되어 구체적인 `Order`를 생성합니다.
6.  틱 종료 시, 행동의 최종 결과를 바탕으로 **단 하나의 통합 보상(Unified Reward)**을 계산합니다.
7.  이 보상 값은 의사결정에 참여한 **두 계층의 Q-테이블을 모두 업데이트**하는 데 사용됩니다 (Credit Assignment).

---

## 3. 가계(Household) AI 모델 설계

### 3.1. 전략 AI (Strategic AI)

-   **상태 (State):**
    -   **입력:** `assets`, `inventory`, `needs`, `is_employed`
    -   **변환:** `(자산 수준, 재고 수준, 주요 욕구)` 튜플로 변환.
        -   `자산 수준`: `[위험, 안정, 부유]` (전체 가계 평균 자산 대비)
        -   `재고 수준`: `[결핍, 충분, 과잉]` (필수품 'food' 재고량 기준)
        -   `주요 욕구`: `[생존, 인정, 성장 등]` (가장 높은 욕구 1가지)
-   **행동 (Action - `Intention`):**
    -   `SATISFY_SURVIVAL_NEED`: 생존 욕구 충족 (식량 구매 등)
    -   `INCREASE_ASSETS`: 자산 증대 (노동, 투자)
    -   `SATISFY_SOCIAL_NEED`: 사회적 욕구 충족 (사치재 구매)
    -   `IMPROVE_SKILLS`: 역량 강화 (교육)

### 3.2. 전술 AI (Tactical AI)

-   **`Intention: SATISFY_SURVIVAL_NEED`**
    -   **상태:** `(식량 재고 수준)`
    -   **행동 (`Tactic`):** `BUY_FOOD`, `PRODUCE_FOOD_AT_HOME`
-   **`Intention: INCREASE_ASSETS`**
    -   **상태:** `(고용 상태, 시장 임금 수준)`
    -   **행동 (`Tactic`):** `PARTICIPATE_LABOR_MARKET`, `CHANGE_JOB`, `DEMAND_WAGE_INCREASE`

### 3.3. 보상(Reward) 함수

-   **피드백:** `(자산 증가율) + (주요 욕구 감소율 * 가중치)`
-   자산이 늘어나거나, 가장 시급했던 욕구가 효과적으로 해소되면 높은 보상을 받습니다.
-   **가중치:** 초기에는 1.0으로 설정하며, 향후 모델 고도화 시 동적으로 조절될 수 있습니다.

---

## 4. 기업(Firm) AI 모델 설계

### 4.1. 전략 AI (Strategic AI)

-   **상태 (State):**
    -   **입력:** `profit_margin`, `inventory_ratio`, `hiring_success_rate`, `sales_performance`
    -   **변환:** `(이윤률, 재고율, 채용률, 판매 실적)` 튜플로 변환.
        -   `이윤률`, `재고율`, `채용률`: `[낮음, 보통, 높음]`
        -   `판매 실적`: `[매우 부진, 부진, 보통, 완판]`
-   **행동 (Action - `Intention`):**
    -   `MAXIMIZE_PROFIT`: 단기 이윤 극대화
    -   `SECURE_MARKET_SHARE`: 시장 점유율 확보
    -   `IMPROVE_PRODUCTIVITY`: 생산성 향상

### 4.2. 전술 AI (Tactical AI)

-   **`Intention: MAXIMIZE_PROFIT`**
    -   **상태:** `(현재 가격, 시장 평균 가격, 재고 수준)`
    -   **행동 (`Tactic`):** `INCREASE_PRICE`, `DECREASE_PRICE`, `MAINTAIN_PRICE`
-   **`Intention: SECURE_MARKET_SHARE`**
    -   **상태:** `(자사 점유율, 경쟁사 가격)`
    -   **행동 (`Tactic`):** `AGGRESSIVE_PRICE_CUT`, `PROMOTIONAL_EVENT`
-   **`Intention: IMPROVE_PRODUCTIVITY`**
    -   **상태:** `(현재 생산성 수준, 투자 가능 자금)`
    -   **행동 (`Tactic`):** `INVEST_IN_RD`, `INVEST_IN_CAPITAL`

### 4.3. 보상(Reward) 함수

-   **피드백:** `(기업 자산 증가율)`
-   가장 직관적인 지표인 자산(자본)의 장기적 증감률을 보상으로 삼아, 지속 가능한 성장을 학습 목표로 설정합니다.

---

## 5. 학습 및 진화 메커니즘

### 5.1. 기본 학습 프로세스

각 에이전트 AI는 자신만의 Q-테이블(전략, 전술)을 가지고, 행동에 대한 피드백(보상)을 통해 Q-테이블의 값을 업데이트하며 학습합니다. 이 과정은 시뮬레이션 틱마다 반복됩니다.

### 5.2. 모방 및 진화 학습 (Imitation and Evolutionary Learning)

개별적인 학습을 넘어, 성공적인 전략이 개체군 전체로 확산되는 메커니즘을 도입합니다.

-   **도태 (Elimination):** 에이전트가 비활성화(사망)되면, 해당 에이전트가 가졌던 실패한 Q-테이블은 시뮬레이션에서 **제거(도태)**됩니다.
-   **모방/복제 (Imitation/Cloning):**
    1.  **주기적 모방:** 특정 주기(예: 1000틱)마다, 자산 기준 상위 10% 에이전트의 **전략 Q-테이블(`Q_strategy`)**을 하위 50% 에이전트에게 복제하여 전파합니다. 이는 성공적인 장기 목표 설정 방식을 학습시키는 효과를 가집니다.
    2.  **신규 생성 시 복제:** 새로운 에이전트가 생성될 때, 현재 가장 성공적인 에이전트의 Q-테이블 전체(전략+전술)를 복제하여 부여합니다.
    3.  **변이 (Mutation):** 복제 시, Q-테이블의 값들에 약간의 무작위 변이를 주어 새로운 전략을 탐색할 기회를 제공합니다.

### 5.3. 가계 AI의 생존 최우선 학습

-   **죽음에 대한 강력한 처벌:** 가계 에이전트가 비활성화(사망)되는 순간, 해당 AI는 **매우 크고 즉각적인 부정적 보상**을 받습니다. 이는 AI에게 '이 행동은 절대 피해야 한다'는 강력한 학습 신호가 됩니다.
-   **생존 자체에 대한 보상:** `survival_need`가 낮은 수준으로 유지되고 가계가 활성 상태를 유지하는 것 자체에 대해 작은 긍정적 보상을 지속적으로 부여하여, AI가 '생존'을 최우선 목표로 삼도록 유도합니다.