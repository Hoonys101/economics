# 📋 Work Order: WO-Diag-005-Genesis (The Ignition)

## 🎯 Goal
정부 보조금 없이도 경제가 자생할 수 있도록 **시장 유연성(가격 및 임금 하향 조정)을 대폭 강화**하고, 초기 자본을 통한 **점화 에너지**를 주입한다.

## 🛠️ Tasks

### 1. 기업: 재고 기반 공격적 투매 (Fire-Sale Logic)
- **Target**: `simulation/decisions/standalone_rule_based_firm_engine.py`
- **Logic**: `_adjust_price_based_on_inventory` 메서드 수정.
    - 현재는 `diff_ratio`에 따라 선형적으로 조정함.
    - **수정**: `config.GENESIS_PRICE_ADJUSTMENT_MULTIPLIER`를 사용하여 가격 인하 속도를 **2배** 가속하라.
    - 재고가 `OVERSTOCK_THRESHOLD`를 크게 초과할 경우(예: 2배 이상), 가격을 기존 로직보다 더 파격적으로(최대 50% 할인) 낮추는 'Emergency Sale' 조건을 추가하라.

### 2. 가계: 생존 기반 임금 투항 (Wage Surrender)
- **Target**: `simulation/decisions/rule_based_household_engine.py` (또는 해당 로직 위치)
- **Logic**: 가계의 희망 임금(`reservation_wage`) 조정 로직 수정.
    - **수정**: 가계가 실직 상태이며 `survival_need`가 고통 수준(`SURVIVAL_NEED_THRESHOLD` 이상)일 때, `config.GENESIS_WAGE_FLEXIBILITY_FACTOR`를 적용하여 **희망 임금을 이전보다 2배 더 공격적으로 낮추게** 하라.
    - 최소 생존 비용만 보장된다면 최저 임금(`BASE_WAGE`) 미만으로라도 노동을 공급하도록 유도하라.

### 3. 검증: 1000틱 자생력 정찰
- **Script**: `python scripts/recon_normal_1000.py 5.0 1.0` 실행 (Stimulus=False 필수)
- **Verification**: 
    - 1000틱 동안 대규모 아사(Type A) 없이 경제 순환이 유지되는가?
    - 재고가 쌓일 때 가격이 즉각 하락하고, 실직자가 속출할 때 낮은 임금으로라도 재고용이 일어나는가?

## 📂 Referenced Specs
- [implementation_plan.md](file:///C:/Users/Gram%20Pro/.gemini/antigravity/brain/5aad18a3-c16e-456e-8a9d-ea97b4edfa53/implementation_plan.md)
- `config.py` (Genesis 파라미터 추가됨)
