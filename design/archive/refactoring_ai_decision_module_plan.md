# AI 피라미드 아키텍처 설계 (AI Pyramid Architecture Design)

## 1. 개요 (Overview)

### 1.1. 문제 정의
현재 AI 의사결정 모델은 단일 구조(Monolithic)로, 가계의 상태를 입력받아 최종 행동(Order 리스트)을 직접 출력한다. 이 방식은 행동의 종류가 적을 때는 유효하지만, '투자', '학습' 등 복잡하고 추상적인 행동이 추가될수록 다음과 같은 확장성 및 유지보수 문제를 야기한다.

- **확장성 한계:** 새로운 행동 하나를 추가하기 위해 거대한 단일 AI 모델 전체를 수정하고 재훈련해야 한다.
- **성능 저하:** AI가 고려해야 할 경우의 수가 너무 많아져 학습이 비효율적이고 최적의 해를 찾기 어려워진다.
- **해석의 어려움:** AI의 특정 행동이 어떤 최종 목표를 위해 결정되었는지 직관적으로 파악하기 어렵다.

### 1.2. 목표
이 문제를 해결하기 위해, AI 의사결정 구조를 여러 계층으로 분리하는 **'AI 피라미드 아키텍처'**를 도입한다. 이 아키텍처의 목표는 다음과 같다.

- **모듈성 (Modularity):** 각 AI가 특정 영역의 의사결정에만 집중하도록 역할을 분리한다.
- **확장성 (Scalability):** 새로운 행동을 추가할 때, 전체가 아닌 특정 하위 AI 모듈만 수정/추가할 수 있도록 한다.
- **전문성 및 성능 향상 (Specialization & Performance):** 각 AI는 더 작은 문제에 집중하므로 더 작고, 빠르며, 효율적인 학습이 가능하다.

---

## 2. 아키텍처 다이어그램 (Architecture Diagram)

```
+--------------------------------+
|      Level 1: 전략 AI          |  (Strategic AI)
| (최상위 목표 Intention 결정)   |
+--------------------------------+
               |
               ▼ (e.g., 'INVEST')
+--------------------------------+
|      Level 2: 전술 AI          |  (Tactical AI)
| (구체적 방침 Tactic 결정)      |
+--------------------------------+
     |           |           |
     ▼           ▼           ▼
 (Tactic 1)  (Tactic 2)  (Tactic 3)
(e.g., 'STUDY') (e.g., 'BUY_STOCK')

+--------------------------------+
|      Level 3: 실행 엔진        |  (Execution Engine)
| (실제 Order 생성/상태 변경)    |
+--------------------------------+
```

---

## 3. 계층별 정의 (Layer Definitions)

### 3.1. Level 1: 전략 AI (Strategic AI)
- **역할:** 현재 에이전트의 전반적인 상태를 바탕으로 이번 턴에 달성해야 할 가장 중요한 **최상위 목표(Intention)**를 결정한다.
- **입력 (State):** 에이전트의 전체 상태 (자산, 모든 욕구, 고용 상태, 시장 거시 지표 등)
- **출력 (Decision):** `Intention` Enum 값 (예: `INVEST`, `CONSUME`, `WORK`)

### 3.2. Level 2: 전술 AI (Tactical AI)
- **역할:** '전략 AI'가 결정한 상위 목표를 달성하기 위한 가장 효과적인 **구체적인 행동 방침(Tactic)**을 결정한다. 각 `Intention` 별로 특화된 '전술 AI'가 존재할 수 있다.
- **입력 (State):** 상위에서 전달받은 `Intention` + 해당 목표와 관련된 에이전트의 세부 상태 (예: `INVEST` 목표의 경우, 현재 기술 수준, 시장 이자율 등)
- **출력 (Decision):** `Tactic` Enum 값 (예: `Intention`이 `INVEST`일 경우, `STUDY` 또는 `BUY_STOCK`을 출력)

### 3.3. Level 3: 실행 엔진 (Execution Engine)
- **역할:** '전술 AI'가 결정한 행동 방침을 실제 시뮬레이션 세계에서 실행한다.
- **입력 (Input):** `Tactic` Enum 값
- **출력 (Output):** 시장에 제출할 `List[Order]`를 생성하거나, 에이전트의 상태(예: 기술 수준)를 직접 변경한다.

---

## 4. 데이터 모델 (Data Models)

새로운 의사결정 흐름을 위해 `simulation/decisions/constants.py`와 같은 파일에 다음 Enum들을 정의한다.

### 4.1. `Intention` Enum
```python
from enum import Enum, auto

class Intention(Enum):
    DO_NOTHING = auto()      # 아무것도 안 함
    SATISFY_SURVIVAL_NEED = auto() # 생존 욕구 충족
    SATISFY_SOCIAL_NEED = auto()   # 사회적 욕구 충족 (모방 등)
    INCREASE_ASSETS = auto()     # 자산 증대
    IMPROVE_SKILLS = auto()      # 역량 강화 (장기 성장)
```

### 4.2. `Tactic` Enum
```python
from enum import Enum, auto

class Tactic(Enum):
    # SATISFY_SURVIVAL_NEED Tactics
    BUY_ESSENTIAL_GOODS = auto()

    # SATISFY_SOCIAL_NEED Tactics
    BUY_LUXURY_GOODS = auto()

    # INCREASE_ASSETS Tactics
    PARTICIPATE_LABOR_MARKET = auto()
    INVEST_IN_STOCKS = auto()
    START_BUSINESS = auto()

    # IMPROVE_SKILLS Tactics
    TAKE_EDUCATION = auto()
```

---

## 5. 단계별 구현 계획 (Phased Implementation Plan)

### 5.1. Phase 1: 프로토타입 구현
1.  **본 설계 문서 작성 완료.**
2.  **데이터 모델 정의:** `simulation/decisions/constants.py` 파일에 `Intention`과 `Tactic` Enum을 정의한다.
3.  **AI 클래스 구조 리팩토링:**
    - `BaseDecisionAI` 추상 클래스를 정의한다.
    - 기존 `AIDecisionEngine`을 '전략 AI' 역할을 하도록 리팩토링하여 `Intention`을 출력하게 한다.
    - `ConsumptionTacticalAI`를 새로 구현하여, `SATISFY_SURVIVAL_NEED` 목표를 받아 `BUY_ESSENTIAL_GOODS` 전술을 결정하도록 한다.
4.  **의사결정 흐름 조정:** `HouseholdDecisionEngine`이 이 새로운 피라미드 구조에 따라 각 AI를 순차적으로 호출하고 최종 주문을 생성하도록 전체 흐름을 조정한다.

### 5.2. Phase 2: 기능 확장
- 프로토타입이 안정적으로 작동하면, `INCREASE_ASSETS`와 `IMPROVE_SKILLS` 목표를 처리할 `InvestmentTacticalAI`, `LaborTacticalAI` 등을 추가로 구현하여 기능을 확장한다.

---

## 6. 모델 관리 시스템 (Model Management System)

- **`AIModelRegistry` 구축:** 피라미드 구조에 따라 여러 개로 나뉘는 AI 모델(`strategymodel.pkl`, `consumption_model.pkl` 등)을 효율적으로 로드하고 관리할 수 있는 중앙 레지스트리 클래스를 구현한다.
- **모델 파일명 규칙:** `[level]_[intention/tactic]_[version].pkl` (예: `L1_strategy_v1.pkl`, `L2_consume_v1.pkl`)과 같은 명명 규칙을 도입하여 관리를 용이하게 한다.