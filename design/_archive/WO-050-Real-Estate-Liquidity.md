# Work Order: WO-050-Real-Estate-Liquidity

**Date:** 2026-01-11
**Phase:** Phase 22 (The Awakening) - Step 4 (Liquidity)
**Assignee:** Jules (Worker AI)
**Objective:** 가계(Household)가 보유한 부동산을 시장에 매도(Sell)하여 현금 유동성을 확보하는 로직을 구현한다.

## 1. Problem Statement
현재 `Household` 에이전트는 주택을 "살(Buy)" 수는 있지만, "팔(Sell)" 수는 없다.
이로 인해 다음과 같은 문제가 발생한다:
1.  **House Poor**: 현금은 없는데 집만 깔고 앉아 굶어 죽는(Starvation) 현상.
2.  **Market Stagnation**: 매물이 공급되지 않아(신규 분양 제외) 부동산 거래 절벽 발생.
3.  **No Moving**: 더 좋은 집으로 이사하거나, 싼 집으로 다운사이징할 수 없음.

## 2. System Architecture (System 2 Extension)

`HouseholdSystem2Planner`에 `decide_selling()` 로직을 추가한다.

### 2.1 Selling Triggers (매도 조건)

가계는 다음 두 가지 상황에서 매도를 고려한다.

1.  **Distress Sale (생존형 급매)**
    *   **Condition**: `Cash < Monthly_Survival_Cost * 2` (2달 치 식비도 없음).
    *   **Action**: 즉시 시장가(Market Price)보다 약간 낮게(95-98%) 매도 주문.
    *   **Priority**: Critical.

2.  **Profit Taking / Adjustment (차익 실현/조정)**
    *   **Condition**: `Current_Price > Purchase_Price * (1 + Expected_Return)` AND `Market_Trend == "PEAK"`.
    *   **System 2 Check**: "지금 팔고 전세(Rent)로 가는 것이 NPV상 이득인가?"
    *   **Action**: 시장가(Market Price) 또는 호가(Ask)로 주문.

## 3. Implementation Logic

### Module: `simulation/ai/household_system2.py` (`HouseholdSystem2Planner`)

1.  **`decide_selling()`**:
    *   현재 보유 주택 확인 (`agent.owned_properties`).
    *   Trigger 조건 검사 (Distress Sale vs Profit Taking).
    *   매도 결정 시 `agent.housing_target_mode = "SELL"` 또는 필요한 상태 값 반환.

### Module: `simulation/systems/housing_system.py` (Transaction Handler)

매매 체결 시 (`PersistenceManager` 또는 `Simulation` 호출에 의해 `process_transaction` 실행), 다음 절차를 원자적으로 수행해야 한다.

1.  **Ownership Transfer**: `Unit.owner_id` 변경 (Seller -> Buyer).
2.  **Cash Transfer**: Buyer Cash -> Seller Cash.
3.  **Occupancy Handling (거주자 처리)**:
    *   **Seller (구 집주인)**:
        *   만약 팔린 주택이 `residing_property_id`였다면, 해당 속성을 `None`으로 변경.
        *   **Grace Period (유예 기간)**: `agent.housing_grace_period = 2` (틱 단위) 설정.
        *   유예 기간 동안은 `apply_homeless_penalty`에서 제외됨.

## 4. Verification Plan (Test Cases)

1.  **Distress Test**: 현금을 강제로 0으로 만든 후, 보유 주택을 매물로 내놓는지 확인.
2.  **Transaction Test**: 매수자가 나타났을 때 소유권 이전 및 현금 입금 확인.
3.  **Homeless Loop**: 집을 판 후, 판 돈으로 전세를 구하거나 싼 집을 사는지 확인(Cycle Completion).

## 5. Constraint
*   **1가구 1주택**: 현재 시뮬레이션은 다주택 투자를 제한적으로만 허용하므로, 자가 주택 매도 시 "거주지 불명" 상태 처리에 유의할 것.

## 6. Risk Mitigation (Architect Prime Review)
> **"Rich Homeless" 시나리오 방지**
> 집을 팔아 현금은 풍부하지만, 다음 틱에 전세/매물을 구하지 못해 노숙 상태로 사망하는 경우.

*   **Solution: Temporary Housing Buffer**
    *   매도 체결 시, 에이전트는 `is_in_temporary_housing = True` 상태가 되어 2틱(Grace Period) 동안 Survival 패널티를 받지 않음.
    *   Grace Period 동안 새 집(Buy)이나 전세(Rent)를 구해야 함.
    *   2틱 후에도 거처를 구하지 못하면 `is_homeless = True`로 전환되고 정상 패널티 적용.

## 7. Technical Clarifications for Jules (Architect Prime Guidance)

1.  **Entry Price Tracking**: 
    - `simulation/models.py`의 `RealEstateUnit` 클래스에 `last_purchase_price: float = 0.0` 필드를 추가한다. (수석 승인)
    - `HousingSystem.process_transaction`에서 소유권 이전 시 해당 필드를 `tx.price`로 업데이트한다.
  
2.  **Distress Sale Threshold**: 
    - `Distress` 상태는 `agent.assets < (current_monthly_survival_cost * 1.5)`로 정의한다. (약 1.5개월분 생존 비용 미만 시)
    - `current_monthly_survival_cost`는 `config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK * market_food_price * 30` (월간 추정치)으로 산출한다.

3.  **Selling Price Strategy**:
    - **Distress Sale**: `unit.estimated_value * 0.95` (급매, 5% 할인).
    - **Profit Taking**: `unit.estimated_value * 1.05` (차익 실현, 5% 프리미엄).

4.  **Grace Period**:
    - `Household` 클래스에 `housing_grace_period: int = 0` 필드를 추가한다. (승인)

5.  **Logging & Testing**:
    - `iron_test.py`의 핵심 로직을 건드리지 말고, `HousingSystem`과 `HouseholdSystem2Planner`에서 `logger.info`를 통해 "DISTRESS_SELL", "PROFIT_SELL", "GRACE_PERIOD_ACTIVE" 등의 로그를 상세히 남겨 기록으로 검증하라.

