# W-2 Work Order: Phase 6 - The Brand Economy Implementation

**목표**: 브랜드 가치와 가계 성향이 반영된 '점수 기반 매칭' 시스템 구현.

## 1단계: 데이터 모델 확장 (models.py, firms.py, core_agents.py)
1.  **`simulation/models.py`**: `Order` 클래스에 `target_agent_id: Optional[int] = None` 필드를 추가하십시오.
2.  **`simulation/firms.py`**: 
    - `brand_value` (float), `marketing_budget_rate` (float) 필드를 추가하십시오.
    - `on_tick()` 시점에 `BRAND_DECAY`를 적용하고, 마케팅 예산을 지출하여 `brand_value`를 높이는 `_update_brand_equity()` 메서드를 구현하십시오.
3.  **`simulation/core_agents.py`**:
    - `Household` 에이전트에 `quality_preference` 필드를 추가하십시오.
    - 초기화 시 가계의 자산(Assets) 수준에 따라 0.0 ~ 1.0 사이의 값을 할당하십시오.

## 2단계: 유틸리티 스코어링 로직 (household_ai.py)
1.  **`simulation/ai/household_ai.py`**:
    - `get_best_utility_offer()` 메서드를 구현하십시오.
    - 시장의 모든 Asks를 순회하며 $Score = \frac{U \times (1 + 0.01 \times Brand \times Pref)}{Price}$ 공식을 적용하여 최고 점수 판매자를 찾으십시오.
2.  구매 주문 생성 시 `target_agent_id`를 위에서 찾은 판매자 ID로 설정하십시오.

## 3단계: 시장 매칭 엔진 고도화 (order_book_market.py)
1.  **`simulation/markets/order_book_market.py`**:
    - `_match_orders_for_item` 내부에 `Targeted Matching` 로직을 추가하십시오.
    - `buy_order.target_agent_id`가 있는 경우, 해당 판매자의 주문을 `sell_orders` 리스트에서 먼저 찾아 매칭을 시도하십시오.
    - 가격 조건(Buy Price >= Sell Price)이 충족되는지 확인하십시오.

## 4단계: 상수 설정 (config.py)
- 아래 상수를 추가하십시오.
    - `MARKETING_EFFICIENCY = 0.5`
    - `BRAND_DECAY = 0.02`
    - `BRAND_UTILITY_ALPHA = 0.01`
