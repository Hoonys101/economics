# V2 AI 에이전트 특질 및 학습 방식 설계

## 1. 개요

모든 AI 에이전트가 동일한 방식으로 학습하고 행동하는 것을 넘어, 각자 고유의 '성향'을 가지도록 설계한다. 이를 위해 에이전트의 행동 경향성을 결정하는 **'특질 (Personality)'**과, 경험으로부터 배우는 방식을 결정하는 **'학습 초점 (Learning Focus)'**이라는 두 가지 새로운 개념을 도입한다.

---

## 2. 에이전트 특질 (Personality) 정의

에이전트의 특질은 단기적인 행동 선호도를 넘어, 에이전트의 **내적 상태(욕구) 변화**와 **장기적인 행동 경향성**을 모두 결정하는 핵심적인 요소이다.

### 2.1. 특질의 종류

1.  **수전노형 (Asset-Focused / Miser):**
    -   **핵심 동기:** 자산 증대 (`INCREASE_ASSETS`)
    -   **행동 경향:** 단기적인 욕구 충족보다는 자산을 축적하고, 소비를 최소화하는 행동을 선호한다.

2.  **지위추구형 (Status-Seeking):**
    -   **핵심 동기:** 사회적 욕구 충족 (`SATISFY_SOCIAL_NEED`)
    -   **행동 경향:** 자산을 소모하더라도, 다른 에이전트를 모방하여 사치재를 구매하는 등 사회적 지위를 높이는 행동을 선호한다.

3.  **학습형 (Growth-Oriented):**
    -   **핵심 동기:** 역량 강화 (`IMPROVE_SKILLS`)
    -   **행동 경향:** 당장의 자산 증대나 소비보다는, 교육/훈련 등 자신의 능력을 향상시키는 장기적인 투자 행동을 선호한다.

### 2.2. 특질의 구현: 2가지 핵심 메커니즘

#### 2.2.1. 메커니즘 1: 욕구 성장 가중치 (Desire Growth Weights)

특질은 시간이 지남에 따라 각 **욕구(Needs)가 증가하는 속도**에 직접적인 영향을 미쳐, 특질에 맞는 행동을 하도록 내적 동기를 지속적으로 유발한다.

-   **구현 방안:**
    -   각 에이전트는 생성 시 할당된 `Personality`에 따라 `desire_weights` 딕셔너리를 가진다.
    -   매 틱마다 `_update_needs` 메서드에서 기본 욕구 증가량(`BASE_DESIRE_GROWTH`)에 이 가중치를 곱하여 각 욕구를 차등적으로 증가시킨다.
-   **예시 `desire_weights` (상대적 성장률):**
    -   **수전노형:** `{'asset': 1.5, 'social': 0.5, 'improvement': 0.5}`
    -   **지위추구형:** `{'asset': 0.5, 'social': 1.5, 'improvement': 0.5}`
    -   **학습형:** `{'asset': 0.5, 'social': 0.5, 'improvement': 1.5}`
    -   (생존 욕구는 모든 특질에서 기본 성장률 1.0을 가짐)

#### 2.2.2. 메커니즘 2: 행동 선택 선호도 (Action Selection Preference)

특질은 여러 행동의 기대 보상(Q-value)이 비슷할 경우, **자신의 핵심 동기와 일치하는 `Intention`을 선택할 확률**을 높인다.

-   **구현 방안:**
    -   에이전트 생성 시, 3가지 특질 중 하나를 무작위 또는 특정 분포에 따라 할당한다.
    -   AI의 행동 선택 로직(`choose_action`)에서, 여러 `Intention`의 Q-값이 설정된 임계값(예: 5%) 이내로 유사할 경우, 자신의 `Personality`에 해당하는 `Intention`을 최종 행동으로 선택한다.

---

## 3. 학습 초점 (Learning Focus) 특질 설계

'학습 초점'은 계층적 Q-러닝에서, 최종 보상 신호를 **전략 AI(상위)와 전술 AI(하위) 중 어느 쪽에 더 비중을 두어 학습시킬지**를 결정하는 파라미터이다.

### 3.1. `learning_focus` 파라미터

- 각 에이전트는 `learning_focus`라는 0.0에서 1.0 사이의 값을 가진다.
- 이 값은 Q-러닝 업데이트 공식의 학습률(alpha, α)을 조절하는 데 사용된다.

### 3.2. 차등 학습률 (Differential Learning Rates) 적용

- **전략 AI의 학습률:** `alpha_strategy = base_alpha * learning_focus`
- **전술 AI의 학습률:** `alpha_tactic = base_alpha * (1.0 - learning_focus)`

하나의 최종 보상(reward)이 주어졌을 때, 각 계층의 Q-테이블은 자신에게 할당된 학습률에 따라 업데이트된다.

`Q_strategy(s, a) ← Q_strategy(s, a) + alpha_strategy * (delta)`
`Q_tactic(s, a) ← Q_tactic(s, a) + alpha_tactic * (delta)`

### 3.3. 학습 초점의 해석

- **`learning_focus`가 1.0에 가까울수록 (전략가 / Philosopher):**
    - `alpha_strategy`는 커지고 `alpha_tactic`은 0에 가까워진다.
    - 경험의 결과를 자신의 **장기적인 목표(`Intention`)가 올바른지**를 되돌아보는 데 주로 사용한다.

- **`learning_focus`가 0.0에 가까울수록 (기술가 / Tactician):**
    - `alpha_strategy`는 0에 가까워지고 `alpha_tactic`은 커진다.
    - 경험의 결과를 **목표 달성을 위한 `Tactic`을 개선**하는 데 주로 사용한다.

## 4. 기대 효과

- **에이전트 다양성 증대:** `특질`과 `학습 초점`이라는 두 축의 조합을 통해, "자신의 신념(전략)은 잘 바꾸지 않지만 돈 버는 기술(전술)은 기가 막히게 발전시키는 수전노(Miser-Tactician)" 또는 "돈 버는 방법은 서툴지만, 끊임없이 더 나은 삶의 목표(전략)를 고민하는 학습가(Growth-Strategist)"와 같이 훨씬 더 다채롭고 현실적인 에이전트들을 시뮬레이션에 등장시킬 수 있다.