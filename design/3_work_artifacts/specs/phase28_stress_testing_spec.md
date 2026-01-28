# 상세 명세서: Phase 28 - 거시 경제 안정성 스트레스 테스트

## 1. 개요

- **목표**: God Class 리팩토링 이후의 아키텍처를 준수하며, 시스템에 3가지 핵심 거시 경제 스트레스 시나리오(초인플레이션, 디플레이션, 공급 충격)를 도입합니다.
- **범위**: `StressScenarioConfig` DTO를 정의하고, `EventSystem`, `CommerceSystem` 및 에이전트(`Household`, `Firm`) 내부에 시나리오별 행동 로직을 구현합니다.

## 2. 아키텍처 원칙 (Pre-flight Audit 기반)

이 구현은 감사 보고서에서 식별된 위험을 완화하기 위해 다음 제약 조건을 엄격히 준수합니다.

- **[C-1] 트리거는 `EventSystem`으로 중앙화**: 모든 시나리오의 시작(자산 충격, 생산성 저하 등)은 `EventSystem.execute_scheduled_events` 내에서만 처리됩니다. `Simulation.run_tick`에 `if self.time == X`와 같은 조건문을 추가하는 것은 금지됩니다.
- **[C-2] `StressScenarioConfig` DTO의 명시적 전달**: `StressScenarioConfig` DTO는 `Simulation`에서 생성되어, `EventSystem`, `CommerceSystem` 등 영향을 받는 모든 하위 시스템과 `agent.make_decision` 메서드에 명시적으로 전달되어야 합니다.
- **[C-3] 책임 분리 원칙 준수**:
    - **`EventSystem`**: 충격 **개시** 책임 (예: 모든 가계 자산을 일회성으로 변경).
    - **`Agent` (`make_decision`)**: 시나리오 파라미터에 기반한 **의도 형성** 책임 (예: 사재기를 위한 `BUY` 주문 생성).
    - **`CommerceSystem`**: 에이전트로부터 분리된 **행동 실행** 책임 (예: 최종 소비량에 `consumption_pessimism_factor` 적용).
- **[C-4] 범위 확정 (Scope Containment)**: "공급 충격" 시나리오의 '투입물 대체(Input Substitution)' 로직 구현은 복잡한 리팩토링을 요구하므로 **이번 Phase의 범위에서 제외**합니다.

## 3. API 명세 (`simulation/dtos/scenario.py`)

`StressScenarioConfig` DTO는 모든 시나리오 파라미터를 포함하는 단일 객체로, 시뮬레이션 초기화 시 생성되어 각 시스템과 에이전트에 전달됩니다.

## 4. 시나리오별 구현 계획

### 4.1. 시나리오 1: 초인플레이션 (Hyperinflation)

- **트리거 (수요 견인)**:
    - **Injection Point**: `EventSystem.execute_scheduled_events`
    - **로직**: `config.scenario_name == 'hyperinflation'`이고 `time == config.start_tick`일 때, `context.households`를 순회하며 `h.assets *= (1 + config.demand_shock_cash_injection)`을 적용합니다.
- **핵심 행동 (인플레이션 기대 가속)**:
    - **Injection Point**: `Household.update_perceived_prices`
    - **로직**: 기존 적응 기대(adaptive expectation) 계산에서 `self.adaptation_rate`를 `self.adaptation_rate * scenario_config.inflation_expectation_multiplier`로 대체하여 기대 인플레이션의 변화 속도를 높입니다.
- **핵심 행동 (사재기)**:
    - **Injection Point**: `Household.make_decision` (정확히는 `AIDrivenHouseholdDecisionEngine` 내부)
    - **로직**: 의사결정 로직에서 `expected_inflation`이 특정 임계값 이상일 때, `basic_food`와 같은 생필품의 `BUY` 주문 수량을 `1 + scenario_config.hoarding_propensity_factor` 만큼 증폭시킵니다.

### 4.2. 시나리오 2: 디플레이션 악순환 (Deflationary Spiral)

- **트리거 (자산 충격)**:
    - **Injection Point**: `EventSystem.execute_scheduled_events`
    - **로직**: `config.scenario_name == 'deflation'`이고 `time == config.start_tick`일 때, `context.households`와 `context.firms`를 순회하며 `agent.assets *= (1 - config.asset_shock_reduction)`을 적용합니다.
