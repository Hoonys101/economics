# 📨 To: Jules Monitor (Debug Request)

수석 아키텍트(Architect Prime)의 Sensor Repair 지침에 따라, `GovernmentAI`가 의사결정을 내리는 시점의 `market_data` 정합성을 검증하고 수정하기 위한 디버깅 요청서입니다.

---

## 🐞 Debug Request: Government AI Sensory Synchronization

**Priority:** HIGH
**Target:** `simulation/engine.py`, `simulation/ai/government_ai.py`

### 1. 문제 정의 (Problem Statement)
현재 `GovernmentAI`가 `decide_policy`와 `calculate_reward`를 수행할 때 사용하는 `market_data` 스냅샷이 **최신 틱(Tick T)의 경제 상황을 반영하지 못하고 과거(Tick T-1) 데이터이거나, 필수 키값이 누락**되어 있을 가능성이 높습니다.

*   **원인 추정:** `Simulation.run_tick()` 내에서 `self.tracker.track()`(지표 업데이트)은 틱의 **가장 마지막**에 실행되지만, `government.make_policy_decision()`은 그보다 앞서 실행됩니다.
*   **증상:** `_prepare_market_data()`가 호출될 때 `tracker.get_latest_indicators()`는 아직 이번 틱의 실업률, GDP 등을 집계하지 못한 상태입니다. 이로 인해 AI가 `unemployment_rate: 0.0` 또는 오래된 데이터를 보고 학습하게 됩니다.

### 2. 진단 지침 (Diagnosis Instructions)

Jules Monitor는 다음 순서로 코드를 검증하고 수정하십시오.

1.  **데이터 시점 확인 (`simulation/engine.py`)**:
    *   Line 380 부근: `self.government.make_policy_decision(market_data, self.time)` 호출 시점의 `market_data` 내용을 덤프하십시오.
    *   특히 `market_data["unemployment_rate"]`와 `market_data["total_production"]` 값이 이번 틱의 예상치와 맞는지, 아니면 이전 틱 값인지 확인하십시오.

2.  **Sensory Module 정합성 확인**:
    *   Line 360 부근: `WO-057-B Sensory Module`은 별도로 계산된 `latest_indicators`를 사용합니다.
    *   `GovernmentAI`가 사용하는 `market_data`와 `Sensory Module`이 사용하는 데이터 소스가 일치하는지(Single Source of Truth) 확인하십시오.

### 3. 수정 목표 (Resolution Goals)

*   **Option A (동기화)**: `make_policy_decision` 호출 전에 최소한의 핵심 거시 지표(실업률, 물가 등)를 임시 집계하여 `market_data`에 주입(Inject) 하십시오.
*   **Option B (명시적 Lag)**: 만약 T-1 데이터를 보고 결정하는 것이 의도라면, `GovernmentAI` 코드 내에서 `unemployment` 등이 `0.0`으로 잡히지 않도록 Fallback 로직을 강화하십시오. (**Architect 권장: Option A에 가깝게, Sensory Module의 계산 값을 market_data에도 동기화할 것**)

### 4. 실행 명령 (Action)

```bash
# 1. 현재 데이터 흐름을 추적하기 위한 로그 추가 및 드라이런
python scripts/gemini_worker.py debug "Check market_data content inside run_tick before gov decision" --target simulation/engine.py
```

**[참조: 관련 코드 스니펫]**
*   `simulation/engine.py`: `_prepare_market_data` 메서드의 데이터 소스 (`tracker.get_latest_indicators`)
*   `simulation/ai/government_ai.py`: `_get_state` 메서드 내 `market_data.get(...)` 호출부
