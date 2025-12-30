# Backend Diagnosis Test Suite - Jules 구현 지침서

> **문서 유형**: 구현자(Jules) 전용 명세서  
> **승인 상태**: Architect Prime 승인 완료  
> **목적**: GDP 0, 실업률 100%, OrderBook 시각화 불가 증상 진단

---

## 1. 개요

### 1.1 문제 상황
시뮬레이션이 "식물인간(Vegetative State)" 상태:
- GDP가 0으로 보고됨
- 실업률이 100%로 보고됨
- OrderBook 시각화가 불가능함

### 1.2 진단 전략
**상류(Source) → 하류(Sink)** 순서로 데이터 파이프라인 검증:

| 순서 | Spec | 진단 대상 | 파일명 |
|:---:|:---:|:---|:---|
| 1 | Spec 0 | 에이전트 주문 생성 | `test_agent_decision.py` |
| 2 | Spec 1 | 시장 매칭 로직 | `test_market_mechanics.py` |
| 3 | Spec 2 | 지표 집계 로직 | `test_indicator_pipeline.py` |
| 4 | Spec 3 | API 직렬화 | `test_api_contract.py` (추후) |

---

## 2. 공통 설정

### 2.1 파일 구조
```
tests/
└── diagnosis/
    ├── __init__.py
    ├── conftest.py          # 공용 Fixtures
    ├── test_agent_decision.py
    ├── test_market_mechanics.py
    └── test_indicator_pipeline.py
```

### 2.2 의존성 (conftest.py)
```python
# 필수 Import
from simulation.core_agents import Household, Talent, Personality
from simulation.firms import Firm
from simulation.markets.order_book_market import OrderBookMarket
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.models import Order, Transaction
```

### 2.3 Mock Config Module (conftest.py에 Fixture로)
```python
@pytest.fixture
def mock_config_module():
    config = Mock()
    config.GOODS = {"basic_food": {"initial_price": 10.0}}
    config.LABOR_MARKET_MIN_WAGE = 5.0
    config.NEED_INCREASE_BASE_VALUES = {"survival": 5.0, "labor_need": 1.0}
    # ... 기타 필수 설정
    return config
```

---

## 3. Spec 0: Agent Decision Verification

### 3.1 목적
에이전트의 `make_decision()` 호출 시 **빈 리스트가 아닌 유효한 Order 객체**가 반환되는지 확인.

> **핵심 질문**: 에이전트가 주문을 생성하고 있는가?

### 3.2 파일 경로
`tests/diagnosis/test_agent_decision.py`

### 3.3 테스트 케이스

#### TC-0.1: 배고픈 가계의 구매 주문 생성
```
조건:
  - Household.needs["survival"] = 50.0 (높음)
  - Household.assets = 1000.0 (충분)
  - Household.inventory["basic_food"] = 0 (없음)

행동:
  orders, _ = household.make_decision(markets, goods_data, market_data, time=1)

검증:
  ASSERT len(orders) > 0, "배고픈 가계가 식량 구매 주문을 생성하지 않음"
  ASSERT orders[0].order_type == "bid"
```

#### TC-0.2: 재고 보유 기업의 판매 주문 생성
```
조건:
  - Firm.inventory["basic_food"] = 50 (있음)
  - Firm.assets = 5000.0 (충분)
  - Firm.is_active = True

행동:
  orders, _ = firm.make_decision(markets, goods_data, market_data, time=1)

검증:
  ASSERT len(orders) > 0, "재고가 있는 기업이 판매 주문을 생성하지 않음"
  ASSERT orders[0].order_type == "ask"
```

### 3.4 결과 해석
| 결과 | 의미 | 다음 단계 |
|:---:|:---|:---|
| FAIL | AI Decision Engine이 주문을 생성하지 않음 | Decision Engine 디버깅 |
| PASS | 주문은 생성됨 | Spec 1로 진행 |

---

## 4. Spec 1: Market Matching Integrity

