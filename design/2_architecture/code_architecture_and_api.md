# 프로젝트 아키텍처 및 API 관계도

이 문서는 "살아있는 디지털 경제" 프로젝트의 핵심 아키텍처, 주요 컴포넌트 간의 상호작용(API), 그리고 데이터 흐름을 설명합니다. 복잡한 시스템의 구조를 한눈에 파악하고, 향후 유지보수 및 기능 확장을 용이하게 하는 것을 목표로 합니다.

## 1. 핵심 컴포넌트 개요 (Core Components)

| 컴포넌트 | 파일 위치 | 주요 역할 |
| :--- | :--- | :--- |
| **Simulation** | `simulation/engine.py` | 시뮬레이션의 전체 흐름(시간, 틱)을 관장하는 메인 엔진 |
| **BaseAgent** | `simulation/base_agent.py` | 모든 에이전트(가계, 기업)의 기반이 되는 추상 클래스 |
| **Household / Firm** | `simulation/core_agents.py` | 경제 활동의 주체. `BaseAgent`를 상속받아 구현됨 |
| **DecisionEngine** | `simulation/decisions/*` | AI의 결정을 실제 시장 주문으로 변환하는 의사결정 로직 |
| **HouseholdAI / FirmAI** | `simulation/ai/*` | 강화학습을 통해 에이전트의 행동(Tactic)을 결정하는 AI 두뇌 |
| **AIDecisionEngine** | `simulation/ai_model.py` | AI 모델(알고리즘)을 래핑하고, 예측/학습/저장/로드를 담당 |
| **AIEngineRegistry** | `simulation/ai_model.py` | 모든 AI 엔진 인스턴스를 생성하고 관리하는 중앙 레지스트리 |
| **OrderBookMarket** | `simulation/markets/*` | 주문을 받아 매칭하고 거래를 체결시키는 시장 메커니즘 |
| **EconomicIndicatorTracker** | `simulation/engine.py` | GDP, 실업률 등 거시 경제 지표를 추적 및 기록 |
| **SimulationRepository** | `simulation/db/repository.py` | 시뮬레이션 데이터를 데이터베이스에 저장하고 조회하는 역할 |

---

## 2. 주요 상호작용 흐름 (Key Interaction Flows)

### 2.1. 시뮬레이션 1틱(Tick) 흐름

`Simulation.run_tick()` 메서드가 호출될 때의 핵심적인 상호작용 순서입니다.

```
[Simulation.run_tick]
    |
    | 1. 시장 데이터 준비 (_prepare_market_data)
    |
    +--> [Firm.make_decision] -> [FirmDecisionEngine] -> AI를 통해 상품 판매/구인 주문(Order) 생성
    |
    +--> [Household.make_decision] -> [HouseholdDecisionEngine] -> AI를 통해 상품 구매/구직 주문(Order) 생성
    |
    | 2. 모든 주문을 각 Market에 제출 (market.place_order)
    |
    +--> [OrderBookMarket.match_and_execute_orders]
    |       |
    |       L--> 거래(Transaction) 목록 반환
    |
    | 3. 거래 결과 처리 (_process_transactions)
    |       |
    |       L--> 에이전트 자산, 재고, 고용상태 업데이트
    |
    | 4. AI 모델 학습 (household.decision_engine.ai_engine.update_learning)
    |       |
    |       L--> 행동 전/후 상태와 보상을 기반으로 Q-table 업데이트
    |
    | 5. 생산 및 소비 활동
    |       |
    |       +--> [Firm.produce]
    |       L--> [Household.decide_and_consume]
    |
    | 6. 에이전트 상태 업데이트 및 생명주기 관리
    |       |
    |       L--> 욕구 업데이트, 파산/폐업 처리 (_handle_agent_lifecycle)
    |
    | 7. 경제 지표 업데이트
    |       |
    |       L--> [EconomicIndicatorTracker.update] -> [SimulationRepository.save_economic_indicator]
    |
    L--> 틱(Tick) 종료
```

### 2.2. 가계(Household) AI 의사결정 흐름

가계 에이전트 하나가 소비/노동 결정을 내리는 과정의 상세 흐름입니다. 데이터의 일관성과 효율성을 위해 '상태 스냅샷'을 생성하여 재사용하는 모델을 따릅니다.

```
[Household.make_decision]
    |
    | 1. '에이전트 상태 스냅샷' 생성
    |    (자산, 욕구, 재고, 시장 정보 등 현시점의 모든 데이터를 종합)
    |
    +--> [HouseholdAI.decide_and_learn(snapshot)]
    |       |
    |       | 1. 스냅샷을 분석하여 '의도(Intention)' 결정
    |       | 2. '의도'와 스냅샷을 분석하여 '전술(Tactic)' 및 '적극성(Aggressiveness)' 결정
    |       | 3. 최종 결정 `(Tactic, Aggressiveness)` 반환
    |       |
    |       L--> (학습 단계에서는 Q-table 업데이트도 수행)
    |
    | 2. 실행 엔진에 AI의 결정과 상태 스냅샷 전달
    |
    +--> [HouseholdDecisionEngine.make_orders(decision, snapshot)]
            |
            | 1. AI의 결정(예: '공격적 식량 구매')을 해석
            | 2. 함께 전달된 스냅샷의 데이터(예: 전체 자산)를 참조하여 규칙에 따라 최종 가격/수량 결정
            | 3. 시장에 제출할 주문(Order) 리스트 생성
            |
            L--> 주문(Order) 리스트 반환
```

