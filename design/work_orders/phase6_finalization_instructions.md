# W-2 Work Order: Phase 6 Finalization

> **Assignee**: Jules
> **Priority**: High
> **Branch**: `phase6-brand-finalization`
> **Base**: `main`

---

## 📋 Overview

Phase 6 Brand Economy의 핵심 로직은 구현 완료되었으나, **자동화 및 AI 통합**이 필요합니다.
본 작업 완료 후, AI가 브랜드 투자를 학습할 수 있는 환경이 갖춰집니다.

---

## ✅ Task 1: `Firm.post_ask()` 메서드 구현 (Auto-Injection)

### Target File
`simulation/firms.py`

### Objective
Firm이 판매 주문 생성 시, `BrandManager`의 데이터를 자동으로 주입하도록 래퍼 메서드 구현.

### Implementation Spec

```python
def post_ask(self, item_id: str, price: float, quantity: float, market: "OrderBookMarket", current_tick: int) -> Order:
    """
    판매 주문을 생성하고 시장에 제출합니다.
    Brand Metadata를 자동으로 주입합니다.
    """
    # 1. 브랜드 정보 스냅샷
    brand_snapshot = {
        "brand_awareness": self.brand_manager.brand_awareness,
        "perceived_quality": self.brand_manager.perceived_quality,
    }

    # 2. 주문 생성 (brand_info 자동 주입)
    order = Order(
        agent_id=self.id,
        order_type="SELL",
        item_id=item_id,
        quantity=quantity,
        price=price,
        market_id=market.id,
        brand_info=brand_snapshot  # <-- Critical Injection
    )

    # 3. 시장에 제출
    market.place_order(order, current_tick)

    self.logger.debug(
        f"FIRM_POST_ASK | Firm {self.id} posted SELL order for {quantity:.1f} {item_id} @ {price:.2f} with brand_info",
        extra={"agent_id": self.id, "tick": current_tick, "brand_awareness": brand_snapshot["brand_awareness"]}
    )

    return order
```

### Integration Point
`DecisionEngine` 또는 기존 주문 생성 로직에서 `firm.post_ask()`를 호출하도록 수정해야 합니다.

**Search for**: `Order(` ... `order_type="SELL"` in `simulation/decisions/` 디렉토리
**Replace with**: `firm.post_ask()` 호출

---

## ✅ Task 2: AI Reward 함수 수정 (Brand Valuation)

### Target File
`simulation/ai/firm_ai.py`

### Objective
보상 함수에 **브랜드 자산 가치 변동분**을 반영하여, AI가 마케팅 투자를 긍정적으로 학습하도록 유도.

### The Formula
```
Reward = CashFlow + (Δ BrandAwareness × Assets × 0.05)
```

### Implementation Spec

#### Step 1: `Firm` 에이전트에 `prev_awareness` 속성 추가

**File**: `simulation/firms.py` (`Firm.__init__`)

```python
# In Firm.__init__, after brand_manager initialization:
self.prev_awareness: float = 0.0  # For AI Reward Calculation
```

#### Step 2: `FirmAI.calculate_reward` 수정

**File**: `simulation/ai/firm_ai.py`

```python
def calculate_reward(self, firm_agent: "Firm", prev_state: Dict, current_state: Dict) -> float:
    """
    Reward = Financial Performance + Brand Asset Valuation
    """
    # 1. 재무적 성과 (기존 로직 유지)
    profit = current_state.get("net_income", 0.0)

    # 2. 비재무적 성과: 브랜드 자산 가치 변동
    current_awareness = firm_agent.brand_manager.brand_awareness
    prev_awareness = firm_agent.prev_awareness

    delta_awareness = current_awareness - prev_awareness
    brand_valuation = delta_awareness * firm_agent.assets * 0.05  # 5% of Assets

    # 3. 통합 보상
    total_reward = profit + brand_valuation

    # 4. 상태 갱신 (Firm Body에 저장)
    firm_agent.prev_awareness = current_awareness

    self.logger.debug(
        f"FIRM_AI_REWARD | Firm {firm_agent.id}: Profit={profit:.2f}, ΔAwareness={delta_awareness:.4f}, BrandValue={brand_valuation:.2f}, TotalReward={total_reward:.2f}",
        extra={"agent_id": firm_agent.id}
    )

    return total_reward
```

### Configuration
`config.py`에 이미 추가된 `AI_VALUATION_MULTIPLIER = 1000.0`은 **사용하지 않습니다**.
대신 **상대 가치 공식** (`assets * 0.05`)을 사용합니다.

---

## ✅ Task 3: Visualization Data Logging

### Target File
`simulation/firms.py` (`Firm.update_needs` 또는 새 메서드)

### Objective
대시보드 분석을 위해 `brand_premium` 지표를 로그에 기록.

### Implementation Spec

```python
def calculate_brand_premium(self, market_data: Dict[str, Any]) -> float:
    """
    브랜드 프리미엄 = 내 판매가격 - 시장 평균가격
    """
    item_id = self.specialization
    market_avg_key = f"{item_id}_avg_traded_price"

    market_avg_price = market_data.get("goods_market", {}).get(market_avg_key, 0.0)

    # 내 최근 판매가 (last_prices에서 조회)
    my_price = self.last_prices.get(item_id, market_avg_price)

    if market_avg_price > 0:
        brand_premium = my_price - market_avg_price
    else:
        brand_premium = 0.0

    return brand_premium
```

### Logging Point
`Firm.update_needs()` 마지막에 추가:

```python
# At end of update_needs(), before final log:
brand_premium = self.calculate_brand_premium(market_data) if market_data else 0.0
self.logger.info(
    f"FIRM_BRAND_METRICS | Firm {self.id}: Awareness={self.brand_manager.brand_awareness:.4f}, "
    f"Quality={self.brand_manager.perceived_quality:.4f}, Premium={brand_premium:.2f}",
    extra={
        **log_extra,
        "brand_awareness": self.brand_manager.brand_awareness,
        "perceived_quality": self.brand_manager.perceived_quality,
        "brand_premium": brand_premium
    }
)
```

---

## 📁 Reference Files

| File | Purpose |
|------|---------|
| [phase6_brand_economy_spec.md](file:///c:/coding/economics/design/specs/phase6_brand_economy_spec.md) | 원본 설계 명세 |
| [brand_manager.py](file:///c:/coding/economics/simulation/brands/brand_manager.py) | 브랜드 로직 구현체 |
| [firms.py](file:///c:/coding/economics/simulation/firms.py) | Firm 에이전트 (수정 대상) |
| [firm_ai.py](file:///c:/coding/economics/simulation/ai/firm_ai.py) | AI 보상 함수 (수정 대상) |

---

## 🧪 Verification

작업 완료 후 다음을 확인하십시오:

1. **Unit Test**: `verify_brand_economy.py` 실행 시 PASS
2. **Integration**: 10틱 시뮬레이션 실행 후 로그에서 `FIRM_BRAND_METRICS` 확인
3. **AI Learning**: 마케팅 지출 증가 시 `TotalReward` 감소하지 않는지 확인

---

## ⚠️ Notes

- `config.AI_VALUATION_MULTIPLIER`는 **deprecated** 처리 (주석 추가)
- 기존 `Order` 생성 로직을 `post_ask()`로 점진적 마이그레이션
- PR 제목: `feat(brand): Auto-inject brand metadata & AI reward valuation`
