# DEBUG_MARKET_REPORT

## 1. 조사 개요
**Work Order:**
**목표:** 시장 거래 정체 및 가계 멸종 원인 추적
**수행 일시:** 2026-01-06 (Simulation Time)
**도구:** `scripts/iron_test.py` (10 Ticks)

## 2. 단계별 조사 결과

### Step 1: 주문 생성 (Order Generation)
- **결과:** 정상 확인.
- **근거:**
 - `DEBUG_WO14 | Firm {id} Orders: {N}` 로그가 정상 출력됨.
 - `DEBUG_WO14 | Household {id} Orders: {N}` 로그가 정상 출력됨.
 - 가계와 기업 모두 매 틱마다 활발하게 주문을 생성하고 있음.

### Step 2: 시장 진입 (Market Entry)
- **결과:** 정상 확인.
- **근거:**
 - `Placing order: ...` 로그가 모든 주문에 대해 출력됨.
 - `DEBUG_WO14 | Matching {item}: Buys={N}, Sells={M}` 로그에서 매수/매도 주문이 호가창에 등록된 것을 확인 (예: `Buys=20, Sells=2`).

### Step 3: 매칭 로직 (Matching Logic) - **결함 발견**
- **현상:**
 - `MATCHED_TARGETED` 로그는 다수 발생함 (예: `MATCHED_TARGETED | 3.00 of basic_food...`).
 - 그러나 일반 상품(goods)에 대해 **`MATCHED_GENERAL` 로그가 전무함.**
 - 노동 시장(labor)은 `MATCHED_GENERAL`이 정상 발생함.
 - `Comparing: Buy ... vs Sell ...` 로그(일반 매칭 루프 내부)가 상품 시장에서는 전혀 출력되지 않음.
- **원인 분석 (Root Cause):**
 - `simulation/markets/order_book_market.py`의 `_match_orders_for_item` 메서드에서 **Targeted Order(지정가/지정대상 주문)의 Fallback 로직 부재.**
 - 코드는 `targeted_buys`와 `general_buys`를 분리하여 처리함.
 - `targeted_buys` 중 매칭에 실패한 주문들(`remaining_targeted_buys`)은 **일반 매칭 풀(`general_buys`)로 재진입하지 않음.**
 - 즉, 가계가 특정 브랜드(기업)를 선호하여 타겟팅했으나, 해당 기업이 재고가 없거나 가격이 비싸 거래가 성사되지 않을 경우, 가계는 시장에 다른 저렴한 물건이 있어도 구매를 시도조차 하지 않고 굶게 됨.
 - 이는 "브랜드 충성도로 인한 아사(Starvation by Brand Loyalty)" 현상을 유발함.

### Step 4: 가계 상태 (Agent Lifecycle)
- **관찰:** 10 틱 테스트에서는 100% 생존했으나, 이는 초기 자산($20,000)이 많고 과잉 공급(Firms dumping inventory)으로 인한 디플레이션 덕분임.
- **위험:** 장기 시뮬레이션에서 특정 선호 기업이 파산하거나 물량이 부족해지면, 해당 기업을 타겟팅한 가계들은 Fallback 없이 구매에 실패하여 `survival_need`가 급증, 결국 멸종하게 됨.

## 3. 해결 방안 (Fix Proposal)

### 수정 대상
`simulation/markets/order_book_market.py`: `_match_orders_for_item` 메서드

### 수정 로직
Targeted Matching 루프 종료 후, 남은 타겟 주문들(`remaining_targeted_buys`)을 일반 매칭 풀(`general_buys`)에 병합하고 재정렬(가격 내림차순)하여 General Matching 루프를 실행하도록 변경.

```python
# Fallback Logic Insertion
if remaining_targeted_buys:
 general_buys.extend(remaining_targeted_buys)
 general_buys.sort(key=lambda o: o.price, reverse=True)
```

이 수정은 브랜드 선호가 있는 가계도 1차 시도 실패 시 시장가(또는 최선가)로 다른 기업의 물건을 구매할 수 있게 하여 시장 유동성을 공급하고 생존율을 높일 것임.