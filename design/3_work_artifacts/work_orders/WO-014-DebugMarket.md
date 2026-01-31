# 시장 매칭 실패 및 가계 멸종 원인 정밀 조사

## 1. 개요
현재 Phase 4.5 통합 테스트 중, 가계가 식량을 사려는 의사결정을 내림에도 불구하고 시장에서 실제 거래(`MATCHED`)가 단 한 건도 발생하지 않고 가계가 대거 멸종하는 현상이 발생함.

## 2. 조사 대상 및 순서 (Step-by-Step)

### Step 1: 주문 생성 및 전송 확인 (Source to Engine)
- **파일**: `simulation/engine.py`
- **작업**:
 - `household.make_decision` 호출 직후 `len(household_orders)`를 출력하는 로그 추가.
 - `firm.make_decision` 호출 직후 `len(firm_orders)`를 출력하는 로그 추가.
- **목표**: 엔진이 에이전트로부터 주문서를 정상적으로 수령하는지 확인.

### Step 2: 시장 객체 내부 유입 확인 (Engine to Market)
- **파일**: `simulation/markets/order_book_market.py`
- **작업**:
 - `place_order` 메서드 내의 `self.logger.debug` 로그를 `self.logger.info`로 상향 조정.
- **목표**: `engine.py`가 호출한 `place_order`가 시장 객체의 `self.buy_orders` / `self.sell_orders`에 실제로 데이터를 수집하는지 확인.

### Step 3: 매칭 로직 진입 및 결함 확인 (Matching Logic)
- **파일**: `simulation/markets/order_book_market.py`
- **작업**:
 - `_match_orders_for_item` 함수 최상단에 `item_id`, `len(b_orders)`, `len(s_orders)`를 출력하는 로그 추가.
 - 만약 두 리스트가 충분한데도 매칭이 안 된다면, 가격 비교 구문(`b_order.price >= s_order.price`) 전후의 값을 로그로 찍어 비교.
- **목표**: 매칭이 안 되는 결정적인 '논리적 벽'을 발견.

### Step 4: 가계 사망 원인 분석 (Lifecycle)
- **파일**: `simulation/engine.py`
- **작업**:
 - `_handle_agent_lifecycle` 메서드에서 에이전트가 처리되는 시점에 `survival_need`, `assets` 상태를 짧게 로깅.
- **목표**: 거래 실패가 직접적인 사인인지, 아니면 다른 예기치 못한 비용(세금, 이자 등)이 원인인지 확인.

## 3. 보고 양식
조사 완료 후 `reports/DEBUG_MARKET_REPORT.md` 파일을 생성하여 위 4단계별 발견 사항과 해결책(Fix)을 제안할 것.
