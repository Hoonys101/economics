# WO-067: High-Fidelity Reaction Test (Sensory System Verification)

## 1. 개요 (Overview)
- **목표**: WO-066에서 구현된 '감각 시스템(Sensory System)'이 외부 경제 충격(Inflation Shock)을 즉각적으로 인지하고, 2 Ticks 이내에 정책 대응(Hawkish Action)을 수행하는지 검증합니다.
- **담당자**: Jules (Implementer)
- **유형**: Verification Script (`scripts/verify_policy_reaction.py`)

## 2. 테스트 시나리오 (Test Scenario)

### 2.1 초기 설정 (Setup)
- **Config Overrides**:
    - `GOVERNMENT_POLICY_MODE`: `"AI_ADAPTIVE"` (Smart Leviathan 활성화)
    - `GOV_ACTION_INTERVAL`: `1` (즉각적인 반응 테스트를 위해 쿨타임 해제)
    - `CB_INFLATION_TARGET`: `0.02` (2%)
- **Target Agents**: Government(SmartLeviathan), CentralBank.

### 2.2 실행 절차 (Execution Steps)

1.  **Phase 1: Burn-in (Tick 0 ~ 99)**
    - 일반적인 경제 시뮬레이션을 진행하여 초기 데이터를 안정화합니다.
    - `Government.sensory_data`가 정상적으로 갱신되는지 확인합니다.

2.  **Phase 2: The Shock (Tick 100)**
    - **Action**: `Government.update_sensory_data()` 호출 시, 강제적으로 조작된 `GovernmentStateDTO`를 주입합니다.
    - **Injected Data**:
        - `inflation_sma`: `0.15` (15% Hyper-inflation warning)
        - `gdp_growth_sma`: `0.03` (Normal)
        - `unemployment_sma`: `0.04` (Full employment)
    - **Logging**: "TEST_SHOCK_INJECTED | Inflation set to 15%" 로그 출력.

3.  **Phase 3: Reaction (Tick 101)**
    - 시뮬레이션 1 Tick 진행 (`government.make_policy_decision` 호출).
    - **Verification Points**:
        - **인지(Perception)**: `Government` 에이전트 내부의 `sensory_data.inflation_sma`가 0.15로 유지되고 있는가?
        - **판단(Decision)**: `SmartLeviathanPolicy`가 `ACTION_HAWKISH` (긴축)를 선택했는가?
        - **행동(Action)**: `CentralBank.base_rate`가 이전 Tick 대비 상승(`+0.0025` 이상)했는가?

## 3. 검증 스크립트 명세 (`scripts/verify_policy_reaction.py`)

### 3.1 Pseudo-code
```python
def verify_reaction():
    # 1. Setup Engine & Config
    config = load_config()
    config.GOV_ACTION_INTERVAL = 1  # Critical Override
    engine = Engine(config)
    
    # 2. Burn-in
    for _ in range(100):
        engine.step()
        
    # 3. Capture State Before Shock
    gov = engine.agents["government"]
    cb = engine.agents["central_bank"]
    rate_before = cb.base_rate
    
    # 4. Inject Shock (Override Sensory Data)
    shock_dto = GovernmentStateDTO(
        tick=100,
        inflation_sma=0.15,  # SHOCK!
        gdp_growth_sma=0.03,
        unemployment_sma=0.04,
        approval_sma=0.5,
        current_gdp=10000.0,
        budget_balance=0.0
    )
    gov.update_sensory_data(shock_dto)
    
    # 5. Step (Reaction)
    engine.step() # Tick 101
    
    # 6. Validate
    rate_after = cb.base_rate
    
    if rate_after > rate_before:
        print(f"PASS: Interest Rate Increased. {rate_before} -> {rate_after}")
        return True
    else:
        print(f"FAIL: Rate unchanged or dropped. {rate_before} -> {rate_after}")
        return False
```

## 4. 예외 처리 및 주의사항
- **쿨타임 간섭**: `GOV_ACTION_INTERVAL`이 1이 아닌 경우 테스트는 무조건 실패하므로, Config 강제 덮어쓰기가 필수적입니다.
