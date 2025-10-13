# API 설계: HouseholdDecisionEngine

## 1. 목적

새롭게 구현된 V2 AI 아키텍처(`HouseholdAI`)를 실제 시뮬레이션 루프에 통합한다. 이를 위해 `DecisionEngine` 추상 클래스를 상속받는 구체적인 `HouseholdDecisionEngine`을 구현한다. 이 엔진은 `HouseholdAI`가 내린 추상적인 결정(`Tactic`)을 시장에 제출할 수 있는 구체적인 `Order` 객체로 변환하는 책임을 진다.

## 2. 관련 파일

-   **생성될 파일:** `simulation/decisions/household_decision_engine.py`
-   **수정될 파일:** `simulation/engine.py` (새로운 엔진을 사용하도록)
-   **참조할 파일:**
    -   `simulation/ai/household_ai.py`
    -   `simulation/ai/api.py`
    -   `simulation/decisions.py`
    -   `simulation/core_markets.py` (Order 클래스)

## 3. 클래스 및 API 명세

### 3.1. `HouseholdDecisionEngine` 클래스

**위치:** `simulation/decisions/household_decision_engine.py`

```python
from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING

from simulation.decisions import DecisionEngine
from simulation.ai.household_ai import HouseholdAI
from simulation.core_markets import Market, Order
from simulation.ai.enums import Tactic

if TYPE_CHECKING:
    from simulation.core_agents import Household

class HouseholdDecisionEngine(DecisionEngine):
    """
    가계 에이전트의 의사결정을 담당하는 구체적인 엔진.
    HouseholdAI를 사용하여 결정을 내리고, 이를 실제 시장 주문으로 변환한다.
    """

    def __init__(self, agent: Household):
        """
        HouseholdDecisionEngine의 생성자.
        에이전트에 특화된 AI 엔진 인스턴스를 생성하고 초기화한다.
        """
        self.agent = agent
        # AI 엔진 인스턴스화 (추후 AIDecisionEngine과의 관계 재정의 필요)
        self.ai_engine = HouseholdAI(agent_id=agent.id, ai_decision_engine=None) 
        # TODO: ai_decision_engine 인자를 어떻게 처리할지 결정해야 함. 
        # 현재는 순환 참조 문제로 None을 전달.

    def make_decisions(self, agent: Household, markets: Dict[str, Market], goods_data: List[Dict[str, Any]]) -> List[Order]:
        """
        AI 엔진을 사용하여 의사결정을 내리고, 이를 주문 목록으로 변환하여 반환한다.

        :param agent: 의사결정을 내릴 가계 에이전트.
        :param markets: 현재 시뮬레이션의 모든 시장 정보.
        :param goods_data: 시뮬레이션의 모든 재화 정보.
        :return: 생성된 주문(Order)의 리스트.
        """
        # 1. AI에 필요한 데이터 준비
        agent_data = agent.get_agent_data() # 에이전트 상태 데이터
        market_data = self._get_market_data(markets) # 시장 상태 데이터
        
        # 보상 계산을 위해 이전 상태 데이터를 저장해야 하지만, 
        # 학습은 엔진 외부에서 일어나므로 여기서는 의사결정에만 집중한다.
        pre_state_data = agent.get_pre_state_data() 

        # 2. AI를 통해 Tactic 결정
        # decide_and_learn 메서드는 학습 로직도 포함하지만, 이 단계에서는 결정된 Tactic만 사용.
        chosen_tactic = self.ai_engine.decide_and_learn(agent_data, market_data, pre_state_data)

        # 3. Tactic을 실제 Order로 변환
        orders = self._execute_tactic(chosen_tactic, agent, markets)

        return orders

    def _execute_tactic(self, tactic: Tactic, agent: Household, markets: Dict[str, Market]) -> List[Order]:
        """
        AI가 선택한 Tactic을 구체적인 시장 주문(Order)으로 변환한다.
        """
        if tactic == Tactic.BUY_ESSENTIAL_GOODS:
            # 생존에 필요한 'food' 1단위 구매 시도
            food_market = markets.get('food')
            if food_market and agent.assets > food_market.get_market_price():
                return [Order(agent, 'food', 1, food_market.get_market_price())]
        
        elif tactic == Tactic.PARTICIPATE_LABOR_MARKET:
            # 노동 시장에 노동력 1단위 판매 시도 (취업)
            labor_market = markets.get('labor')
            if labor_market:
                # 희망 임금은 일단 최저 임금으로 설정 (추후 AI가 결정하도록 고도화)
                desired_wage = agent.get_desired_wage() 
                return [Order(agent, 'labor', 1, desired_wage)]

        # TODO: 다른 Tactic(BUY_LUXURY_GOODS, INVEST_IN_STOCKS, TAKE_EDUCATION)에 대한 주문 생성 로직 추가
        
        return [] # 해당 Tactic에 대한 행동이 없으면 빈 리스트 반환

    def _get_market_data(self, markets: Dict[str, Market]) -> Dict[str, Any]:
        """
        AI에 필요한 시장 데이터를 수집하고 가공한다.
        """
        market_data = {}
        for name, market in markets.items():
            market_data[name] = {
                'price': market.get_market_price(),
                'demand': market.get_total_demand(),
                'supply': market.get_total_supply(),
            }
            # 노동 시장의 경우 추가 정보 수집
            if name == 'labor':
                # TODO: 실업률 계산 로직 추가
                market_data[name]['unemployment_rate'] = 0.1 # 임시값
                market_data[name]['avg_wage'] = market.get_average_wage()

        return market_data

```

## 4. 통합 계획

1.  **`simulation/decisions/`** 디렉토리를 생성합니다.
2.  위 명세에 따라 `simulation/decisions/household_decision_engine.py` 파일을 생성합니다.
3.  `simulation/engine.py`의 `run_tick` 메서드 내에서 가계 에이전트의 의사결정 부분을 수정합니다.
    -   기존의 임시 소비 로직을 제거합니다.
    -   각 가계 에이전트에 대해 `HouseholdDecisionEngine` 인스턴스를 생성합니다.
    -   `engine.make_decisions()`를 호출하여 주문을 받고, 이를 해당 시장에 제출합니다.

## 5. 학습 프로세스 (참고)

-   `HouseholdDecisionEngine`은 의사결정(Tactic -> Order)에만 집중합니다.
-   실제 학습(`ai_engine.update_learning()`)은 `simulation/engine.py`의 `run_tick` 메서드가 **종료된 후**, 한 틱 동안의 행동 결과(상태 변화, 보상)가 모두 집계된 시점에서 일괄적으로 호출되어야 합니다. 이는 설계 문서에 명시된 "틱 종료 후 학습" 원칙을 따릅니다.