- **핵심 행동 (패닉 셀링)**:
    - **Injection Point**: `Household.make_decision`
    - **로직**: `scenario_config.panic_selling_enabled`가 `True`이고, 가계의 자산이 특정 임계값 미만일 때, 포트폴리오의 주식(`stock_{firm_id}`)에 대한 `SELL` 주문을 생성합니다.
- **핵심 행동 (소비 붕괴)**:
    - **Injection Point**: `CommerceSystem.execute_consumption_and_leisure`
    - **로직**: `breeding_planner`가 반환한 소비량(`consume_list`)을 가계에 실제 적용하기 직전, `household.is_employed == False`이면 최종 소비량을 `c_amt * (1 - scenario_config.consumption_pessimism_factor)`로 감소시킵니다.
- **핵심 행동 (부채 회피)**:
    - **Injection Point**: `Household.make_decision`
    - **로직**: `REPAYMENT` 주문을 생성하는 로직의 예산 할당량을 `scenario_config.debt_aversion_multiplier` 만큼 증폭시켜 다른 소비/투자보다 우선적으로 처리되도록 합니다.

### 4.3. 시나리오 3: 공급 충격 (Supply Shock)

- **트리거 (생산성 충격)**:
    - **Injection Point**: `EventSystem.execute_scheduled_events`
    - **로직**: `config.scenario_name == 'supply_shock'`이고 `time == config.start_tick`일 때, `context.firms`를 순회하며 `scenario_config.exogenous_productivity_shock` 맵에 해당하는 기업(예: `firm.type == 'Farm'`)의 `firm.productivity_factor`를 수정합니다.
- **핵심 행동 (투입물 대체)**:
    - **상태**: **범위 외 (Out of Scope)**. 현재 로직을 유지합니다.

## 5. 수정될 코드 구조 (Pseudo-code)

### `Simulation.run_tick`
```python
def run_tick(self, ...):
    # ...
    # StressScenarioConfig는 __init__에서 생성되어 self.stress_scenario_config에 저장됨
    
    # 1. EventSystem에 DTO 전달
    if self.event_system and self.stress_scenario_config.is_active:
         context: EventContext = {...}
         self.event_system.execute_scheduled_events(self.time, context, self.stress_scenario_config)
    
    # ... (중략) ...

    # 2. Agent.make_decision에 DTO 전달
    for household in self.households:
        household.make_decision(..., stress_scenario_config=self.stress_scenario_config)

    # ... (중략) ...

    # 3. CommerceSystem에 DTO 전달
    if self.commerce_system:
        commerce_context: CommerceContext = {...}
        self.commerce_system.execute_consumption_and_leisure(commerce_context, self.stress_scenario_config)
    
    # ...
```

## 6. 검증 계획

1.  **단위 테스트**: `EventSystem`과 `CommerceSystem`의 시나리오 로직에 대한 단위 테스트를 작성합니다. (`test_event_system.py`, `test_commerce_system.py`)
    - 예: `EventSystem`에 하이퍼인플레이션 설정을 전달하고, `execute_scheduled_events` 호출 후 가계 자산이 올바르게 증가했는지 검증합니다.
2.  **통합 테스트**: `test_engine.py`에 시나리오별 테스트 케이스를 추가합니다.
    - 예: 디플레이션 시나리오를 활성화하고 100틱을 실행한 후, 실업률과 기업 파산 수가 기준 시뮬레이션보다 높게 나타나는지 검증합니다.

## 7. 🚨 Risk & Impact Audit (회귀 위험 분석)

- **위험**: `Simulation.run_tick`에 직접적인 조건문을 추가하여 `EventSystem`의 역할을 무시할 위험.
- **완화**: 본 명세서는 모든 트리거를 `EventSystem`에 위임하도록 강제하여 `run_tick`의 단일 책임 원칙을 보존하고 회귀를 방지합니다.
- **위험**: `consumption_pessimism_factor`와 같은 로직을 에이전트의 `make_decision`에 잘못 구현하여 `CommerceSystem`의 책임을 침해할 위험.
- **완화**: 본 명세서는 소비 실행 단계인 `CommerceSystem`에 해당 로직을 명확히 할당하여 아키텍처 일관성을 유지합니다.

## 8. JULES 구현 지침

- **Routine**: 구현 중 발견되는 모든 기술 부채나 설계 개선 아이디어는 `communications/insights/` 폴더에 `[Insight] <주제>.md` 형식으로 기록 및 보고해야 합니다.