---

## 3. 컴포넌트별 API 및 관계

### 3.1. `Simulation`
- **역할**: 시뮬레이션의 지휘자(Orchestrator). 모든 컴포넌트를 생성하고 `run_tick`을 통해 각 스텝을 조율.
- **주요 API**:
    - `run_tick()`: 한 틱의 시뮬레이션을 실행.
    - `_prepare_market_data()`: AI 의사결정에 필요한 시장 데이터를 가공하여 제공.
    - `_process_transactions()`: 체결된 거래를 바탕으로 에이전트 상태를 업데이트.
    - `_handle_agent_lifecycle()`: 에이전트의 파산, 실업 등을 처리.
- **의존성**: `Household`, `Firm`, `Market`, `EconomicIndicatorTracker`, `AIEngineRegistry`, `SimulationRepository`

### 3.2. `BaseAgent` (`Household`, `Firm`)
- **역할**: 경제 활동의 주체. 자산, 재고, 욕구 등의 상태를 가지며 의사결정을 수행.
- **주요 API**:
    - `make_decision()`: `DecisionEngine`을 호출하여 주문을 생성.
    - `get_agent_data()`: AI 분석에 필요한 자신의 상태 데이터를 반환.
    - `update_needs()`: 시간이 지남에 따라 변화하는 욕구를 업데이트.
    - `clone()`: 자신과 동일한(또는 유사한) 새로운 에이전트를 복제.
- **의존성**: `DecisionEngine`

### 3.3. `DecisionEngine` (`HouseholdDecisionEngine`)
- **역할**: AI의 추상적인 '전술'을 구체적인 '시장 주문'으로 번역하는 중간 다리.
- **주요 API**:
    - `make_decisions()`: AI 엔진을 호출하여 `Tactic`을 얻고, 이를 `Order` 리스트로 변환하여 반환.
    - `_execute_tactic()`: `Tactic` 종류에 따라 적절한 `Order`를 생성.
- **의존성**: `HouseholdAI`, `Market`, `Order`

### 3.4. `BaseAIEngine` (`HouseholdAI`)
- **역할**: 에이전트의 두뇌. 강화학습(Q-learning)을 통해 주어진 상태에서 최적의 행동을 결정.
- **주요 API**:
    - `decide_and_learn()`: 현재 상태에 따라 행동을 결정하고, 이전 행동의 결과를 바탕으로 학습(Q-table 업데이트).
    - `choose_intention()` / `choose_tactic()`: 2단계 의사결정(전략적->전술적).
    - `_get_strategic_state()` / `_get_tactical_state()`: 상태 정의 함수.
    - `_calculate_reward()`: 행동에 대한 보상 계산 함수.
    - `set_ai_decision_engine()`: 순환 참조 해결을 위해 `AIDecisionEngine`을 외부에서 주입받음.
- **의존성**: `AIDecisionEngine` (선택적, 예측 보상 사용 시)

### 3.5. `AIDecisionEngine` & `AIEngineRegistry`
- **역할**:
    - `AIDecisionEngine`: 실제 머신러닝 모델(`scikit-learn` 등)을 감싸고, `predict`, `train` API를 제공.
    - `AIEngineRegistry`: 가치관(`value_orientation`)별로 `AIDecisionEngine` 인스턴스를 관리하는 팩토리 및 레지스트리.
- **주요 API**:
    - `AIEngineRegistry.get_engine()`: 특정 가치관의 AI 엔진을 가져오거나 생성.
    - `AIDecisionEngine.predict()`: 주어진 상태에 대한 예측값(보상)을 반환.
    - `AIDecisionEngine.train()`: 상태-보상 데이터를 기반으로 내부 모델을 학습.
- **의존성**: `ModelWrapper` (내부적으로 ML 라이브러리 사용)

### 3.6. `OrderBookMarket`
- **역할**: 수요(buy)와 공급(sell) 주문을 받아 가격 우선, 시간 우선 원칙에 따라 매칭.
- **주요 API**:
    - `place_order()`: 새로운 주문을 오더북에 추가.
    - `match_and_execute_orders()`: 오더북을 스캔하여 체결 가능한 모든 거래를 실행하고 `Transaction` 리스트를 반환.
    - `get_best_ask()` / `get_best_bid()`: 현재 시장의 최저 판매가 / 최고 구매가를 조회.
- **의존성**: `Order`, `Transaction`

---

## 4. 에이전트별 가격 및 수량 결정 알고리즘 (Agent-Specific Price and Quantity Determination Algorithms)

