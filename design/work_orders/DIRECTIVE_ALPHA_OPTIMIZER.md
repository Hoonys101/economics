# 🏎️ [Directive] Jules-Alpha: Optimizer

## 1. 🛑 Goal
시뮬레이션 연산 속도를 획기적으로 향상시켜 1,000틱 완주 시간을 3분 이내로 단축하십시오.

## 2. 🧱 Technical Task (Zero-Question Spec)

### A. I/O Optimization (The DB Bottleneck)
- **Target File**: `simulation/engine.py` (line ~77)
- **Action**: `self.batch_save_interval` 변수의 할당값을 `50`으로 강제(Hardcode/Config Override)하십시오.
- **Goal**: 매 틱 발생하는 DB Flush 부하를 1/50로 제거합니다.

### B. UI/Terminal Optimization (Log Suppression)
- **Target File**: `scripts/experiments/dynasty_report.py` (또는 실험 메인 스크립트)
- **Action**: 
    1. 스크립트 최상단에 `logging.getLogger("simulation").setLevel(logging.WARNING)` 추가.
    2. `logging.getLogger("simulation.engine").setLevel(logging.WARNING)` 추가.
- **Goal**: 매 틱 수천 줄씩 발생하는 `INFO` 로그를 Mute 하여 터미널 I/O를 절약합니다.

### C. Implementation: Vectorized Consumption (Logic Booster)
- **Target File**: `simulation/ai/vectorized_planner.py`
- **Action**: `decide_consumption_batch(agents, market_data)` 메서드를 **실제로 구현**하십시오.
    - **Logic Map**:
        1. 각 에이전트의 `inventory`, `assets`, `needs["survival"]`을 NumPy Array로 추출.
        2. `market_data`에서 상품 가격 배열 생성.
        3. 가계 자산 내에서 생존 필수품(Food)을 최대치로 구매하도록 하는 Boolean Mask 연산 수행.
- **Target File**: `simulation/engine.py`
- **Action**: 
    1. **Integrity Preservation**: `run_tick` 내의 가계 소비 루프(line ~545)는 **제거하지 마십시오**. `apply_leisure_effect`와 `update_needs`는 시뮬레이션의 생존 논리(Integrity)를 위해 필수적입니다.
    2. **Optimization**: `Household.decide_and_consume` 내부의 복잡한 연산을 `VectorizedHouseholdPlanner`의 계산 결과로 대체하십시오. 즉, 루프는 돌되 내부의 무거운 '결정 로직'만 벡터화된 값으로 치환하는 방식입니다.

### D. Missing Script & Testing
- **Target File**: `scripts/experiments/dynasty_report.py`
- **Action**: 해당 파일이 존재하지 않는다면, 최근 수행한 `Lively God Mode` 실험 코드를 바탕으로 **신규 생성**하십시오. (기존 `scripts/run_experiment.py` 등을 참고하여 1,000틱 완주 스크립트로 정형화)
- **Verification**: `scripts/iron_test.py`에 소요 시간 대비 처리 틱 수(`TPS = Total Ticks / Total Time`)를 출력하는 로직을 추가하여 성능 향상을 증명하십시오.
