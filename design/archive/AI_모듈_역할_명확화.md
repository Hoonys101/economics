# AI 모듈 역할 명확화 (AI Module Role Clarification)

## 1. `AITrainingManager` 및 `AIDecisionEngine` 역할 명확화

### 1.1. 문제점
- 현재 `ai_model.py` 내 `AITrainingManager`와 `AIDecisionEngine` 클래스의 역할과 책임이 명확하게 분리되어 있지 않아, 코드 이해 및 유지보수에 어려움이 있습니다.
- 특히, `AITrainingManager`가 `AIDecisionEngine` 인스턴스를 관리하고 로드하는 역할을 하지만, `AIDecisionEngine` 자체도 모델 저장/로드 로직을 가지고 있어 혼란을 줄 수 있습니다.

### 1.2. 개선 방안

#### 1.2.1. `AIDecisionEngine`의 역할
- **주요 책임:**
    - 특정 `value_orientation` (가치관)을 가진 에이전트의 의사결정 로직을 캡슐화합니다.
    - 에이전트의 현재 상태를 기반으로 행동(주문)을 생성하고, 이에 대한 보상(reward)을 예측합니다.
    - AI 모델(예: `SGDRegressor`)을 사용하여 상태-행동-보상 매핑을 학습하고, 최적의 행동을 선택합니다.
    - 자신의 AI 모델(`self.model`)과 상태 벡터라이저(`self.vectorizer`)를 관리하고, 이를 파일(`ai_model_{value_orientation}.pkl`)로 저장(`save_model`)하고 로드(`load_model`)하는 기능을 수행합니다.
- **`AITrainingManager`와의 관계:** `AITrainingManager`에 의해 생성되고 관리됩니다. `AITrainingManager`는 `AIDecisionEngine`의 `save_model` 및 `load_model` 메서드를 호출하여 모델의 영속성을 관리합니다.

#### 1.2.2. `AITrainingManager`의 역할
- **주요 책임:**
    - 시뮬레이션 내 모든 `AIDecisionEngine` 인스턴스를 중앙에서 관리합니다.
    - 각 `value_orientation`에 해당하는 `AIDecisionEngine` 인스턴스를 제공(`get_engine`)합니다.
    - 에이전트의 경험 데이터(pre-state, post-state, transactions, reward)를 수집(`collect_experience`)하고, 이를 바탕으로 해당 `AIDecisionEngine`을 훈련(`end_episode`)시킵니다.
    - 에피소드 종료 시 모든 `AIDecisionEngine`의 모델을 저장하도록 지시합니다.
- **`AIDecisionEngine`과의 관계:** `AIDecisionEngine` 인스턴스를 생성하고, 이들의 훈련 및 모델 영속성(저장/로드)을 조율하는 상위 관리자 역할을 수행합니다.

### 1.3. 예상 효과
- AI 관련 코드의 책임이 명확해져 코드 이해 및 유지보수가 용이해집니다.
- AI 모델의 훈련 및 관리가 체계화되어 확장성이 향상됩니다.
- 각 클래스의 역할이 명확해짐에 따라 향후 AI 모델 교체 또는 훈련 방식 변경 시 유연하게 대응할 수 있습니다.