AI가 행동 방침(Tactic)을 결정한 후, 실제 시장에 제출될 주문(Order)의 구체적인 가격과 수량은 다음 알고리즘에 따라 결정됩니다.

### 4.1. 가계 (Household)

#### 4.1.1. 상품 구매 시 (예: 식량, 사치품, 교육 서비스)
*   **가격 결정:** 가계는 '가격 수용자(Price Taker)'처럼 행동합니다. 시장의 **최저 매도 호가(Best Ask)**를 조회하여 그 가격으로 매수 주문을 제출합니다.
    *   **코드 위치:** `simulation/decisions/household_decision_engine.py`의 `_execute_tactic` 메서드
    *   **예시:** `price = goods_market.get_best_ask('food')`
*   **수량 결정:** 현재 로직에서는 **`1` 단위로 고정**되어 있습니다.
    *   **코드 위치:** `simulation/decisions/household_decision_engine.py`의 `_execute_tactic` 메서드
    *   **예시:** `orders.append(Order(agent.id, 'buy', 'food', 1, price, goods_market.id))`

#### 4.1.2. 노동 판매 시 (구직)
*   **가격(임금) 결정:** `agent.get_desired_wage()` 메서드를 호출하여 희망 임금을 결정하려고 합니다.
    *   **코드 위치:** `simulation/decisions/household_decision_engine.py`의 `_execute_tactic` 메서드
    *   **현재 상태:** `simulation/core_agents.py`의 `Household` 클래스에 `get_desired_wage()` 메서드가 구현되어 있습니다.
*   **수량 결정:** **`1` 단위(한 명의 노동력)로 고정**되어 있습니다.
    *   **코드 위치:** `simulation/decisions/household_decision_engine.py`의 `_execute_tactic` 메서드
    *   **예시:** `orders.append(Order(agent.id, 'sell', 'labor', 1, desired_wage, labor_market.id))`

### 4.2. 기업 (Firm)

#### 4.2.1. 상품 판매 시
*   **가격 결정:** **동적 가격 책정 알고리즘**을 사용합니다.
    1.  **기준 가격:** 이전 틱에서 판매했던 가격(`firm.last_prices`)을 기준으로 시작합니다. (초기값은 `config.GOODS_MARKET_SELL_PRICE`)
    2.  **재고 기반 조정:** 목표 재고량(`firm.production_targets`) 대비 현재 재고(`current_inventory`) 수준을 비교하여 가격을 조정합니다.
        *   재고가 목표보다 많으면(`OVERSTOCK_THRESHOLD` 초과) 가격을 낮춥니다.
        *   재고가 목표보다 적으면(`UNDERSTOCK_THRESHOLD` 미만) 가격을 높입니다.
        *   가격 조정의 민감도는 `config.PRICE_ADJUSTMENT_FACTOR` 및 `config.PRICE_ADJUSTMENT_EXPONENT`에 의해 제어됩니다.
    3.  **최종 가격:** 조정된 가격은 `config.MIN_SELL_PRICE`와 `config.MAX_SELL_PRICE` 범위 내로 제한됩니다.
    *   **코드 위치:** `simulation/decisions/firm_decision_engine.py`의 `make_decisions` 메서드
*   **수량 결정:** 판매할 수량은 **현재 보유한 재고 전체**(`current_inventory`)입니다. 다만, `config.MAX_SELL_QUANTITY`를 초과하지 않도록 제한됩니다.
    *   **코드 위치:** `simulation/decisions/firm_decision_engine.py`의 `make_decisions` 메서드
    *   **예시:** `quantity_to_sell = min(current_inventory, self.config_module.MAX_SELL_QUANTITY)`

#### 4.2.2. 노동 구매 시 (고용)
*   **가격(임금) 결정:** **동적 임금 책정 알고리즘**을 사용합니다.
    1.  **수익성 기반:** 기업의 최근 수익성 이력(`firm.profit_history`)을 바탕으로 `config.BASE_WAGE`에 '수익 기반 프리미엄'을 추가합니다.
    2.  **경쟁 기반:** 이전 틱에서 고용에 실패했거나, 필요한 노동력이 현재 고용된 직원보다 많을 경우, '경쟁 프리미엄'을 추가하여 임금을 높입니다.
    *   **코드 위치:** `simulation/decisions/firm_decision_engine.py`의 `_calculate_dynamic_wage_offer` 메서드 및 `make_decisions` 메서드
*   **수량 결정:** 생산 목표 달성에 필요한 노동력(`total_needed_labor`)과 현재 고용된 직원 수(`len(firm.employees)`)를 비교하여 직원이 더 필요하다고 판단되면, **`1` 명을 추가로 고용**하기 위한 매수 주문을 제출합니다.
    *   **코드 위치:** `simulation/decisions/firm_decision_engine.py`의 `make_decisions` 메서드
    *   **예시:** `order = Order(firm.id, 'BUY', 'labor', 1.0, offered_wage, 'labor_market')`