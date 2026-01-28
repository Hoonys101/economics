# W-2 Work Order: Operation Phoenix (Entrepreneurship)

> **Assignee**: Jules  
> **Priority**: P0 (Critical)  
> **Branch**: `feature/entrepreneurship`  
> **Base**: `main`

---

## 📋 Overview

**목표**: 기업 멸종을 막고, 시장의 빈자리를 신규 창업으로 채워 경제를 무한 순환시킨다.

**문제**: 현재 시뮬레이션은 기업이 파산하면 새로운 기업이 생성되지 않아 1000틱 내 전멸함.

**해결**: 부유한 가계가 자본을 투자해 새로운 기업을 설립하는 "창업 메커니즘" 구현.

---

## ✅ Task 1: Add Config Constants

**File**: `config.py`

```python
# ==============================================================================
# Task #9: Entrepreneurship Constants
# ==============================================================================
MIN_FIRMS_THRESHOLD = 5          # 최소 기업 수 (이하로 떨어지면 창업 유도)
STARTUP_COST = 15000.0           # 창업 비용 (가계 현금에서 차감)
ENTREPRENEURSHIP_SPIRIT = 0.05   # 자격 있는 가계의 창업 확률 (5%)
STARTUP_CAPITAL_MULTIPLIER = 1.5 # 창업 자격: cash > STARTUP_COST * 이 값
```

---

## ✅ Task 2: Add `spawn_firm()` in SimulationEngine

**File**: `simulation/engine.py`

```python
def spawn_firm(self, founder_household: "Household") -> Optional["Firm"]:
    """
    부유한 가계가 새로운 기업을 설립합니다.
    
    Args:
        founder_household: 창업주 가계 에이전트
        
    Returns:
        생성된 Firm 객체 또는 None (실패 시)
    """
    startup_cost = getattr(self.config_module, "STARTUP_COST", 15000.0)
    
    # 1. 자본 차감
    if founder_household.cash < startup_cost:
        return None
    founder_household.cash -= startup_cost
    
    # 2. 새 기업 ID 생성
    max_id = max([a.id for a in self.agents], default=0)
    new_firm_id = max_id + 1
    
    # 3. 업종 선택 (부족한 업종 우선)
    specializations = ["basic_food", "clothing", "education_service"]
    # 간단히 랜덤 또는 기업 수가 적은 업종 선택
    import random
    specialization = random.choice(specializations)
    
    # 4. AI 설정
    from simulation.ai.firm_ai import FirmAI
    from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
    
    value_orientation = random.choice([
        self.config_module.VALUE_ORIENTATION_WEALTH_AND_NEEDS,
        self.config_module.VALUE_ORIENTATION_NEEDS_AND_GROWTH,
    ])
    ai_decision_engine = self.ai_manager.get_engine(value_orientation)
    firm_ai = FirmAI(agent_id=str(new_firm_id), ai_decision_engine=ai_decision_engine)
    firm_decision_engine = AIDrivenFirmDecisionEngine(firm_ai, self.config_module, self.logger)
    
    # 5. Firm 생성
    new_firm = Firm(
        id=new_firm_id,
        initial_capital=startup_cost,
        initial_liquidity_need=getattr(self.config_module, "INITIAL_FIRM_LIQUIDITY_NEED_MEAN", 50.0),
        specialization=specialization,
        productivity_factor=random.uniform(8.0, 12.0),
        decision_engine=firm_decision_engine,
        value_orientation=value_orientation,
        config_module=self.config_module,
        logger=self.logger,
    )
    new_firm.founder_id = founder_household.id
    
    # 6. 리스트에 추가
    self.firms.append(new_firm)
    self.agents.append(new_firm)
    
    self.logger.info(
        f"STARTUP | Household {founder_household.id} founded Firm {new_firm_id} "
        f"(Specialization: {specialization}, Capital: {startup_cost})",
        extra={"tick": self.time, "agent_id": new_firm_id, "tags": ["entrepreneurship"]}
    )
    
    return new_firm
```

---

## ✅ Task 3: Add Entrepreneurship Check in `run_tick()`

**File**: `simulation/engine.py` (inside `run_tick()` method)

```python
def _check_entrepreneurship(self):
    """
    매 틱마다 창업 조건을 확인하고 신규 기업을 생성합니다.
    """
    min_firms = getattr(self.config_module, "MIN_FIRMS_THRESHOLD", 5)
    startup_cost = getattr(self.config_module, "STARTUP_COST", 15000.0)
    spirit = getattr(self.config_module, "ENTREPRENEURSHIP_SPIRIT", 0.05)
    capital_multiplier = getattr(self.config_module, "STARTUP_CAPITAL_MULTIPLIER", 1.5)
    
    active_firms_count = sum(1 for f in self.firms if f.is_active)
    
    # Hard Trigger: 기업 수가 최소치 이하
    if active_firms_count < min_firms:
        trigger_probability = 0.5  # 50% 창업 확률 (위기 상황)
    else:
        trigger_probability = spirit  # 일반 창업 확률 (5%)
    
    # 부유한 가계 필터링
    wealthy_households = [
        h for h in self.households 
        if h.is_active and h.cash > startup_cost * capital_multiplier
    ]
    
    import random
    for household in wealthy_households:
        if random.random() < trigger_probability:
            self.spawn_firm(household)
            break  # 한 틱에 하나씩만 창업
```

**Call Site**: `run_tick()` 메서드 내, 기업/가계 행동 처리 후에 호출:
```python
# At end of run_tick(), before saving state:
self._check_entrepreneurship()
```

---

## 📁 Reference Files

- [engine.py](file:///c:/coding/economics/simulation/engine.py) - 수정 대상 (spawn_firm, _check_entrepreneurship)
- [config.py](file:///c:/coding/economics/config.py) - 상수 추가
- [firms.py](file:///c:/coding/economics/simulation/firms.py) - Firm 생성자 참조

---

## 🧪 Verification

1. `python scripts/iron_test.py` 실행
2. 로그에서 `STARTUP |` 메시지 확인 (창업 발생)
3. 1000틱 종료 시 `active_firms > 0` 확인
4. `iron_test_summary.csv`에서 생존자 수 확인

**성공 기준**: 1000틱 종료 시 활성 기업 ≥ 1

---

## ⚠️ Notes

- `spawn_firm()`은 `SimulationEngine` 레벨에서 처리 (Household가 직접 Firm을 생성하면 안 됨)
- 한 틱에 여러 개 창업 가능하나, 초기에는 1개로 제한하여 안정성 확보
- `founder_id`는 향후 배당금/소유권 추적에 사용 가능 (Phase 3 연계)
