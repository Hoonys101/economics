# 🧪 Test Plan: TP-014 (Phase 14 Integration & Transformation)

**목표**: Phase 14-1(배당)과 Phase 14-2(혁신)가 경제의 "Distribution Trap"을 해결하고 "Structural Transformation"을 달성하는지 단계별로 검증한다.

## 🔍 Test Plan A: "주인의 귀환" (WO-022 검증)
> **Hypothesis**: 기업의 잉여 현금이 배당을 통해 가계로 환류되면, 구매력이 복원되어 200틱 붕괴를 막을 수 있다.

### 1. 환경 설정 (Setup)
- **Modules**: Base Engine + **WO-022 (Dividend)** ON.
- **Innovation**: OFF (모든 신규 창업은 `FOOD` 섹터).
- **Parameters**: 
  - `INCOME_TAX_RATE = 0.0`
  - `FIRM_PRODUCTIVITY_FACTOR = 20.0`
  - `STOCK_MARKET_ENABLED = False` (단, 내부적으로 100% 지분 발행)

### 2. 검증 절차 (Procedures)
1.  **Run Simulation**: 400틱 실행.
2.  **Check Logs**:
    - `DIVIDEND | Firm X -> Household Y : $...` 로그 발생 확인.
3.  **Analyze Data**:
    - **Asset Cross**: `total_capital_income`이 `total_labor_income`과 비등해지거나 역전하는 구간 확인.
    - **Survival**: 200틱(Laissez-Faire 한계점)을 돌파하는가?

### 3. 성공 기준 (Success Criteria)
- [ ] 가계와 기업의 현금이 0이 되지 않고 순환해야 함.
- [ ] "No Jobs"로 인한 아사가 현저히 감소해야 함.

---

## 🚀 Test Plan B: "산업 혁명" (WO-023 검증)
> **Hypothesis**: 구매력이 뒷받침된 상태에서 '새로운 욕구(Consumer Goods)'가 공급되면, 잉여 노동과 자본이 이동하여 1인당 GDP가 급증한다.

### 1. 환경 설정 (Setup)
- **Pre-requisite**: Test Plan A 성공 확인 후 진행.
- **Modules**: Base Engine + WO-022 + **WO-023 (Innovation)** ON.
- **Parameters**:
  - `VISIONARY_ENTREPRENEUR_RATE = 0.05`
  - `TARGET_FOOD_BUFFER_QUANTITY = 5.0`

### 2. 검증 절차 (Procedures)
1.  **Run Simulation**: 1000틱 실행.
2.  **Check Logs**:
    - `STARTUP | Type: CONSUMER_GOODS` (Visionary 진입) 확인.
3.  **Analyze Data**:
    - **Sector Shift**: `manufacturing_employment` (Goods) 비중이 `agriculture_employment` (Food) 비중을 잠식해 들어가는지 확인.
    - **Consumption Shift**: 가계 지출 내역에 `consumer_goods` 구매 기록 확인.

### 3. 성공 기준 (Success Criteria)
- [ ] **Structural Transformation**: 농업 중심 -> 제조업 중심 혹은 균형 성장 확인.
- [ ] **GDP Quantum Jump**: 단순 빵 생산량보다 더 높은 효용/가치 창출 확인.
- [ ] **1000 Ticks Survival**: 영구 존속 경제 달성.
