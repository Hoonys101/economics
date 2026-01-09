# [To Jules] Phase 17-4: 허영심 시스템 구현 지시

## Context
Phase 17-3B(부동산/모기지) 완료 후, Phase 17-4(허영의 사회)로 진입합니다.
이 모듈은 에이전트에게 "상대적 박탈감"을 부여하여 비합리적 소비를 유도합니다.

## References
- **상세 설계서**: `design/specs/phase17-4_vanity_spec.md` (필독)
- **브랜치**: `phase-17-4-vanity` (신규 생성)

---

## Tasks

### 1. `config.py` Feature Flags 추가
```python
# --- Phase 17-4: Vanity System ---
ENABLE_VANITY_SYSTEM = True
VANITY_WEIGHT = 1.0
MIMICRY_FACTOR = 0.5
REFERENCE_GROUP_PERCENTILE = 0.20

ENABLE_PSYCHOLOGY = True
GOVERNMENT_MODE = "ACTIVE"
ENABLE_MORTGAGE = True
```

GOODS 딕셔너리에 `is_veblen: bool` 속성 추가 (기존: False, luxury_bag 등: True)

### 2. `simulation/core_agents.py` 확장
- `Household.__init__`에 추가:
  - `self.conformity = random.uniform(0.3, 0.8)` (성격 기반)
  - `self.social_rank = 0.5` (초기값)

### 3. `simulation/engine.py` 랭킹 로직
- `run_tick()` 시작부에 `self._update_social_ranks()` 호출
- 새 메서드 `_update_social_ranks()`: 설계서 §3.1 참조
- 새 메서드 `_calculate_reference_standard()`: 설계서 §3.2 참조

### 4. `simulation/decisions/housing_manager.py` 모방 소비
- `decide_mimicry_purchase()` 메서드 추가: 설계서 §3.5 참조
- `should_buy()` 내부에서 호출

### 5. `simulation/ai/household_ai.py` 유틸리티 개편
- `calculate_total_utility()` 또는 관련 보상 함수에 Social Component 반영
- 가드: `if not config.ENABLE_VANITY_SYSTEM: return U_intrinsic`

### 6. `tests/verify_vanity_society.py` 작성
- Unit: `test_social_rank_calculation`, `test_veblen_demand`, `test_mimicry_trigger`
- Integration: `test_rat_race_scenario` (100틱 후 저축률<0, 불행 에이전트 50%+)

---

## Constraints
- **Soft Coding**: 모든 수치는 `config` 변수 참조
- **Feature Flag Guard**: 모든 새 로직은 `if config.ENABLE_X:` 로 감쌀 것
- **기존 테스트 유지**: 기존 테스트(`verify_real_estate_sales.py` 등)가 깨지지 않도록 주의

---

## Deliverables
1. 브랜치 `phase-17-4-vanity` 생성
2. 위 6개 태스크 구현
3. `python tests/verify_vanity_society.py` 통과 확인
4. PR 생성 및 보고
