# AI 통합 문제 해결 및 API 개선 설계안

### 1. 문제 정의

현재 AI 시스템은 잘 설계된 두뇌(`HouseholdAI`)와 이를 실제 행동으로 옮겨야 하는 몸(`HouseholdDecisionEngine`) 사이의 신경망 연결이 일부 끊어져 있는 상태입니다.

1.  **핵심 연결고리 부재 (순환 참조 및 의존성 주입 실패):**
    *   **문제:** `HouseholdAI`는 학습(Q-러닝) 시, 더 나은 장기적 판단을 위해 상위 엔진인 `AIDecisionEngine`이 예측하는 '미래 보상 값'을 참조해야 합니다. 하지만 두 클래스가 서로를 필요로 하는 구조 때문에 초기화 시점에 순환 참조가 발생합니다.
    *   **현재 상태:** 이 문제를 해결하기 위해 `HouseholdDecisionEngine`에서 `AIDecisionEngine` 인스턴스를 나중에 주입(`set_ai_decision_engine`)하려는 시도가 있으나, 정작 `HouseholdAI` 클래스에는 해당 메서드가 존재하지 않아 **연결이 실패**하고 있습니다. 이로 인해 `HouseholdAI`의 보상 계산 로직에서 가장 중요한 부분 중 하나인 예측 보상(`predicted_reward`)이 **현재 전혀 작동하지 않습니다.**

2.  **미구현된 행동 결정 로직 (`Tactic` 실행 부재):**
    *   **문제:** `HouseholdAI`는 '사치품 구매'나 '교육 수강'과 같은 고차원적인 전술(`Tactic`)을 결정할 수 있도록 설계되었습니다. 하지만 `HouseholdDecisionEngine`의 `_execute_tactic` 메서드에는 이 결정들을 실제 시장 주문(`Order`)으로 변환하는 코드가 구현되어 있지 않습니다.
    *   **결과:** AI가 아무리 '인정 욕구'나 '성장 욕구'를 충족시키려 해도, 실제 행동으로 이어지지 않아 **반쪽짜리 의사결정**에 머물러 있습니다.

### 2. 해결 방안

1.  **의존성 주입(Dependency Injection) 패턴 완성:**
    *   `HouseholdAI` 클래스에 `AIDecisionEngine` 인스턴스를 외부에서 설정할 수 있는 공식적인 API(메서드)를 추가합니다. 이를 통해 초기화 시점의 순환 참조 문제를 완전히 해결하고, 두뇌와 상위 엔진 간의 연결을 완성합니다.

2.  **행동 결정 로직(`_execute_tactic`) 확장:**
    *   `HouseholdDecisionEngine`이 모든 `Tactic`을 이해하고 실행할 수 있도록 `BUY_LUXURY_GOODS`와 `TAKE_EDUCATION`에 대한 주문 생성 로직을 구현합니다.
    *   이를 위해 시뮬레이션의 상품 데이터(`goods.json` 등)에 어떤 상품이 '사치품'이고 '교육'인지 식별할 수 있는 명확한 기준(예: `category` 속성)을 정의합니다.

### 3. API 변경 및 신규 설계

아래와 같이 기존 코드의 API를 변경하고 신규 로직을 추가할 것을 제안합니다.

#### 3.1. `simulation/ai/household_ai.py` : `HouseholdAI` 클래스 수정

`AIDecisionEngine`을 주입받을 수 있는 public 메서드를 추가합니다.

