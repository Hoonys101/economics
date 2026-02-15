# PHASE 20: SCAFFOLDING REPORT

## 1. 개요
Phase 20 "The Matrix"의 기초 인프라(Scaffolding) 구축이 완료되었습니다.
본 보고서는 구현된 시스템 2(System 2)의 동작 원리와 성별 인구 통계의 초기 분포, 그리고 향후 예측 로직의 확장 가능성에 대한 인사이트를 담고 있습니다.

## 2. 구현 사항 요약
- **Config 확장**: System 2 구동을 위한 상수 (`SYSTEM2_TICKS_PER_CALC`, `HORIZON`, `DISCOUNT_RATE`) 및 인구 역학 상수(`FORMULA_TECH_LEVEL` 등)가 추가되었습니다.
- **Household 인프라**:
    - `gender` 속성 추가 (초기화 시 50:50 확률적 배분 검증 완료).
    - `home_quality_score` 속성 추가 (기본값 1.0).
    - `System2Planner` 인스턴스 내장.
- **System 2 Planner**:
    - **Forward Projection**: 현재 자산, 기대 임금, 시장 생존 비용(식비)을 기반으로 미래 100틱(Horizon)의 자산 흐름을 예측.
    - **NPV Calculation**: 미래 자산 가치를 `0.98` 할인율로 환산하여 현재 의사결정의 가치 척도 제공.
    - **Bankruptcy Detection**: 선형 예측 상 자산이 고갈되는 시점(Tick)을 탐지하여 "Survival Mode" 발동의 근거 마련.

## 3. 검증 결과 (Insights)

### 3.1 성별 인구 구성 (Gender Distribution)
`tests/test_phase20_scaffolding.py` 실행 결과, 100명의 에이전트 생성 시 `M: 47`, `F: 53` (실행 마다 변동) 등으로 이상적인 50:50 분포에 근접함을 확인하였습니다. 이는 향후 `Lactation Dependency` 및 `Marriage Market` 구현 시 안정적인 짝짓기 풀(Matching Pool)을 보장합니다.

### 3.2 System 2 예측 로직 (Future Projection)
- **Positive Flow**: 임금이 생존 비용을 상회할 경우, NPV는 초기 자산보다 높게 산출되며 `Estimated_Bankruptcy_Tick`은 -1(Safe)로 반환됨을 확인했습니다. 이는 에이전트가 "투자 모드"로 전환할 수 있는 심리적 여유를 수치화합니다.
- **Negative Flow**: 임금이 없거나 생존 비용이 과다할 경우, 자산 고갈 시점(Bankruptcy Tick)이 정확히 예측되었습니다. (예: 자산 100, 순손실 -20/tick -> 6틱 째 파산 예측).
    - **인사이트**: 단순 선형 예측임에도 불구하고, 에이전트에게 "미래의 공포"를 주입하는 메커니즘으로 충분히 작동합니다. System 1(RL)은 현재 보상에 집중하지만, System 2는 이 `Bankruptcy Tick` 정보를 통해 "지금 굶더라도 저축해야 한다"는 장기적 제약을 RL Reward에 Penalty로 주입할 수 있습니다.

## 4. 향후 제언 (Next Steps)
1. **불확실성 반영**: 현재 System 2는 결정론적(Deterministic) 선형 예측을 수행합니다. 추후 `market_volatility`를 반영하여 미래 자산의 신뢰 구간(Confidence Interval)을 계산하면 에이전트의 'Risk Aversion' 성향을 더 정교하게 모델링할 수 있습니다.
2. **가사 노동과 시간 배분**: 현재 `home_quality_score`는 1.0으로 고정되어 있으나, 이를 유지하기 위해 System 2가 '노동 시간'을 줄이고 '가사 시간'을 늘리도록 계획하는 `Time Allocation Solver`가 필요합니다.
3. **NPV의 활용**: 산출된 NPV 값을 에이전트의 `Social Rank` 계산이나 `Marriage Market`의 배우자 가치 평가(Mate Value)에 통합하여, "미래가 유망한 배우자"를 선호하는 현상을 구현할 수 있습니다.
