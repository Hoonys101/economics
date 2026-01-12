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
- **Action**: `run_tick` 내의 가계 소비 루프(line ~545)를 위 `decide_consumption_batch` 결과에 따른 일괄 구매 반영 로직으로 교체하십시오.

## 3. ✅ Verification
- **Speed Test**: 최적화 전후의 **초당 틱(TPS) 속도**를 측정하여 리포트하십시오.
- **Integrity Test**: `iron_test.py`를 실행하여 가계의 굶주림(Survival need)이 정상적으로 해결되고 있는지 확인하십시오.
