# W-1 Specification: Brand Value & Product Quality (Task #7)

**모듈**: Task #7 - Differentiation Strategy  
**상태**: 🟡 Drafting (설계 진행 중)  
**작성자**: Architect (Antigravity)  
**대상 파일**: `config.py`, `simulation/firms.py`, `simulation/core_agents.py`, `simulation/ai/household_ai.py`

---

## 1. 개요 (Overview)
시장 경쟁을 단순 가격 경쟁에서 **"가격 vs 품질(브랜드)"**의 2차원 경쟁으로 확장한다.
기업은 마케팅/품질 투자를 통해 `brand_value`를 높여 **프리미엄 가격**을 받을 수 있고, 가계는 소득 수준이나 성향에 따라 **가심비(가격 대비 품질/만족도)** 소비를 한다.

---

## 2. 아키텍처 및 데이터 모델

### 2.1 Firm (Supplier)
*   **속성 추가**:
    *   `brand_value` (float): 현재 브랜드/품질 인지도. (0.0 ~ 100.0)
    *   `marketing_budget` (float): 이번 틱에 할당된 마케팅 예산.
*   **매커니즘**:
    *   **투자**: 자본을 투입하여 `brand_value`를 상승시킴.
    *   **감가상각**: 매 틱마다 일정 비율(`BRAND_DECAY_RATE`)로 자연 감소.
    *   **효과**: 동일 제품이라도 `brand_value`가 높으면 가계의 효용(Utility) 계산 시 보너스를 부여.

### 2.2 Household (Consumer)
*   **속성 추가**:
    *   `quality_preference` (float): 품질 민감도. (0.0 ~ 1.0)
        *   높을수록: 비싸도 브랜드 높은 제품 선호 (Luxury/Brand loyals).
        *   낮을수록: 가격 중심 소비 (Price sensitive).
*   **소비 결정 로직 변경**:
    *   기존: `Utility = Good_Utility * Quantity`
    *   변경: `Utility = (Good_Utility * (1 + Brand_Value * Quality_Preference)) * Quantity`

### 2.3 Goods Configuration
*   **적용 대상**: 모든 소비재 (`basic_food`는 효과 미미, `luxury_food`, `clothing` 등재 효과 큼). `config.py`의 `GOODS` 정의에 `brand_coefficient` 추가.

---

## 3. 세부 구현 명세

### 3.1 Config 추가 (`config.py`)
```python
# --- Brand & Quality ---
BRAND_DECAY_RATE = 0.05         # 틱당 브랜드 가치 감소율 (5%)
MARKETING_EFFICIENCY = 0.1      # 마케팅 비용 1단위당 브랜드 상승량
MAX_BRAND_VALUE = 50.0          # 브랜드 가치 상한선

# Household Preference
INITIAL_QUALITY_PREFERENCE_MEAN = 0.3
INITIAL_QUALITY_PREFERENCE_RANGE = 0.2
```

### 3.2 Firm Logic (`simulation/firms.py`)
*   **`__init__`**: `self.brand_value = 0.0` 초기화.
*   **`invest_in_marketing(amount)`**:
    ```python
    def invest_in_marketing(self, amount: float):
        self.assets -= amount
        gain = amount * self.config.MARKETING_EFFICIENCY
        self.brand_value = min(self.config.MAX_BRAND_VALUE, self.brand_value + gain)
    ```
*   **`update_brand()`** (매 틱 호출):
    ```python
    def update_brand(self):
        self.brand_value *= (1 - self.config.BRAND_DECAY_RATE)
    ```

### 3.3 Market & Matching Logic (Crucial Change)

**문제**: 기존 Order Book은 가격 우선 원칙이므로, 소비자가 비싼 브랜드 제품을 사려고 해도 싼 제품이 먼저 매칭됨.
**해결**: **`Targeted Order`** 시스템 도입.

1.  **DTO 변경 (`simulation/models.py` or `dtos.py`)**:
    *   `Order` 클래스에 `target_agent_id: Optional[int] = None` 필드 추가.
2.  **Market Logic Change (`order_book_market.py`)**:
    *   `match_orders` 루프 내에서 조건 추가:
        ```python
        # In matching loop
        if buy_order.target_agent_id is not None:
             if sell_order.agent_id != buy_order.target_agent_id:
                 continue # Skip mismatch
        ```
    *   이렇게 하면 소비자가 특정 기업의 제품을 "지목"해서 구매 가능.

### 3.4 Household Decision Logic (`household_ai.py` / `rule_based...`)

*   **쇼핑 프로세스 변경**:
    1.  **Scan**: `market.get_all_asks(item_id)`를 통해 현재 나와있는 매도 주문들을 **전수 조회**.
    2.  **Score**: 각 매도 주문(Selling Offer)에 대해 점수 계산.
        *   `Score = (Base_Utility * (1 + Firm_Brand * My_Pref)) / Price`
        *   Firm_Brand는 `firm.brand_value`를 참조 (AgentState 등 활용).
    3.  **Select**: 점수가 가장 높은 주문의 `agent_id`를 `target_agent_id`로 설정하여 Buy Order 제출.
    4.  **Fallback**: 만약 `target_agent_id`를 지정하지 않으면(또는 브랜드가 중요하지 않으면), 기존처럼 `None`으로 설정하여 최저가 매칭.

### 3.5 Firm Logic update
*   **Production**: 기존과 동일 (Generic Item 생산/판매).
*   **Brand**: 마케팅 투자 액션 수행 시 `self.brand_value` 상승.

---

## 4. 데이터베이스 변경 (`schema.py`)

```sql
-- Firms 테이블 (또는 AgentState)
ALTER TABLE agent_states ADD COLUMN brand_value REAL DEFAULT 0.0;
```

---

## 5. 검증 계획 (Verification)
1.  **브랜드 성장 테스트**: 마케팅 예산을 쓴 기업의 브랜드 가치가 오르는지 확인.
2.  **선호도 테스트**: `quality_preference`가 높은 가계가 브랜드 가치가 높은(그러나 가격도 조금 비싼) 상품을 선택하는지 확인.
3.  **쇠퇴 테스트**: 투자를 멈추면 브랜드 가치가 하락하는지 확인.

---

## 6. 작업 체크리스트
- [ ] `config.py` 상수 추가
- [ ] `Firm` 클래스에 브랜드 로직(`invest`, `decay`) 추가
- [ ] `Household` 클래스에 `quality_preference` 속성 추가
- [ ] **핵심**: `market_mechanics` 또는 `household_decision`에서 매물 선택(Selection) 로직에 브랜드 가중치 반영.
- [ ] DB 스키마 업데이트