### 4.1 목적
`OrderBookMarket.place_order()`와 `match_orders()`가 정상 작동하여 **Transaction 객체를 반환**하는지 확인.

> **핵심 질문**: 주문이 시장에서 매칭되고 있는가?

### 4.2 파일 경로
`tests/diagnosis/test_market_mechanics.py`

### 4.3 API 정렬 (중요!)
실제 코드의 메서드 시그니처:
```python
# 주문 제출
market.place_order(order: Order, current_time: int) -> None

# 매칭 실행 (거래 반환)
market.match_orders(current_time: int) -> List[Transaction]

# Order 생성
Order(agent_id, order_type, item_id, quantity, price, market_id)
```

### 4.4 테스트 케이스

#### TC-1.1: 가격 일치 시 거래 성사
```
조건:
  market = OrderBookMarket(market_id="basic_food")
  ask = Order(agent_id=1, order_type="ask", item_id="basic_food", quantity=10, price=100, market_id="basic_food")
  bid = Order(agent_id=2, order_type="bid", item_id="basic_food", quantity=5, price=100, market_id="basic_food")

행동:
  market.place_order(ask, current_time=1)
  market.place_order(bid, current_time=1)
  transactions = market.match_orders(current_time=1)

검증:
  ASSERT len(transactions) > 0, "가격 일치 주문이 매칭되지 않음"
  ASSERT transactions[0].quantity == 5
  ASSERT transactions[0].price == 100
```

#### TC-1.2: 잔여 물량 확인
```
(TC-1.1 이후)

행동:
  remaining_asks = market.get_all_asks("basic_food")
  total_remaining = sum(o.quantity for o in remaining_asks)

검증:
  ASSERT total_remaining == 5, "잔여 매도 물량이 5여야 함"
```

#### TC-1.3: 가격 불일치 시 거래 불성사
```
조건:
  ask = Order(..., price=100)
  bid = Order(..., price=80)  # 더 낮음

검증:
  ASSERT len(transactions) == 0
```

### 4.5 결과 해석
| 결과 | 의미 | 다음 단계 |
|:---:|:---|:---|
| FAIL | 매칭 로직 자체에 버그 | OrderBookMarket 디버깅 |
| PASS | 시장 매칭은 정상 | Spec 2로 진행 |

---

## 5. Spec 2: Indicator Tracker Verification

### 5.1 목적
`EconomicIndicatorTracker`가 **GDP 필드를 가지고 있는지**, 그리고 대체 지표가 올바르게 집계되는지 확인.

> **핵심 발견**: 코드베이스 분석 결과 **`gdp` 필드가 존재하지 않음**. 프론트엔드가 잘못된 필드를 요청하고 있을 가능성 높음.

### 5.2 파일 경로
`tests/diagnosis/test_indicator_pipeline.py`

### 5.3 테스트 케이스

#### TC-2.1: GDP 필드 존재 여부 확인 (핵심!)
```
조건:
  tracker = EconomicIndicatorTracker(config_module=mock_config)
  tracker.track(time=1, households=[], firms=[], markets={})

행동:
  indicators = tracker.get_latest_indicators()

검증:
  IF "gdp" NOT IN indicators:
      PRINT "[WARNING] GDP 필드가 존재하지 않음!"
      PRINT "  -> 프론트엔드가 gdp를 요청한다면 이것이 원인"
  
  # 사용 가능한 필드 출력
  FOR key, value IN indicators.items():
      PRINT f"  - {key}: {value}"
```

#### TC-2.2: total_production 집계 확인
```
조건:
  firm1 = Mock(is_active=True, current_production=100)
  firm2 = Mock(is_active=True, current_production=50)
  tracker.track(time=1, households=[], firms=[firm1, firm2], markets={})

검증:
  indicators = tracker.get_latest_indicators()
  ASSERT indicators["total_production"] == 150
```

