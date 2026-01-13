# WO-054: Malthusian Trap Verification (Pre-Modern Baseline)

## 1. Objective
현대 자본주의적 성장(Phase 22)을 분석하기 전에, 기술 혁신(하버-보슈법 등)이 없는 상태에서 인류가 겪었던 **'멜서스 트랩(Malthusian Trap)'**을 시뮬레이션으로 재현합니다. 인구가 증가함에 따라 노동의 한계 생산성이 체감하고, 결국 임금이 최저 생계비 이하로 떨어져 기아로 인한 인구 감소가 발생하는 '철의 천장(Iron Ceiling)'을 확인하는 것이 목적입니다.

## 2. Technical Requirements (Pre-Modern Config)
Jules는 다음 설정을 적용하여 시뮬레이션을 수행해야 합니다.

### A. Fixed Land Assets (Capital as Land)
- **Mechanism**: `capital_stock`의 증가를 차단하여 이를 '유한한 토지'로 취급합니다.
- **Config**: 
    - `CAPITAL_DEPRECIATION_RATE = 0.0` (토지는 닳지 않음)
    - `CorporateManager._manage_capital_expenditure`를 비활성화하거나, 기업의 자본 구매 예산을 0으로 고정.
    - `INITIAL_FIRM_CAPITAL_MEAN = 100.0` (고정된 토지량)

### B. Tech Stagnation (No Haber-Bosch)
- **Mechanism**: 기술 발전에 의한 생산성 향상을 차단합니다.
- **Config**:
    - `FIRM_PRODUCTIVITY_FACTOR`를 상수로 고정 (10.0 ~ 20.0).
    - `INFRASTRUCTURE_TFP_BOOST = 0.0`
    - `RND_WAGE_PREMIUM` 비활성화.

### C. No Survival Safety Net & Primitive Breeding
- **Mechanism**: 국가의 보조금이 생태적 경쟁을 방해하지 않도록 하며, 인구는 소득에 따라 본능적으로 증가합니다.
- **Config**:
    - `UNEMPLOYMENT_BENEFIT_RATIO = 0.0`
    - `GOVERNMENT_STIMULUS_ENABLED = False`
    - `SURVIVAL_NEED_DEATH_THRESHOLD = 100.0` (God Mode 해제 - 굶으면 죽음)
    - `TECH_CONTRACEPTION_ENABLED = False` (System 1: 본능적 번식)
    - `BIOLOGICAL_FERTILITY_RATE = 0.2` (높은 출산율 유도)

### D. Firm Stability in Stagnation
- **Mechanism**: 기술이 정체된 경제에서 기업이 임대료나 고정비 때문에 조기 파산하지 않도록 합니다.
- **Config**:
    - `FIRM_MAINTENANCE_FEE = 0.0`
    - `INTEREST_RATE = 0.0` (금융 시스템 배제)
    - `DIVIDEND_RATE = 0.0` (이익 유보)

## 3. Verification Metrics
시뮬레이션 결과 리포트(`reports/malthusian_trap_report.md`)에 포함되어야 할 항목:
1. **Inverse Correlation**: 인구($L$) 증가 시 평균 임금($W$)의 하락 그래프.
2. **Iron Ceiling Population**: 인구가 수렴하거나 진동하는 임계치(Threshold) 확인.
3. **Malthusian Catastrophe**: 임금이 `Survival_Cost` 미만으로 떨어지는 시점의 사망률 급증 현상.
4. **Subsistence Equilibrium**: 인구가 기하급수적으로 늘다가 식량 공급의 한계(산술급수적 혹은 정체)에 부딪혀 꺾이는 **'철의 천장'** 시각화.

## 4. Implementation Steps for Jules
1. `malthusian_trap_baseline.py` 실험 스크립트 작성.
2. 위 기술 사양(Fixed Land, No Welfare)을 강제 적용.
3. 500틱 시뮬레이션 실행 후 ASCII Plot으로 인구/임금 상관관계 출력.
