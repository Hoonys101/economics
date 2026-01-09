# [To Jules] Phase 17-5: The Leviathan (정부와 정치) 구현 지시

## Context
Phase 17-4(Vanity) 완료 후, Phase 17-5(Leviathan)로 진입합니다.
이 모듈은 여론조사, 선거, 정당 시스템을 통해 정부의 정치적 생존 본능을 구현합니다.

## References
- **상세 설계서**: `design/specs/phase17-5_leviathan_spec.md` (필독)
- **브랜치**: `phase-17-5-leviathan` (신규 생성)

---

## Tasks

### 1. Config 추가
`config.py`에 다음 상수 추가:
```python
# Phase 17-5: The Leviathan
POLL_SAMPLE_RATE = 0.05
POLL_LAG_TICKS = 4        # 여론조사 결과가 정부에 전달되기까지 지연 (틱)
ELECTION_CYCLE_TICKS = 100
DISCONTENT_TOLERANCE = 0.4
STIMULUS_TRIGGER_APPROVAL = 0.4  # 지지율 40% 미만이면 부양책
```

### 2. Government Agent 확장 (`simulation/agents/government.py`)
- `PoliticalParty` Enum 클래스 정의
- `Government` 클래스 확장:
  - 속성: `ruling_party`, `approval_rating`, `poll_history`
  - 메서드: `run_poll(households, tick)`
    - 전체 가구의 5% 샘플링
    - `approval = (satisfied_count / sample_size)`
    - `poll_history`에 저장

### 3. Policy AI (`Government.run_welfare_check` 내 로직 수정)
- **Lagged Feedback**: 의사결정 시 `poll_history[-Poll_Lag]` 사용.
- **Logic**:
  - 지지율 < `STIMULUS_TRIGGER_APPROVAL` 일 때:
    - BLUE 정권: 기업 보조금 지급 (`provide_subsidy` to Firms) - *Hint: Firm agent list passing needed*
    - RED 정권: 가계 복지 확대 (`STIMULUS CHECK`)
  - 지지율 > 0.6 일 때:
    - 긴축 (세율 유지 또는 인상)

### 4. Election System (`simulation/engine.py`)
- `run_tick`에서 `if tick % ELECTION_CYCLE == 0` 체크.
- `_hold_election()` 메서드:
  - 모든 에이전트의 `discontent` 확인 (없으면 `1.0 - social_rank` 등을 대용).
  - 과반수가 행복하지 않으면 정권 교체 (`ruling_party` 변경).
  - 정권 교체 시 로그 출력: `ELECTION_RESULT | Regime Change: BLUE -> RED`

### 5. Verification
- `Python tests/verify_leviathan.py` 작성 및 통과
  - `test_poll_lag`: 지지율 변화가 n틱 뒤에 반영되는지.
  - `test_election_swing`: 불만 세력이 많을 때 정권 바뀌는지.

---

## Constraints
- **Lag Implementation**: 정부는 절대 '현재' 지지율을 알 수 없음. 반드시 과거 데이터를 봐야 함.
- **Refactoring**: 기존 `config.py` 상수들을 적극 활용하되, 이번에 추가되는 정책 로직은 `SimulationConfig`를 사용하는 구조로 짜보는 것을 권장 (선택 사항).

## Deliverables
1. 브랜치 `phase-17-5-leviathan` 생성
2. 위 태스크 구현
3. `tests/verify_leviathan.py` 통과 확인
4. PR 생성 및 보고
