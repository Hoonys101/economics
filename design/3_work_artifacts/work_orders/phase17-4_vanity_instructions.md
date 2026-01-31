# [To Jules] 허영의 사회 & 제어 시스템 구현

## Context
Phase 17-3B 완료. Phase 17-4는 **허영심 모듈**과 **SimulationConfig 제어 시스템**을 통합 구현합니다.

## References
- **상세 설계서**: `design/specs/phase17-4_vanity_spec.md`
- **브랜치**: `phase-17-4-vanity-control` (신규 생성)

---

## Tasks (순서대로 진행)

### Task 1: SimulationConfig 싱글톤 클래스
**파일**: `simulation/simulation_config.py` (신규)

```python
class SimulationConfig:
 _instance = None
 def __new__(cls):
 if cls._instance is None:
 cls._instance = super().__new__(cls)
 # 통화/금융
 cls._instance.base_interest_rate = 0.05
 cls._instance.mortgage_ltv_ratio = 0.8
 cls._instance.enable_mortgage = True
 # 재정/분배
 cls._instance.tax_rate_income = 0.10
 cls._instance.corporate_tax_rate = 0.0
 cls._instance.government_mode = "ACTIVE"
 # 심리/행동
 cls._instance.enable_vanity_system = True
 cls._instance.vanity_weight = 1.0
 cls._instance.mimicry_factor = 0.5
 cls._instance.reference_group_percentile = 0.20
 cls._instance.enable_psychology = True
 return cls._instance
```

### Task 2: Refactoring Pass 1
기존 코드에서 `config.CONSTANT` → `SimulationConfig().property` 변경:
- `simulation/bank.py`: 금리, LTV
- `simulation/agents/government.py`: 세율
- `simulation/engine.py`: 주요 상수들 (점진적)

**가이드라인**: `from simulation.simulation_config import SimulationConfig` 추가

### Task 3: Household 확장 + 랭킹 로직
**파일**: `simulation/core_agents.py`
- `Household.__init__`에 추가:
 - `self.conformity = random.uniform(0.3, 0.8)`
 - `self.social_rank = 0.5`
 - `self.patience = random.uniform(0.3, 0.7)`

**파일**: `simulation/engine.py`
- `run_tick()` 시작부에 `self._update_social_ranks()` 호출
- 설계서 §3.1, §3.2 참조

### Task 4: 유틸리티 함수 개편
**파일**: `simulation/ai/household_ai.py`
```python
cfg = SimulationConfig()
if cfg.enable_vanity_system:
 gap = household.social_rank - cfg.reference_group_percentile
 u_social = gap * household.conformity * cfg.vanity_weight
 total_utility = u_intrinsic + (u_social * 100)
```

### Task 5: 베블런재 + 모방 소비
**파일**: `config.py`
- GOODS에 `is_veblen: bool` 추가 (luxury_food, Tier3 housing 등)

**파일**: `simulation/decisions/housing_manager.py`
- `decide_mimicry_purchase()` 메서드 (설계서 §3.5)

### Task 6: 검증 테스트
**파일**: `tests/verify_vanity_society.py` (신규)
- Unit: `test_social_rank_calculation`, `test_veblen_demand`, `test_mimicry_trigger`
- Integration: `test_vanity_switch_ab` (vanity_weight=0 vs 1.5 비교)

---

## Constraints
- **모든 새 상수는 SimulationConfig 경유**
- **모든 로직에 `if cfg.enable_X:` 가드**
- **기존 테스트 유지**: `verify_real_estate_sales.py` 등 깨지지 않도록

---

## Deliverables
1. 브랜치 `phase-17-4-vanity-control` 생성
2. 6개 태스크 순차 구현
3. `python tests/verify_vanity_society.py` 통과 확인
4. PR 생성 및 보고
