# AI 의사결정 모듈 리팩토링 계획

## 1. 개요

현재 AI 의사결정 모듈, 특히 `simulation/ai_model.py` 파일은 여러 책임이 혼재되어 복잡성이 높고 디버깅이 어려운 상태입니다. 이 문제를 해결하고 코드의 유지보수성, 확장성, 테스트 용이성을 높이기 위해 단일 책임 원칙(Single Responsibility Principle)에 입각한 리팩토링을 진행합니다.

## 2. 목표

- **복잡성 감소**: 거대 클래스와 함수를 분리하여 코드의 복잡도를 낮춥니다.
- **책임 분리**: AI의 상태 구성, 모델 관리, 보상 계산, 의사결정 책임을 명확히 분리된 클래스에 위임합니다.
- **테스트 용이성 향상**: 각 컴포넌트를 독립적으로 테스트할 수 있는 구조를 만듭니다.
- **유지보수성 및 확장성 개선**: 향후 새로운 기능(다른 종류의 에이전트, 새로운 보상 체계 등)을 쉽게 추가할 수 있는 유연한 구조를 확보합니다.

## 3. 리팩토링 전략: 3개의 신규 클래스 도입

### 3.1. `StateBuilder` (상태 구성자)

- **책임**: 에이전트의 현재 상태(State)를 AI 모델이 이해할 수 있는 형식(feature dictionary)으로 구성합니다. 에이전트의 속성, 시장 데이터 등을 수집하고 가공하는 모든 로직을 이 클래스가 전담합니다.
- **현재 로직 위치**: `AIDecisionEngine._get_agent_state()`

### 3.2. `ModelWrapper` (모델 관리자)

- **책임**: 머신러닝 모델(`SGDRegressor`)과 데이터 변환기(`DictVectorizer`, `StandardScaler`)를 관리합니다. 모델의 훈련, 예측, 저장, 로딩과 관련된 모든 기술적인 세부사항을 처리하여, `scikit-learn` 라이브러리 의존성을 이 클래스 내에 캡슐화합니다.
- **현재 로직 위치**: `AIDecisionEngine` 및 `AITrainingManager` 전반에 분산

### 3.3. `RewardCalculator` (보상 계산기)

- **책임**: 특정 상태나 행동에 대한 보상(Reward)을 계산합니다. 단기 보상(자산 변화)과 장기 보상(자산과 기술 수준 등) 계산 로직을 모두 포함합니다.
- **현재 로직 위치**: `AITrainingManager.collect_experience()` 및 `AITrainingManager.end_episode()`

## 4. API 설계 및 클래스 간 상호작용

리팩토링 후 클래스 간의 상호작용은 다음과 같이 변경됩니다.

```
AITrainingManager
 │
 └─ 소유:
    ├─ StateBuilder
    ├─ RewardCalculator
    └─ AIDecisionEngine
          │
          └─ 소유:
             ├─ ModelWrapper
             └─ ActionProposalEngine
```

- **`AITrainingManager`**: 전체 AI 훈련 과정을 총괄하며, `StateBuilder`와 `RewardCalculator`를 사용하여 경험 데이터를 수집하고, `AIDecisionEngine`을 통해 모델을 훈련시킵니다.
- **`AIDecisionEngine`**: `ModelWrapper`를 사용하여 특정 상태에 대한 보상을 예측하고, `ActionProposalEngine`이 제안한 행동들 중 최적의 행동을 선택하는 역할에만 집중합니다.

## 5. 객체 초기화 전략

1.  **`AITrainingManager` 초기화**: `AITrainingManager`가 생성될 때, `StateBuilder`와 `RewardCalculator` 인스턴스도 함께 생성하여 소유합니다.
2.  **`AIDecisionEngine` 생성**: `AITrainingManager`가 특정 가치관(`value_orientation`)에 대한 엔진을 처음 요청받을 때(`get_engine`), 해당 가치관을 위한 `AIDecisionEngine`과 그 내부의 `ModelWrapper`를 생성합니다. 이로써 각 AI 엔진은 독립적인 모델을 갖게 됩니다.
3.  **의존성 주입**: `StateBuilder`나 `RewardCalculator`가 필요한 경우, `AITrainingManager`가 각 메서드에 인자로 전달하여 명시적인 의존성을 갖도록 합니다.

## 6. 단계별 리팩토링 실행 계획

1.  **`StateBuilder` 구현**: `AIDecisionEngine._get_agent_state` 로직을 `StateBuilder` 클래스로 이전합니다.
2.  **`ModelWrapper` 구현**: 모델 관리(`scikit-learn` 관련) 로직을 `ModelWrapper` 클래스로 이전합니다.
3.  **`RewardCalculator` 구현**: 보상 계산 로직을 `RewardCalculator` 클래스로 이전합니다.
4.  **기존 클래스 리팩토링**: `AIDecisionEngine`과 `AITrainingManager`를 단순화하여, 새로 만들어진 전문 클래스들을 사용하도록 코드를 재구성합니다.
