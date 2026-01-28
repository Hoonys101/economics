# Phase 17-5: The Leviathan - Specification

## 1. 개요 (Overview)
본 단계는 경제 시뮬레이션에 **정치적 피드백 루프**를 도입합니다.
에이전트들의 경제적 상태(Utility/Discontent)가 투표와 지지율로 표출되고, 정부는 이를 바탕으로 정책(세금, 복지)을 변경하며 생존을 도모합니다. 핵심은 **지연된 피드백(Delayed Feedback)**으로 인한 정부의 실패 가능성 구현입니다.

## 2. 데이터 구조 및 인터페이스 (Data & Interfaces)

### 2.1 Government Agent 확장 (`simulation/agents/government.py`)
기존 `Government` 클래스에 정치적 상태를 추가합니다.

```python
class PoliticalParty(Enum):
    BLUE_GROWTH = "Growth Party"   # 기업 친화, 저세율, 선별 복지
    RED_EQUALITY = "Equality Party" # 노동 친화, 고세율, 보편 복지

class Government(Agent):
    def __init__(self, ...):
        # ... existing ...
        self.ruling_party: PoliticalParty = PoliticalParty.BLUE_GROWTH
        self.approval_rating: float = 0.5
        self.poll_history: List[float] = []
        self.election_tick: int = 100 # 주기적 선거 (예: 100틱마다)
        self.consecutive_terms: int = 0
```

### 2.2 Config 추가 (`config.py` / `SimulationConfig`)
```python
# Phase 17-5: The Leviathan
POLL_SAMPLE_RATE = 0.05       # 인구의 5% 여론조사
POLL_LAG_TICKS = 4            # 여론 반영 지연 시간
ELECTION_CYCLE_TICKS = 100    # 선거 주기
DISCONTENT_TOLERANCE = 0.4    # 불만 임계치 (넘으면 야당 투표)
```

## 3. 핵심 로직 (Core Logic)

### 3.1 The Sensor: 여론조사 (Opinion Polls)
매 틱 실행되지만, 정부는 `POLL_LAG_TICKS` 이전의 데이터를 봅니다.

1. **Sampling**: 전체 `Households` 중 5% 랜덤 추출.
2. **Evaluation**:
   - `Utility`가 지난 틱 대비 증가했는가?
   - `Discontent` (1 - normalized_utility)가 낮은가?
3. **Approva Rating**:
   - 만족하는 에이전트 비율 = `Approval Rating`.
   - `poll_history`에 저장.
4. **Perception Lag**:
   - 정부 AI가 의사결정에 사용하는 값은 `poll_history[-lag]` 입니다.

### 3.2 The Actuator: 정책 및 예산 (Policy AI)
정부 AI(`GovernmentAI`)는 지지율 방어를 최우선 목표로 합니다.

**Decision Logic:**
```python
current_approval = self.get_lagged_approval()

if current_approval < 0.4:  # 위기 상황
    if self.ruling_party == BLUE:
        # 경기 부양 (Stimulus)
        action = "STIMULUS_CHECK" # 기업 보조금 or 세금 감면
    else: # RED
        # 복지 확대 (Welfare)
        action = "WELFARE_EXPANSION" # 현금 살포
elif current_approval > 0.6: # 안정 상황
    # 재정 건전성 확보
    action = "AUSTERITY" # 증세 or 지출 축소
```

**Party Differentiator:**
- **Blue Party**: 법인세 인하 선호, 기업 R&D 보조금 지급.
- **Red Party**: 소득세 인상(상류층), 실업 급여/기본소득 확대.

### 3.3 The Judge: 선거 (Election)
`ELECTION_CYCLE_TICKS` 마다 실행.

**Retrospective Voting Model:**
- 각 에이전트는 "지난 20틱 동안 내 삶이 나아졌는가?"를 판단.
- `mean(recent_utilities) < threshold` OR `discontent > tolerance` -> **심판(Opposition)**.
- 그렇지 않으면 -> **유지(Incumbent)**.

**Outcome:**
- 과반 득표 시 집권당 유지. 실패 시 정권 교체.
- 정권 교체 시:
  - `ruling_party` 변경.
  - 전 정권의 정책 기조 초기화 (급격한 정책 선회 시뮬레이션).

## 4. 검증 계획 (Verification)

### 4.1 Unit Tests (`tests/verify_leviathan.py`)
- `test_poll_lag`: 여론조사 데이터가 지정된 틱만큼 지연되어 반영되는지 확인.
- `test_election_swing`: 불만도가 높을 때 정권 교체가 일어나는지 확인.
- `test_party_policy_diff`: 정당에 따라 다른 정책(세율 등)이 적용되는지 확인.

### 4.2 Scenario Test
- **"The Angry Voter" Scenario**:
  - 강제로 에이전트들의 유틸리티를 낮춤 (세금 폭탄 등).
  - 다음 선거에서 정권이 교체되는지 관찰.
  - 새 정권이 복지/부양책을 쓰는지 확인.

## 5. File Changes
- `[MODIFY] config.py`: 상수 추가
- `[MODIFY] simulation/agents/government.py`: 정당, 여론조사 속성 및 메서드 추가
- `[MODIFY] simulation/ai/government_ai.py` (New/Modify): 정책 결정 AI 로직 확장
- `[MODIFY] simulation/engine.py`: `run_tick`에 선거 스케줄러 추가
- `[NEW] tests/verify_leviathan.py`: 검증 테스트
