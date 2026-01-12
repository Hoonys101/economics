# 🏎️ [Directive] Jules-Alpha: Optimizer

## 1. 🛑 Goal
시뮬레이션 연산 속도를 획기적으로 향상시켜 1,000틱 완주 시간을 단축하십시오.

## 2. 🧱 Technical Task
1.  **DB I/O Batching**: 
    - `simulation/engine.py`에서 `BATCH_SAVE_INTERVAL = 50`으로 설정하십시오.
    - 매 틱 발생하는 DB Flush 부하를 최소화합니다.
2.  **Log Level Tuning**:
    - 시뮬레이션 메인 로거의 레벨을 `WARNING`으로 설정하십시오.
    - `info` 로그 출력을 무력화하여 터미널 I/O를 절약합니다.
3.  **Vectorization**:
    - `VectorizedHouseholdPlanner`에 `decide_consumption_batch`를 추가하십시오.
    - 기존 `Household.decide_and_consume` 루프를 행렬 연산 기반으로 대체할 준비를 하십시오.

## 3. ✅ Verification
- 최적화 전후의 **초당 틱(TPS) 속도**를 측정하여 리포트하십시오.
- 모든 기능(거래, 소비)이 기존과 동일하게 동작함을 `iron_test.py`로 확인하십시오.
