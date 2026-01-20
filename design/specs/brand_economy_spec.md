# W-1 Specification: Phase 6 - The Brand Economy (Final Technical Spec)

**작성자**: Antigravity (Second Architect)
**승인**: Architect Prime
**목표**: 가격 중심의 완전경쟁시장에서 '브랜드 가치'와 '품질 선호도'가 반영된 독점적 경쟁시장으로의 진화.

---

## 1. 데이터 모델 변경 (Data Model Updates)

### 1.1 `simulation/models.py`
- **Order (Class)**:
    - `target_agent_id: Optional[int] = None` 필드 추가.
    - 특정 판매자를 지정하여 구매 점수가 가장 높은 오퍼와 직접 매칭되도록 지원.

### 1.2 `simulation/firms.py`
- **Attributes**:
    - `brand_value: float` (0.0 ~ 100.0, 기본값 0.0)
    - `marketing_budget_rate: float` (잉여 현금 중 마케팅에 투자할 비율, 기본값 0.05)
- **Logic**:
    - `on_tick()` 또는 `produce()` 전후에 `brand_value` 감쇄(`BRAND_DECAY`) 및 마케팅 투자에 따른 상승분 반영.

### 1.3 `simulation/core_agents.py` (Household)
- **Attributes**:
    - `quality_preference: float` (0.0 ~ 1.0)
    - 초기화 시 자산 수준에 비례하여 설정 (상위 20%는 고품질 선호, 하위는 가성비 선호).

---

## 2. 핵심 알고리즘: Utility Scoring 매칭

### 2.1 효용 점수 공식 (The Formula)
가계 에이전트는 시장의 모든 매도 주문(Asks)에 대해 아래 공식을 통해 점수를 계산합니다.
$$Score = \frac{BaseUtility \times (1 + \alpha \times Brand \times Pref)}{Price}$$
- $\alpha$: 브랜드 가치 가중치 상수 (Config: `BRAND_UTILITY_ALPHA = 0.01`)
- $Brand$: 판매 기업의 `brand_value`
- $Pref$: 가계의 `quality_preference`

### 2.2 가계 구매 로직 (`HouseholdAI`)
1.  `market.get_all_asks(item_id)`를 통해 모든 매도 주문을 샘플링합니다.
2.  각 주문에 대해 위 공식을 적용하여 최고 점수를 가진 `seller_id`를 선정합니다.
3.  구매 주문(`Order`) 생성 시 `target_agent_id = best_seller_id`를 설정하여 제출합니다.

### 2.3 시장 매칭 로직 (`OrderBookMarket`)
1.  **Targeted Pass**: `buy_order.target_agent_id`가 설정된 주문을 우선 처리합니다.
    - 해당 `target_agent_id`를 가진 판매자의 주문이 존재하고 가격 조건이 맞으면 매칭.
2.  **Global Pass**: 남은 주문들에 대해 기존의 가격 우선 매칭(Greedy)을 수행합니다.

---

## 3. 설정 상수 (Config Update)
- `MARKETING_EFFICIENCY = 0.5` (1원당 브랜드 상승량)
- `BRAND_DECAY = 0.02` (틱당 2% 자연 감소)
- `BRAND_UTILITY_ALPHA = 0.01` (브랜드 효과 반영 계수)

---

## 4. Zero-Question Verification
- 가계의 자산이 많을수록 브랜드 브랜드 가치가 높은 상품을 구매하는 경향이 있는가?
- 마케팅 투자를 지속하는 기업이 프리미엄 가격을 유지하면서도 점유율을 방어하는가?
- 시장 매칭 시 `target_agent_id`가 있는 주문이 실제 지정된 판매자와 체결되는가?