```python
# simulation/ai/household_ai.py

from typing import Any, Dict, List, Tuple, TYPE_CHECKING

from .api import BaseAIEngine, Intention, Tactic

if TYPE_CHECKING:
    from simulation.ai_model import AIDecisionEngine

class HouseholdAI(BaseAIEngine):
    def __init__(self, agent_id: str, gamma: float = 0.9, epsilon: float = 0.1, base_alpha: float = 0.1, learning_focus: float = 0.5):
        super().__init__(agent_id, gamma, epsilon, base_alpha, learning_focus)
        # AIDecisionEngine 인스턴스를 저장할 속성 초기화
        self.ai_decision_engine: AIDecisionEngine | None = None

    # --- NEW METHOD ---
    def set_ai_decision_engine(self, engine: AIDecisionEngine):
        """
        AIDecisionEngine 인스턴스를 외부에서 주입받아 설정합니다.
        이 메서드는 순환 참조 문제를 해결하기 위해 사용됩니다.
        """
        self.ai_decision_engine = engine
    # --- END NEW METHOD ---

    # ... (기존의 _discretize, _get_strategic_state 등 다른 메서드는 그대로 유지) ...

    def _calculate_reward(self, pre_state_data: Dict[str, Any], post_state_data: Dict[str, Any], agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """
        가계 행동의 결과로 얻어지는 보상을 계산한다.
        (이하 로직은 기존과 동일)
        """
        # ... (기존 보상 계산 로직) ...
        
        # 이제 self.ai_decision_engine이 정상적으로 주입되므로 아래 코드가 작동함
        if self.ai_decision_engine:
            predicted_reward = self.ai_decision_engine.get_predicted_reward(agent_data, market_data)
            reward += predicted_reward * 0.05 
        
        return reward
```

#### 3.2. `simulation/decisions/household_decision_engine.py` : `_execute_tactic` 메서드 확장

'사치품'과 '교육' 구매 로직을 추가합니다.

```python
# simulation/decisions/household_decision_engine.py

# ... (imports) ...

class HouseholdDecisionEngine(DecisionEngine):
    # ... (__init__, make_decisions 등) ...

    def _execute_tactic(self, tactic: Tactic, agent: Household, markets: Dict[str, Market]) -> List[Order]:
        """
        AI가 선택한 Tactic을 구체적인 시장 주문(Order)으로 변환한다.
        """
        orders = []
        goods_market = markets.get('goods_market')

        if tactic == Tactic.BUY_ESSENTIAL_GOODS:
            # 'food'는 필수재로 간주
            if goods_market and agent.assets > goods_market.get_market_price('food'):
                orders.append(Order(agent, 'food', 1, goods_market.get_market_price('food')))
        
        elif tactic == Tactic.PARTICIPATE_LABOR_MARKET:
            labor_market = markets.get('labor')
            if labor_market:
                desired_wage = agent.get_desired_wage() 
                orders.append(Order(agent, 'labor', 1, desired_wage))

        # --- NEW LOGIC ---
        elif tactic == Tactic.BUY_LUXURY_GOODS:
            # 'luxury_good' ID를 가진 상품을 사치품으로 간주
            if goods_market:
                price = goods_market.get_market_price('luxury_good')
                if price is not None and agent.assets > price:
                    orders.append(Order(agent, 'luxury_good', 1, price))

        elif tactic == Tactic.TAKE_EDUCATION:
            # 'education_service' ID를 가진 상품을 교육으로 간주
            if goods_market:
                price = goods_market.get_market_price('education_service')
                if price is not None and agent.assets > price:
                    orders.append(Order(agent, 'education_service', 1, price))
        # --- END NEW LOGIC ---
        
        return orders
```

### 4. 기대 효과

위 설계안이 적용되면 다음과 같은 개선이 기대됩니다.

*   **AI 학습 완전 정상화:** `HouseholdAI`가 `AIDecisionEngine`의 예측 보상을 정상적으로 활용하게 되어, Q-러닝 기반의 장기적이고 전략적인 학습이 가능해집니다.
*   **에이전트 행동 다변화:** 가계 에이전트가 생존뿐만 아니라 사회적 지위나 능력 향상을 위해서도 소비 활동을 시작하여, 시뮬레이션의 경제 현상이 더욱 다채롭고 현실적으로 변합니다.
*   **안정적인 확장 기반 마련:** 명확한 API와 의존성 주입 패턴은 향후 기업 AI(`FirmAI`)나 다른 종류의 AI 에이전트를 추가할 때 발생할 수 있는 유사한 문제들을 예방하는 좋은 선례가 됩니다.