#### TC-2.3: 실업률 100% 시나리오 재현
```
조건:
  모든 가계의 is_employed = False

검증:
  ASSERT indicators["unemployment_rate"] == 100.0
  PRINT "  -> 실업률 100%가 정상 계산됨. 노동시장 매칭 문제일 가능성"
```

### 5.4 결과 해석
| 결과 | 의미 | 다음 단계 |
|:---:|:---|:---|
| GDP 필드 없음 | 프론트엔드-백엔드 필드명 불일치 | API 스키마 동기화 |
| 지표 값 0 | 데이터 전달 파이프라인 문제 | Engine → Tracker 연결 검토 |

---

## 6. 테스트 실행 방법

```bash
# 전체 진단 스위트 실행
pytest tests/diagnosis/ -v --tb=short

# 개별 Spec 실행
pytest tests/diagnosis/test_agent_decision.py -v
pytest tests/diagnosis/test_market_mechanics.py -v
pytest tests/diagnosis/test_indicator_pipeline.py -v

# 진단 로그 출력 포함
pytest tests/diagnosis/ -v -s
```

---

## 7. 예상 결과 시나리오

### 시나리오 A: 에이전트가 주문을 안 냄
```
Spec 0 FAIL → AI Decision Engine 문제
  └─> AIDrivenHouseholdDecisionEngine.make_decisions() 디버깅
```

### 시나리오 B: 주문은 있으나 매칭 안 됨
```
Spec 0 PASS, Spec 1 FAIL → OrderBookMarket 버그
  └─> _match_orders_for_item() 디버깅
```

### 시나리오 C: 거래는 되나 지표가 0
```
Spec 0 PASS, Spec 1 PASS, Spec 2 FAIL → Tracker 연결 문제
  └─> Engine.run_tick() 내 tracker.track() 호출 확인
```

### 시나리오 D: GDP 필드 불일치
```
Spec 2에서 "gdp" 필드 미존재 확인
  └─> 프론트엔드가 "total_production" 또는 다른 필드를 사용하도록 수정
```

---

## 8. 구현 우선순위

1. **conftest.py** 작성 (공용 Fixture)
2. **test_agent_decision.py** (Spec 0)
3. **test_market_mechanics.py** (Spec 1)
4. **test_indicator_pipeline.py** (Spec 2)
5. 테스트 실행 및 결과 보고

---

## 부록: 실제 메서드 시그니처 참조

### Household.make_decision()
```python
def make_decision(
    self,
    markets: Dict[str, "Market"],
    goods_data: List[Dict[str, Any]],
    market_data: Dict[str, Any],
    current_time: int,
    government: Optional[Any] = None,
) -> Tuple[List["Order"], Tuple["Tactic", "Aggressiveness"]]
```

### Firm.make_decision()
```python
def make_decision(
    self, 
    markets: Dict[str, Any], 
    goods_data: list[Dict[str, Any]], 
    market_data: Dict[str, Any], 
    current_time: int, 
    government: Optional[Any] = None
) -> tuple[list[Order], Any]
```

### OrderBookMarket
```python
def place_order(self, order: Order, current_time: int) -> None
def match_orders(self, current_time: int) -> List[Transaction]
def get_all_bids(self, item_id: str) -> List[Order]
def get_all_asks(self, item_id: str) -> List[Order]
def get_best_bid(self, item_id: str) -> Optional[float]
def get_best_ask(self, item_id: str) -> Optional[float]
def get_daily_avg_price(self) -> float
def get_daily_volume(self) -> float
```

### EconomicIndicatorTracker
```python
def track(
    self,
    time: int,
    households: List[Household],
    firms: List[Firm],
    markets: Dict[str, Market],
) -> None

def get_latest_indicators(self) -> Dict[str, Any]
# 반환 필드: unemployment_rate, avg_wage, total_production, 
#           total_consumption, avg_goods_price, food_avg_price, 
#           food_trade_volume, total_household_assets, total_firm_assets
# 주의: "gdp" 필드는 존재하지 않음!
```
