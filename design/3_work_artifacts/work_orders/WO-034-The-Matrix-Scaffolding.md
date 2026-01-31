# Phase 20 "The Matrix" Scaffolding

## 1. 개요
Phase 20 "The Matrix"의 기초 인프라를 구축합니다. 에이전트의 성별(Gender), 가사 노동의 질(Home Quality), 그리고 장기 계획 엔진(System 2)의 뼈대를 생성하는 것을 목표로 합니다.

## 2. 구현 상세

### 2.1 Config 확장 (config.py)
다음 상수들을 추가하십시오.
- `SYSTEM2_TICKS_PER_CALC`: 10 (System 2 실행 주기)
- `SYSTEM2_HORIZON`: 100 (예측 기간)
- `SYSTEM2_DISCOUNT_RATE`: 0.98 (NPV 할인율)
- `FORMULA_TECH_LEVEL`: 0.0
- `LACTATION_INTENSITY`: 1.0
- `HOMEWORK_QUALITY_COEFF`: 0.5

### 2.2 Household 수정 (simulation/core_agents.py)
- `__init__` 시 에이전트에게 성별(`gender`)을 부여하십시오 (M/F 50:50).
- `home_quality_score` (float, 초기값 1.0) 속성을 추가하십시오.
- `get_agent_data` 메서드가 성별 정보를 포함하도록 업데이트하십시오.

### 2.3 System2Planner 설계 (simulation/ai/system2_planner.py)
`System2Planner`의 `project_future` 로직을 다음과 같이 스캐폴딩하십시오.
1. **Inputs**: `agent_data`, `market_data` (Current Market Price Averages).
2. **Logic**:
 - `Daily_Net_CashFlow = (Expected_Wage * 8) - (Average_Price * Survival_Threshold)`.
 - `Future_Wealth(t) = Current_Wealth + (Daily_Net_CashFlow * t)`.
 - `Survival_Check(t)`: `Future_Wealth(t) < 0` 이면 사망(Dead)으로 간주.
3. **NPV Calculation**:
 - `NPV_Wealth = Sum over t [ Future_Wealth(t) * (SYSTEM2_DISCOUNT_RATE ^ t) ]`.
4. **Output**: `NPV_Wealth`, `Estimated_Bankruptcy_Tick`.

## 3. 검증 계획
- `tests/test_phase20_scaffolding.py`를 생성하여 Household의 성별 부여와 `home_quality_score` 초기화 여부를 확인하십시오.

## 4. 인사이트 보고 요청
`reports/PHASE20_SCAFFOLDING_REPORT.md`에 다음 사항을 기록하십시오:
- 성별 도입이 초기 인구 구성에 미치는 영향.
- System 2의 선형 예측 로직이 에이전트의 '미래 불안감'을 어떻게 표현할 수 있을지에 대한 아이디어.
