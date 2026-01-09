# [To Jules] Phase 19: Population Dynamics (진화적 인구 역학) 구현 지시

## Context
Phase 17-5(정부)까지 완료되어 정치/경제 시스템이 갖춰졌습니다.
이제 마지막 퍼즐인 **[Phase 19: 인구 역학]**을 구현합니다.
기존의 단순 비용 계산이 아닌, **'시간 빈곤'**, **'기대 불일치'**, **'r/K 선택'**이 복합적으로 작용하는 '진화적 인구 모델'을 구축해야 합니다.

## References
- **상세 설계서**: `design/specs/phase19_population_dynamics_spec.md` (필독)
- **브랜치**: `phase-19-population` (신규 생성)

---

## Tasks

### 1. Config 추가
`config.py`에 다음 상수 추가:
```python
# Phase 19: Population Dynamics
REPRODUCTION_AGE_START = 20
REPRODUCTION_AGE_END = 45
CHILDCARE_TIME_REQUIRED = 8.0  # 자녀 1명당 하루 필요 시간
HOUSEWORK_BASE_HOURS = 2.0     # 가구 기본 가사 시간
EDUCATION_COST_MULTIPLIERS = { # 교육 수준별 기대 임금 배수
    0: 1.0, 1: 1.5, 2: 2.2, 3: 3.5, 4: 5.0, 5: 8.0
}
SOCIAL_CAPILLARITY_COST = 0.5  # 계층 이동 비용 (K-Factor)
UNNAMED_CHILD_MORTALITY_RATE = 0.001 # 기본 사망률
```

### 2. Household Agent 확장 (`simulation/core_agents.py`)
- **Attributes**:
  - `age` (int): 틱 단위 또는 연 단위 관리.
  - `education_level` (int): 0~5.
  - `children` (List[int]): 자녀 ID 리스트.
  - `expected_wage` (float): 교육 수준에 따른 기대치.
  - `time_budget` (Dict): `labor`, `leisure`, `childcare`, `housework`.

### 3. Demographic Manager (`simulation/systems/demographic_manager.py`)
전체 인구를 관리하는 시스템 에이전트(싱글톤/매니저) 구현.
- `process_aging(agents)`: 나이 증가. `REPRODUCTION_AGE_END` 지나면 번식 불가.
- `process_births(agents)`: 번식 결정 로직에 따라 새 에이전트 생성.
  - 부모의 형질(Talent) 일부 유전 + 돌연변이.
  - 초기 자산은 부모 자산의 일부 이전.

### 4. Evolutionary Decision Logic (`simulation/ai/household_ai.py` or new engine)
`decide_reproduction` 메서드 구현:
1.  **Biological Constraint**: 나이 체크.
2.  **Time Constraint**: `24h - Labor - Housework > Childcare_Needed`?
    - 고소득자는 Labor 줄이는 기회비용이 커서 여기서 탈락하기 쉬움.
3.  **Expectation Constraint**: `Current_Utility > Reservation_Utility`?
    - `Reservation_Utility`는 `Expected_Wage`에 비례.
    - 고학력자는 기대치가 높아 '불만' 상태일 확률 높음 -> 출산 포기.
4.  **Strategy Selection (r/K Check)**:
    - 빈곤층인데 불확실성 높음 -> **r-Strategy** (무식하게 낳음).
    - 중산층이상인데 경쟁 치열 -> **K-Strategy** (신중하게 낳거나 포기).

### 5. Verification
`tests/verify_population_dynamics.py`:
- `test_time_constraint`: 노동 시간이 12시간인 에이전트가 "시간이 없어" 출산 포기하는지.
- `test_expectation_mismatch`: 소득은 같지만 학력이 높은 에이전트가 "눈이 높아" 출산 포기하는지.
- `test_baby_boom`: 저학력/고성장 시나리오에서 출산율 폭발하는지.

---

## Deliverables
1. 브랜치 `phase-19-population` 생성
2. 위 태스크 구현
3. `tests/verify_population_dynamics.py` 통과 확인
4. PR 생성 및 보고
